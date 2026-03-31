# -*- coding: utf-8 -*-
"""
工作日志系统 - FastAPI 主入口
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
from database import init_db, get_db
from models.user import User
from schemas import UserOut
from auth import get_current_user
from routers import auth, journal, summary, aggregate, tools, upload, history

app = FastAPI(
    title="工作日志系统",
    description="每日工作日志记录 + AI月度自动总结",
    version="1.0.0",
)

# CORS - 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 虚拟出 /api/uploads 外链路径供浏览器通过统一鉴权前缀直接拉图
os.makedirs("uploads", exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

# 注册路由
app.include_router(auth.router)
app.include_router(journal.router)
app.include_router(summary.router)
app.include_router(aggregate.router)
app.include_router(tools.router)
app.include_router(upload.router)
app.include_router(history.router)


@app.on_event("startup")
def startup():
    # 确保新模型也被导入后再建表
    from models import aggregate  # noqa
    init_db()


@app.get("/api/auth/me", response_model=UserOut, tags=["认证"])
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.put("/api/auth/theme", tags=["认证"])
def update_theme(theme: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.theme = theme
    db.commit()
    return {"status": "ok", "theme": theme}


@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok"}
