# -*- coding: utf-8 -*-
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ── 用户 ──────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    dept: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: Optional[str]
    email: Optional[str]
    dept: Optional[str]
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── 日志 ──────────────────────────────
class JournalCreate(BaseModel):
    entry_date: date
    content: str
    tags: List[str] = []


class JournalUpdate(BaseModel):
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class JournalOut(BaseModel):
    id: int
    user_id: int
    entry_date: date
    content: str
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── 月度总结 ──────────────────────────
class SummaryGenerate(BaseModel):
    year: int
    month: int


class SummaryUpdate(BaseModel):
    edited_content: str


class SummaryOut(BaseModel):
    id: int
    user_id: int
    year: int
    month: int
    ai_content: Optional[str]
    edited_content: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True


# ── 统计 ──────────────────────────────
class HeatmapItem(BaseModel):
    date: str
    count: int


class StatsOut(BaseModel):
    heatmap: List[HeatmapItem]
    streak: int
    total_this_month: int
    top_tags: List[dict]


# ── 季度总结 ────────────────────
class QuarterlySummaryGenerate(BaseModel):
    year: int
    quarter: int  # 1-4


class QuarterlySummaryUpdate(BaseModel):
    edited_content: str


class QuarterlySummaryOut(BaseModel):
    id: int
    user_id: int
    year: int
    quarter: int
    ai_content: Optional[str]
    edited_content: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True


# ── 年度总结 ────────────────────
class AnnualSummaryGenerate(BaseModel):
    year: int


class AnnualSummaryUpdate(BaseModel):
    edited_content: str


class AnnualSummaryOut(BaseModel):
    id: int
    user_id: int
    year: int
    ai_content: Optional[str]
    edited_content: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True
