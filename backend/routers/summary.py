# -*- coding: utf-8 -*-
import io
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.summary import MonthlySummary
from models.journal import JournalEntry
from models.user import User
from schemas import SummaryGenerate, SummaryUpdate, SummaryOut
from auth import get_current_user
from services.ai_service import generate_monthly_summary
from datetime import date
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

router = APIRouter(prefix="/api/summary", tags=["月度总结"])


def _get_or_404(db, user_id, year, month):
    obj = db.query(MonthlySummary).filter(
        MonthlySummary.user_id == user_id,
        MonthlySummary.year == year,
        MonthlySummary.month == month,
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="总结不存在，请先生成")
    return obj


@router.post("/generate", response_model=SummaryOut, summary="AI生成月度总结")
async def generate(
    data: SummaryGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start = date(data.year, data.month, 1)
    end_month = data.month + 1 if data.month < 12 else 1
    end_year = data.year if data.month < 12 else data.year + 1
    end = date(end_year, end_month, 1)

    entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.entry_date >= start,
        JournalEntry.entry_date < end,
    ).order_by(JournalEntry.entry_date).all()

    journal_list = [
        {"date": e.entry_date.isoformat(), "content": e.content, "tags": e.tags or []}
        for e in entries
    ]

    try:
        ai_text = await generate_monthly_summary(
            year=data.year,
            month=data.month,
            journal_entries=journal_list,
            dept_name=current_user.dept,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # 查找或创建记录
    obj = db.query(MonthlySummary).filter(
        MonthlySummary.user_id == current_user.id,
        MonthlySummary.year == data.year,
        MonthlySummary.month == data.month,
    ).first()

    if obj:
        obj.ai_content = ai_text
        obj.edited_content = ai_text
    else:
        obj = MonthlySummary(
            user_id=current_user.id,
            year=data.year,
            month=data.month,
            ai_content=ai_text,
            edited_content=ai_text,
        )
        db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{year}/{month}", response_model=SummaryOut, summary="获取月度总结")
def get_summary(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_or_404(db, current_user.id, year, month)


@router.put("/{year}/{month}", response_model=SummaryOut, summary="更新/编辑总结")
def update_summary(
    year: int,
    month: int,
    data: SummaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = _get_or_404(db, current_user.id, year, month)
    obj.edited_content = data.edited_content
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{year}/{month}/export", summary="导出Word文档")
def export_word(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    obj = _get_or_404(db, current_user.id, year, month)
    content = obj.edited_content or obj.ai_content or ""

    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(3.7)
    sec.bottom_margin = Cm(3.5)
    sec.left_margin = Cm(2.8)
    sec.right_margin = Cm(2.6)

    for line in content.split("\n"):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(28)
        stripped = line.strip()
        if stripped.startswith(("一、", "二、", "三、", "四、")):
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(stripped)
            run.font.name = "黑体"
            run.font.size = Pt(16)
            run.font.bold = True
        elif stripped and not stripped.startswith("【"):
            pf.first_line_indent = Pt(32)
            pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run = p.add_run(stripped)
            run.font.name = "仿宋_GB2312"
            run.font.size = Pt(16)
        else:
            run = p.add_run(stripped)
            run.font.name = "仿宋_GB2312"
            run.font.size = Pt(16)
        r = run._r
        rpr = r.get_or_add_rPr()
        rfonts = OxmlElement("w:rFonts")
        rfonts.set(qn("w:eastAsia"), run.font.name)
        rpr.insert(0, rfonts)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    filename = f"{year}年{month}月工作总结.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
