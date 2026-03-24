# -*- coding: utf-8 -*-
import io
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.aggregate import QuarterlySummary, AnnualSummary
from models.summary import MonthlySummary
from models.journal import JournalEntry
from models.user import User
from schemas import (
    QuarterlySummaryGenerate, QuarterlySummaryUpdate, QuarterlySummaryOut,
    AnnualSummaryGenerate, AnnualSummaryUpdate, AnnualSummaryOut,
)
from auth import get_current_user
from services.aggregate_service import (
    generate_quarterly_summary, generate_annual_summary, QUARTER_MONTHS, QUARTER_NAMES
)
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

router = APIRouter(prefix="/api/aggregate", tags=["聚合总结"])

# ─────────────────── 工具 ───────────────────

def _word_export(content: str, filename: str):
    """生成公文格式Word文件的StreamingResponse"""
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0); sec.page_height = Cm(29.7)
    sec.top_margin = Cm(3.7); sec.bottom_margin = Cm(3.5)
    sec.left_margin = Cm(2.8); sec.right_margin = Cm(2.6)
    for line in content.split("\n"):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(28)
        stripped = line.strip()
        if stripped.startswith(("一、", "二、", "三、", "四、")):
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(stripped); run.font.name = "黑体"; run.font.size = Pt(16); run.font.bold = True
        elif stripped:
            pf.first_line_indent = Pt(32); pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run = p.add_run(stripped); run.font.name = "仿宋_GB2312"; run.font.size = Pt(16)
        else:
            run = p.add_run(""); run.font.name = "仿宋_GB2312"; run.font.size = Pt(16)
        r = run._r; rpr = r.get_or_add_rPr()
        rf = OxmlElement("w:rFonts"); rf.set(qn("w:eastAsia"), run.font.name); rpr.insert(0, rf)
    buf = io.BytesIO(); doc.save(buf); buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _get_monthly_summaries_for_months(db, user_id, year, months):
    rows = db.query(MonthlySummary).filter(
        MonthlySummary.user_id == user_id,
        MonthlySummary.year == year,
        MonthlySummary.month.in_(months),
    ).all()
    return [
        {"month": r.month, "content": r.edited_content or r.ai_content or ""}
        for r in rows if (r.edited_content or r.ai_content)
    ]


def _get_journal_entries_for_months(db, user_id, year, months):
    start = date(year, min(months), 1)
    end_m = max(months)
    end = date(year + 1, 1, 1) if end_m == 12 else date(year, end_m + 1, 1)
    rows = db.query(JournalEntry).filter(
        JournalEntry.user_id == user_id,
        JournalEntry.entry_date >= start,
        JournalEntry.entry_date < end,
    ).all()
    return [
        {"date": r.entry_date.isoformat(), "content": r.content, "tags": r.tags or []}
        for r in rows if int(r.entry_date.strftime("%m")) in months
    ]


# ─────────────────── 季度总结 ───────────────────

@router.post("/quarterly/generate", response_model=QuarterlySummaryOut, summary="AI生成季度总结")
async def generate_quarterly(
    data: QuarterlySummaryGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.quarter not in (1, 2, 3, 4):
        raise HTTPException(400, "季度必须为1-4")
    months = QUARTER_MONTHS[data.quarter]
    monthly_sums = _get_monthly_summaries_for_months(db, current_user.id, data.year, months)
    journals = _get_journal_entries_for_months(db, current_user.id, data.year, months)

    try:
        ai_text = await generate_quarterly_summary(
            year=data.year, quarter=data.quarter,
            monthly_summaries=monthly_sums, journal_entries=journals,
            dept_name=current_user.dept,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))

    obj = db.query(QuarterlySummary).filter(
        QuarterlySummary.user_id == current_user.id,
        QuarterlySummary.year == data.year,
        QuarterlySummary.quarter == data.quarter,
    ).first()
    if obj:
        obj.ai_content = ai_text; obj.edited_content = ai_text
    else:
        obj = QuarterlySummary(user_id=current_user.id, year=data.year,
                               quarter=data.quarter, ai_content=ai_text, edited_content=ai_text)
        db.add(obj)
    db.commit(); db.refresh(obj)
    return obj


@router.get("/quarterly/{year}/{quarter}", response_model=QuarterlySummaryOut, summary="获取季度总结")
def get_quarterly(year: int, quarter: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    obj = db.query(QuarterlySummary).filter(
        QuarterlySummary.user_id == current_user.id,
        QuarterlySummary.year == year, QuarterlySummary.quarter == quarter,
    ).first()
    if not obj:
        raise HTTPException(404, "总结不存在，请先生成")
    return obj


@router.put("/quarterly/{year}/{quarter}", response_model=QuarterlySummaryOut, summary="编辑季度总结")
def update_quarterly(year: int, quarter: int, data: QuarterlySummaryUpdate,
                     db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    obj = db.query(QuarterlySummary).filter(
        QuarterlySummary.user_id == current_user.id,
        QuarterlySummary.year == year, QuarterlySummary.quarter == quarter,
    ).first()
    if not obj:
        raise HTTPException(404, "总结不存在")
    obj.edited_content = data.edited_content
    db.commit(); db.refresh(obj); return obj


@router.get("/quarterly/{year}/{quarter}/export", summary="导出季度总结Word")
def export_quarterly(year: int, quarter: int, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    obj = db.query(QuarterlySummary).filter(
        QuarterlySummary.user_id == current_user.id,
        QuarterlySummary.year == year, QuarterlySummary.quarter == quarter,
    ).first()
    if not obj:
        raise HTTPException(404, "总结不存在")
    content = obj.edited_content or obj.ai_content or ""
    return _word_export(content, f"{year}年{QUARTER_NAMES[quarter]}工作总结.docx")


# ─────────────────── 年度总结 ───────────────────

@router.post("/annual/generate", response_model=AnnualSummaryOut, summary="AI生成年度总结")
async def generate_annual(
    data: AnnualSummaryGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 优先取季度总结
    qrows = db.query(QuarterlySummary).filter(
        QuarterlySummary.user_id == current_user.id,
        QuarterlySummary.year == data.year,
    ).all()
    q_sums = [{"quarter": r.quarter, "content": r.edited_content or r.ai_content or ""} for r in qrows
              if (r.edited_content or r.ai_content)]

    # 次优：月度总结
    m_sums = _get_monthly_summaries_for_months(db, current_user.id, data.year, list(range(1, 13)))

    # 兜底：原始日志
    journals = _get_journal_entries_for_months(db, current_user.id, data.year, list(range(1, 13)))

    try:
        ai_text = await generate_annual_summary(
            year=data.year,
            quarterly_summaries=q_sums,
            monthly_summaries=m_sums,
            journal_entries=journals,
            dept_name=current_user.dept,
        )
    except RuntimeError as e:
        raise HTTPException(503, str(e))

    obj = db.query(AnnualSummary).filter(
        AnnualSummary.user_id == current_user.id,
        AnnualSummary.year == data.year,
    ).first()
    if obj:
        obj.ai_content = ai_text; obj.edited_content = ai_text
    else:
        obj = AnnualSummary(user_id=current_user.id, year=data.year,
                            ai_content=ai_text, edited_content=ai_text)
        db.add(obj)
    db.commit(); db.refresh(obj); return obj


@router.get("/annual/{year}", response_model=AnnualSummaryOut, summary="获取年度总结")
def get_annual(year: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    obj = db.query(AnnualSummary).filter(
        AnnualSummary.user_id == current_user.id, AnnualSummary.year == year,
    ).first()
    if not obj:
        raise HTTPException(404, "总结不存在，请先生成")
    return obj


@router.put("/annual/{year}", response_model=AnnualSummaryOut, summary="编辑年度总结")
def update_annual(year: int, data: AnnualSummaryUpdate,
                  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    obj = db.query(AnnualSummary).filter(
        AnnualSummary.user_id == current_user.id, AnnualSummary.year == year,
    ).first()
    if not obj:
        raise HTTPException(404, "总结不存在")
    obj.edited_content = data.edited_content
    db.commit(); db.refresh(obj); return obj


@router.get("/annual/{year}/export", summary="导出年度总结Word")
def export_annual(year: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    obj = db.query(AnnualSummary).filter(
        AnnualSummary.user_id == current_user.id, AnnualSummary.year == year,
    ).first()
    if not obj:
        raise HTTPException(404, "总结不存在")
    content = obj.edited_content or obj.ai_content or ""
    return _word_export(content, f"{year}年度工作总结.docx")
