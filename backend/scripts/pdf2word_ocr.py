"""
pdf2word_ocr.py — 基于 PaddleOCR PP-StructureV2 的 PDF→Word 转换工具

核心能力：
1. 版面分析（Layout Analysis）：自动识别标题、正文、表格、图片区域
2. 表格识别（Table Recognition）：将表格还原为 Word 表格格式
3. 中英文混合识别：高精度 OCR，准确率远优于 EasyOCR
4. 多列版面：按区域顺序组织文字，不错行不混排

用法:
  python pdf2word_ocr.py <输入PDF> <输出Word>
示例:
  .\\venv\\Scripts\\python.exe pdf2word_ocr.py C:\\文件.pdf C:\\结果.docx
"""

import sys
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # 全局使用 HuggingFace 国内加速节点
os.environ['FLAGS_use_onednn'] = '0'  # 禁用 oneDNN 修复 ConvertPirAttribute2RuntimeAttribute 报错
os.environ['FLAGS_enable_pir_in_executor'] = '0'  # 禁用 PIR 执行器，回退到旧版执行逻辑
# os.environ['PADDLEX_MODEL_HOSTER'] = 'modelscope'  # modelscope 部分模型报 307 重定向或卡住
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
import re
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ──────────────────── 懒加载 PaddleOCR ────────────────────

_structure_engine = None

def _get_engine():
    global _structure_engine
    if _structure_engine is None:
        print("🚀 正在初始化 PaddleOCR PP-Structure 引擎（首次运行会自动下载模型，请稍候）...")
        from paddleocr import PPStructure
        _structure_engine = PPStructure(
            lang="ch",           # 中英文混合
            show_log=False
        )
    return _structure_engine


# ──────────────────── Word 工具函数 ────────────────────

def _set_cell_border(cell, **kwargs):
    """为单元格设置边框（top/bottom/left/right）"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        tag = f'w:{edge}'
        element = OxmlElement(tag)
        element.set(qn('w:val'), kwargs.get(edge, 'single'))
        element.set(qn('w:sz'), '4')
        element.set(qn('w:space'), '0')
        element.set(qn('w:color'), '000000')
        tcBorders.append(element)
    tcPr.append(tcBorders)


def _add_table_from_html(word_doc, html_str):
    """
    将 PaddleOCR 识别出的 HTML 表格字符串解析并写入 Word 表格。
    支持多行多列，保持原始对齐。
    """
    try:
        from html.parser import HTMLParser

        class TableParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.rows = []
                self.cur_row = None
                self.cur_cell = ""
                self.in_cell = False

            def handle_starttag(self, tag, attrs):
                if tag == 'tr':
                    self.cur_row = []
                elif tag in ('td', 'th'):
                    self.in_cell = True
                    self.cur_cell = ""

            def handle_endtag(self, tag):
                if tag == 'tr' and self.cur_row is not None:
                    self.rows.append(self.cur_row)
                    self.cur_row = None
                elif tag in ('td', 'th') and self.in_cell:
                    if self.cur_row is not None:
                        self.cur_row.append(self.cur_cell.strip())
                    self.in_cell = False

            def handle_data(self, data):
                if self.in_cell:
                    self.cur_cell += data

        parser = TableParser()
        parser.feed(html_str)
        rows = parser.rows

        if not rows:
            return False

        # 统一列数
        col_count = max(len(r) for r in rows)
        for r in rows:
            while len(r) < col_count:
                r.append("")

        tbl = word_doc.add_table(rows=len(rows), cols=col_count)
        tbl.style = 'Table Grid'

        for ri, row_data in enumerate(rows):
            for ci, cell_text in enumerate(row_data):
                cell = tbl.cell(ri, ci)
                cell.text = cell_text
                # 首行加粗（表头）
                if ri == 0:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.bold = True
                            run.font.size = Pt(10)
                else:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.font.size = Pt(10)
        return True

    except Exception as e:
        print(f"  ⚠️ 表格解析失败: {e}，将回退为纯文本")
        return False


def _add_normal_paragraph(word_doc, text, is_title=False):
    """添加普通段落，自动识别首行缩进"""
    text = text.strip()
    if not text:
        return

    p = word_doc.add_paragraph()

    if is_title:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(18)
        run.font.name = '方正小标宋简体'
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf = p.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = Pt(28)
        # 是否首行缩进(段落以中文开头，且不是纯数字/纯英文行)
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        prefix = "　　" if has_chinese else ""
        run = p.add_run(prefix + text)
        run.font.name = '仿宋'
        run.font.size = Pt(16)


# ──────────────────── 主流程 ────────────────────

def pdf_to_word_ocr(pdf_path: str, output_docx_path: str):
    engine = _get_engine()

    print(f"📖 正在读取原文件: {pdf_path}")
    pdf_doc = fitz.open(pdf_path)
    word_doc = Document()

    # 页面设置（A4 标准公文）
    for section in word_doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.8)
        section.right_margin = Cm(2.6)

    # 默认字体
    normal_style = word_doc.styles['Normal']
    normal_style.font.name = '仿宋'
    normal_style.font.size = Pt(16)

    for page_num in range(len(pdf_doc)):
        print(f"⏳ 正在解析第 {page_num + 1}/{len(pdf_doc)} 页（版面分析 + OCR）...")
        page = pdf_doc[page_num]

        # 高分辨率渲染（300 DPI 等效）
        zoom = 2.5
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_array = np.array(img)

        # PP-Structure 分析：直接返回 list 
        parsing_res = engine(img_array)

        if not parsing_res:
            print(f"  ⚠️ 第 {page_num + 1} 页未识别到任何有效区块")
            continue

        # 按区域垂直位置排序（V2 的 bbox 为 [x_left, y_top, x_right, y_bottom]，取 y_top 坐标）
        parsing_res.sort(key=lambda r: r.get('bbox', [0, 0])[1])

        for region in parsing_res:
            region_label = region.get('type', '').lower()
            res_data = region.get('res', None)

            # ── 表格区域 ──
            if region_label == 'table':
                html = ""
                if isinstance(res_data, dict):
                    html = res_data.get('html', '')
                
                if html:
                    print(f"  📊 识别到表格，正在写入 Word 表格...")
                    ok = _add_table_from_html(word_doc, html)
                    if not ok:
                        # 回退：解析 HTML 标签提取纯文本
                        clean_text = re.sub(r'<[^>]+>', ' ', html).strip()
                        if clean_text:
                            _add_normal_paragraph(word_doc, clean_text)
                else:
                    # 若无 HTML，尝试直接取 res 中的表格文字内容
                    if isinstance(res_data, list):
                        for line in res_data:
                            if isinstance(line, dict) and 'text' in line:
                                _add_normal_paragraph(word_doc, line['text'])
                            elif isinstance(line, (list, tuple)) and len(line) >= 2:
                                t = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                                _add_normal_paragraph(word_doc, t.strip())

            # ── 标题区域 ──
            elif region_label == 'title':
                text = ""
                if isinstance(res_data, list):
                    for line in res_data:
                        if isinstance(line, dict):
                            text += line.get('text', '')
                        elif isinstance(line, (list, tuple)) and len(line) >= 2:
                            t = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                            text += t.strip()
                elif isinstance(res_data, dict):
                    text = res_data.get('text', '')
                if text:
                    _add_normal_paragraph(word_doc, text, is_title=True)

            # ── 图片/印章区域 ──
            elif region_label in ('figure', 'figure_caption', 'formula'):
                p = word_doc.add_paragraph()
                label_zh = "图片" if "figure" in region_label else "公式"
                runStream = p.add_run(f"[{label_zh}区域]")
                runStream.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
                runStream.font.size = Pt(10)

            # ── 普通文本区域（text / header / footer 等）──
            else:
                lines = []
                if isinstance(res_data, list):
                    for line_item in res_data:
                        if isinstance(line_item, dict):
                            txt = line_item.get('text', '')
                            if txt: lines.append(txt.strip())
                        # 兼容旧版或其它格式
                        elif isinstance(line_item, (list, tuple)) and len(line_item) >= 2:
                            t = line_item[1][0] if isinstance(line_item[1], (list, tuple)) else str(line_item[1])
                            lines.append(t.strip())

                for line_text in lines:
                    if line_text:
                        _add_normal_paragraph(word_doc, line_text)

        # 非最后一页加分页符
        if page_num < len(pdf_doc) - 1:
            word_doc.add_page_break()

    pdf_doc.close()
    print("💾 正在保存 Word 文档...")
    word_doc.save(output_docx_path)
    print(f"🎉 完成！输出文件: {output_docx_path}")


# ──────────────────── 入口 ────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("💡 用法: python.exe pdf2word_ocr.py <输入PDF路径> <输出Word路径>")
        print(r"⭐ 示例: .\venv\Scripts\python.exe pdf2word_ocr.py C:\123.pdf C:\结果.docx")
        sys.exit(1)

    pdf_to_word_ocr(sys.argv[1], sys.argv[2])
