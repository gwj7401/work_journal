# -*- coding: utf-8 -*-
"""
工作日志系统 - FastAPI 主入口
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_db
from models.user import User
from schemas import UserOut
from auth import get_current_user
from routers import auth, journal, summary
from routers import aggregate

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

# 注册路由
app.include_router(auth.router)
app.include_router(journal.router)
app.include_router(summary.router)
app.include_router(aggregate.router)


@app.on_event("startup")
def startup():
    # 确保新模型也被导入后再建表
    from models import aggregate  # noqa
    init_db()


@app.get("/api/auth/me", response_model=UserOut, tags=["认证"])
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok"}
