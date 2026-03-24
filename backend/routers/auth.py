# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from schemas import UserCreate, UserLogin, UserOut, Token
from auth import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserOut, summary="注册")
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        display_name=data.display_name or data.username,
        email=data.email,
        dept=data.dept,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token, summary="登录")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == data.username, User.is_active == True
    ).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserOut, summary="获取当前用户")
def get_me(current_user: User = Depends(lambda token=None, db=None: None)):
    # 此处由main.py中的依赖注入替代，仅作路由占位
    pass
