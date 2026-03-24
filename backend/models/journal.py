# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Text, Date, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entry_date = Column(Date, nullable=False, index=True, comment="日志日期")
    content = Column(Text, nullable=False, comment="Markdown正文")
    tags = Column(JSON, default=list, comment="标签列表")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
