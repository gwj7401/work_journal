import io
import os
import urllib.parse
from docxtpl import DocxTemplate
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.summary import MonthlySummary
from models.history import SummaryHistory
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

    # 查找或创建记录
    obj = db.query(MonthlySummary).filter(
        MonthlySummary.user_id == current_user.id,
        MonthlySummary.year == data.year,
        MonthlySummary.month == data.month,
    ).first()

    if obj and obj.is_final:
        raise HTTPException(status_code=400, detail="该总结已标记为正式版，如需重新生成请先取消锁定。")

    try:
        ai_text = await generate_monthly_summary(
            year=data.year,
            month=data.month,
            journal_entries=journal_list,
            dept_name=current_user.dept,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

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
    if data.edited_content is not None:
        obj.edited_content = data.edited_content
    if data.is_final is not None:
        # 如果从非定稿变为定稿，存档一份
        if data.is_final and not obj.is_final:
            history = SummaryHistory(
                user_id=current_user.id,
                summary_type="monthly",
                summary_id=obj.id,
                year=obj.year,
                month=obj.month,
                content=obj.edited_content or obj.ai_content,
                version_note="定稿自动存档"
            )
            db.add(history)
        obj.is_final = data.is_final
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{year}/{month}/upload", response_model=SummaryOut, summary="上传Word覆盖总结")
async def upload_word(
    year: int,
    month: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith((".docx", ".doc")):
        raise HTTPException(status_code=400, detail="仅支持上传 .docx 等 Word 文件")
    
    obj = _get_or_404(db, current_user.id, year, month)
    
    try:
        content = await file.read()
        doc = Document(io.BytesIO(content))
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        if text:
            obj.edited_content = text
            obj.is_final = True  # 倒灌的必然是改好的正稿
            # 存档一份
            db.add(SummaryHistory(
                user_id=current_user.id,
                summary_type="monthly",
                summary_id=obj.id,
                year=obj.year,
                month=obj.month,
                content=text,
                version_note="Word上传覆盖存档"
            ))
            db.commit()
            db.refresh(obj)
        else:
            raise HTTPException(status_code=400, detail="未能从文档中提取到文字内容")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析Word文档失败: {str(e)}")
        
    return obj


@router.get("/{year}/{month}/export", summary="导出Word文档")
def export_word(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        obj = _get_or_404(db, current_user.id, year, month)
        content = obj.edited_content or obj.ai_content or ""
        
        # 进行最强力的无干涉行文剥离与 Markdown 洗净
        raw_lines = content.split('\n')
        lines = []
        for line in raw_lines:
            lb = line.strip()
            # 跳过空行
            if not lb:
                continue
            if lb.startswith("覆盖率提示："):
                continue
            
            # 暴力清理任何Markdown特有修饰符
            lb = lb.replace('**', '').replace('##', '').replace('#', '').strip()
            
            # 清理无序列表符号（-、*、•等）
            if lb.startswith("-") or lb.startswith("*") or lb.startswith("•"):
                lb = lb.lstrip("-*•").strip()
            
            # 极力防阻 AI 把“XX部门 年 月 工作总结” 或 “XX部门” 单独成段当作前言输出
            is_redundant_title = ("工作总结" in lb and (str(year) in lb or "三十" in lb))
            is_dept_only = (current_user.dept and lb == current_user.dept)
            if (is_redundant_title and len(lb) < 40) or is_dept_only:
                continue
                
            # 特判：替换AI习惯生成的结尾套话
            if "工作总结" in lb and "请领导审阅" in lb:
                lb = f"以上是我的{year}年{month}月份的工作总结及下平工作规划，请领导审阅并提出宝贵意见。"
                
            lines.append(lb)

        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "模板", "月度总结模板.docx")
        if os.path.exists(template_path):
            doc = DocxTemplate(template_path)
            context = {
                'paras': lines,
                'year': year,
                'month': month,
                'dept_name': current_user.dept if current_user.dept else "",
                'user_name': current_user.display_name if getattr(current_user, 'display_name', None) else ""
            }
            doc.render(context)
            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            filename = f"{year}年{month}月工作总结.docx"
            encoded_filename = urllib.parse.quote(filename)
            return StreamingResponse(
                buf,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"},
            )

        # 兜底：如果用户未提供带 {{ content }} 的外部模板，则调用系统内置的高保真《事业单位考核表》框架
        fallback_template = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sys_table_template.docx")
        doc = DocxTemplate(fallback_template)
        cleaned_content = "\n".join(lines)
        context = {
            'content': cleaned_content, 
            'year': year, 
            'render_period': f"{month}月",
            'user_name': current_user.name if current_user.name else "",
            'dept_name': current_user.dept if current_user.dept else ""
        }
        doc.render(context)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        filename = f"{year}年{month}月工作总结.docx"
        encoded_filename = urllib.parse.quote(filename)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"},
        )
    except Exception as e:
        import traceback
        return Response(content=traceback.format_exc(), status_code=200, media_type="text/plain")
