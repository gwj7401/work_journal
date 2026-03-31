# -*- coding: utf-8 -*-
import os
import tempfile
import uuid
import logging
from fastapi import APIRouter, File, UploadFile, BackgroundTasks, HTTPException, Form
from fastapi.responses import FileResponse
from pdf2docx import Converter

router = APIRouter(prefix="/api/tools", tags=["实用工具"])

def remove_temp_file(path: str):
    """确保在服务端生成并返回后静默销毁零时转换文件，不占用磁盘空间"""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        logging.error(f"清理临时文件失败: {e}")

@router.post("/pdf-to-word", summary="PDF 转换为 Word 文档")
async def convert_pdf_to_word(background_tasks: BackgroundTasks, file: UploadFile = File(...), force_ocr: bool = Form(False)):
    """
    免费、本地离线处理 PDF 到 Docx，数据安全不上传到公网。
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持转换 PDF 格式的文件")
    
    temp_dir = tempfile.gettempdir()
    unique_id = str(uuid.uuid4())
    pdf_path = os.path.join(temp_dir, f"{unique_id}.pdf")
    docx_path = os.path.join(temp_dir, f"{unique_id}.docx")
    
    try:
        # 1. 暂存上传的 PDF 数据包到本地
        with open(pdf_path, "wb") as f:
            f.write(await file.read())
            
        # 2. 智能排查：基于首层字元抽提探明文件血统是否为“包装过的伪扫描件”
        import fitz
        run_ocr = False
        with fitz.open(pdf_path) as f_doc:
            scanned_pages = 0
            for page in f_doc:
                text_len = len(page.get_text("text").strip())
                img_count = len(page.get_images(full=True))
                if text_len < 20 and img_count > 0:
                    scanned_pages += 1
            if scanned_pages >= 1:
                run_ocr = True
        if force_ocr:
            run_ocr = True
        if run_ocr:
            # 对付彻底的死图式文件，自动交火启用刚才打造重装国产神器进行破译
            try:
                import sys
                # 注入搜索目录，确保能够跨包导入本工程 script/ 内的文件
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from scripts.pdf2word_ocr import pdf_to_word_ocr
                
                pdf_to_word_ocr(pdf_path, docx_path)
            except Exception as e:
                # 环境阻力或依赖缺件，优雅降级为原汁原味的图底嵌入
                logging.warning(f"智能脱壳引擎启用失败({e})，回退旧版包裹术。")
                cv = Converter(pdf_path)
                cv.convert(docx_path, start=0, end=None)
                cv.close()
        else:
            # 正常包含排版协议与锚点的文本级格式件，仍然跑高性能标准转换
            cv = Converter(pdf_path)
            cv.convert(docx_path, start=0, end=None)
            cv.close()
            
    except Exception as e:
        remove_temp_file(pdf_path)
        remove_temp_file(docx_path)
        raise HTTPException(status_code=500, detail=f"文件转换失败，可能是 PDF 存在加密或页面受损: {str(e)}")

    # 3. 让 FastAPI 在文件流投递结束后执行这俩清理任务，保障磁盘无痕
    background_tasks.add_task(remove_temp_file, pdf_path)
    background_tasks.add_task(remove_temp_file, docx_path)

    # 4. 组装 Word 返回体，利用 FileResponse 确保 Content-Disposition 正常触发浏览器下载
    original_name = os.path.splitext(file.filename)[0]
    return FileResponse(
        path=docx_path, 
        filename=f"{original_name}.docx", 
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
