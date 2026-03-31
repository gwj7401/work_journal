# -*- coding: utf-8 -*-
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.history import SummaryHistory
from models.user import User
from schemas import SummaryHistoryOut
from auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["版本历史"])


@router.get("/{type}/{summary_id}", response_model=List[SummaryHistoryOut], summary="获取总结的历史记录")
def get_histories(
    type: str,
    summary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if type not in ("monthly", "quarterly", "annual"):
        raise HTTPException(status_code=400, detail="无效的总结类型")

    # 简单鉴权：只能看自己的
    histories = db.query(SummaryHistory).filter(
        SummaryHistory.user_id == current_user.id,
        SummaryHistory.summary_type == type,
        SummaryHistory.summary_id == summary_id
    ).order_by(SummaryHistory.created_at.desc()).all()
    
    return histories


@router.post("/save", response_model=SummaryHistoryOut, summary="手动保存版本快照")
def save_snapshot(
    summary_type: str,
    summary_id: int,
    year: int,
    content: str,
    note: str = "用户手动备份",
    month: int = None,
    quarter: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = SummaryHistory(
        user_id=current_user.id,
        summary_type=summary_type,
        summary_id=summary_id,
        year=year,
        month=month,
        quarter=quarter,
        content=content,
        version_note=note
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
