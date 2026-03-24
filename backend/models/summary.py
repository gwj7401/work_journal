# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, Text, SmallInteger, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    year = Column(SmallInteger, nullable=False, comment="年份")
    month = Column(SmallInteger, nullable=False, comment="月份")
    ai_content = Column(Text, nullable=True, comment="AI生成的总结原文")
    edited_content = Column(Text, nullable=True, comment="用户编辑后的版本")
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
