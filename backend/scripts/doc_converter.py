import os
import win32com.client
from pathlib import Path

source_dir = r"f:\work-journal\docs\模板"

def convert_doc_to_docx():
    word = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        for file in os.listdir(source_dir):
            if file.endswith(".doc") and not file.startswith("~$"):
                in_file = os.path.join(source_dir, file)
                out_file = os.path.join(source_dir, file + "x")  # .docx
                
                print(f"正在转换: {in_file}")
                
                # 兼容模式打开另存为 wdFormatXMLDocument (16)
                doc = word.Documents.Open(in_file)
                doc.SaveAs2(out_file, FileFormat=16)
                doc.Close()
                print(f"转换成功: {out_file}")
                
    except Exception as e:
        print(f"转换失败: {e}")
    finally:
        if word:
            word.Quit()

if __name__ == "__main__":
    convert_doc_to_docx()
