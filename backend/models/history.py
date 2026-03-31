# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Text, SmallInteger, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class SummaryHistory(Base):
    __tablename__ = "summary_histories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    summary_type = Column(String(20), nullable=False, comment="总结类型: monthly, quarterly, annual")
    summary_id = Column(Integer, nullable=False, comment="关联总结表的ID")
    year = Column(SmallInteger, nullable=False, comment="年份")
    month = Column(SmallInteger, nullable=True, comment="月份(仅限月度总结)")
    quarter = Column(SmallInteger, nullable=True, comment="季度(仅限季度总结)")
    content = Column(Text, nullable=True, comment="版本内容文本")
    version_note = Column(String(100), nullable=True, comment="版本自定义注释")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
