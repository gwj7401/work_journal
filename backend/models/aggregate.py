# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, Text, SmallInteger, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base


class QuarterlySummary(Base):
    __tablename__ = "quarterly_summaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    year = Column(SmallInteger, nullable=False, comment="年份")
    quarter = Column(SmallInteger, nullable=False, comment="季度(1-4)")
    ai_content = Column(Text, nullable=True, comment="AI生成内容")
    edited_content = Column(Text, nullable=True, comment="编辑后版本")
    is_final = Column(Boolean, default=False, comment="是否正式定稿不再被AI生成覆盖")
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AnnualSummary(Base):
    __tablename__ = "annual_summaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    year = Column(SmallInteger, nullable=False, comment="年份")
    ai_content = Column(Text, nullable=True, comment="AI生成内容")
    edited_content = Column(Text, nullable=True, comment="编辑后版本")
    is_final = Column(Boolean, default=False, comment="是否正式定稿不再被AI生成覆盖")
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
