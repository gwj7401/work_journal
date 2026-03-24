# -*- coding: utf-8 -*-
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from database import get_db
from models.journal import JournalEntry
from models.user import User
from schemas import JournalCreate, JournalUpdate, JournalOut, HeatmapItem, StatsOut
from auth import get_current_user

router = APIRouter(prefix="/api/journals", tags=["日志"])


@router.post("", response_model=JournalOut, summary="新增或更新今日日志")
def upsert_journal(
    data: JournalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.entry_date == data.entry_date,
    ).first()
    if entry:
        entry.content = data.content
        entry.tags = data.tags
    else:
        entry = JournalEntry(
            user_id=current_user.id,
            entry_date=data.entry_date,
            content=data.content,
            tags=data.tags,
        )
        db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/today", response_model=Optional[JournalOut], summary="获取今日日志")
def get_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    return db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.entry_date == today,
    ).first()


@router.get("/date/{entry_date}", response_model=Optional[JournalOut], summary="按日期获取日志")
def get_by_date(
    entry_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.entry_date == entry_date,
    ).first()


@router.get("/month/{year}/{month}", response_model=List[JournalOut], summary="获取某月所有日志")
def get_by_month(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.entry_date >= start,
        JournalEntry.entry_date < end,
    ).order_by(JournalEntry.entry_date).all()


@router.delete("/{entry_id}", summary="删除日志")
def delete_journal(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id,
        JournalEntry.user_id == current_user.id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="日志不存在")
    db.delete(entry)
    db.commit()
    return {"ok": True}


@router.get("/stats/heatmap", response_model=StatsOut, summary="统计/热力图数据")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    year_ago = today - timedelta(days=365)

    entries = db.query(JournalEntry).filter(
        JournalEntry.user_id == current_user.id,
        JournalEntry.entry_date >= year_ago,
    ).all()

    date_set = set()
    heatmap = []
    tag_counter: dict = {}
    this_month_count = 0

    for e in entries:
        d = e.entry_date.isoformat()
        heatmap.append(HeatmapItem(date=d, count=1))
        date_set.add(e.entry_date)
        if e.entry_date.year == today.year and e.entry_date.month == today.month:
            this_month_count += 1
        for tag in (e.tags or []):
            tag_counter[tag] = tag_counter.get(tag, 0) + 1

    # 连续打卡天数
    streak = 0
    check = today
    while check in date_set:
        streak += 1
        check -= timedelta(days=1)

    top_tags = sorted(
        [{"tag": k, "count": v} for k, v in tag_counter.items()],
        key=lambda x: -x["count"],
    )[:10]

    return StatsOut(
        heatmap=heatmap,
        streak=streak,
        total_this_month=this_month_count,
        top_tags=top_tags,
    )
