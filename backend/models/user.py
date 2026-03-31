# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    password_hash = Column(String(128), nullable=False, comment="密码哈希")
    display_name = Column(String(50), nullable=True, comment="显示名称")
    email = Column(String(100), nullable=True, comment="邮箱")
    dept = Column(String(50), nullable=True, comment="所属部门")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_admin = Column(Boolean, default=False, comment="是否管理员")
    theme = Column(String(30), default="indigo", comment="用户界面主题偏好")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
