# -*- coding: utf-8 -*-
import os
import uuid
import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

# 定义上传落盘基目录
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/image", summary="富文本图片上传接口")
async def upload_image(file: UploadFile = File(...)):
    """
    处理富文本中剪贴板/拖拽或手动选择图片的上传请求。
    保存至后端的 uploads/ 文件夹，并回传前台可直接展示的相对路由链接。
    """
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的图片格式（仅限 jpg/png/gif/webp/svg）")
    
    # 获取原始扩展名，如果未能提取则回退到 png
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ".png"
        
    # 以年月分类存储，避免单文件夹下文件爆满导致索引慢
    date_prefix = datetime.datetime.now().strftime("%Y-%m")
    save_dir = os.path.join(UPLOAD_DIR, date_prefix)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(save_dir, unique_name)
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片保存过程中发生服务器故障：{str(e)}")
        
    # 返回相对路径供前端拼接和拼接后访问
    # 例: /api/uploads/2026-03/1234.png
    url_path = f"/api/uploads/{date_prefix}/{unique_name}"
    
    return {
        "url": url_path,
        "alt": file.filename
    }
