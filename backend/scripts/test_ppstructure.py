"""
test_ppstructure.py — 诊断 PP-Structure 引擎是否正常工作
用法: ..\venv\Scripts\python.exe test_ppstructure.py <图片路径>
"""
import sys
import os

os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_enable_pir_in_executor'] = '0'
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import numpy as np
from PIL import Image

def test_engine(img_path: str):
    print("🔍 正在初始化 PPStructure 引擎...")
    from paddleocr import PPStructure
    engine = PPStructure(lang="ch", show_log=True)
    print("✅ 引擎初始化完成")

    img = Image.open(img_path).convert("RGB")
    img_array = np.array(img)
    print(f"📷 图片尺寸: {img_array.shape}")

    print("⏳ 正在分析版面...")
    result = engine(img_array)

    print(f"\n📊 识别到 {len(result)} 个区域:")
    for i, region in enumerate(result):
        rtype = region.get('type', '未知')
        bbox = region.get('bbox', [])
        res = region.get('res', None)
        print(f"  [{i+1}] 类型={rtype}, bbox={bbox}")
        if isinstance(res, list):
            texts = []
            for item in res:
                if isinstance(item, dict):
                    texts.append(item.get('text', ''))
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    t = item[1][0] if isinstance(item[1], (list, tuple)) else str(item[1])
                    texts.append(t)
            print(f"    文字: {'|'.join(texts[:3])}{'...' if len(texts)>3 else ''}")
        elif isinstance(res, dict):
            if 'html' in res:
                html_head = res['html'][:80]
                print(f"    HTML表格(前80字): {html_head}")
            else:
                print(f"    res keys: {list(res.keys())}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 用后端目录下的测试图片
        test_image = os.path.join(os.path.dirname(__file__), "..", "tmp_000045.png")
        if os.path.exists(test_image):
            test_engine(test_image)
        else:
            print("💡 用法: python test_ppstructure.py <图片路径>")
            print("   或把图片放在 backend/tmp_000045.png 自动测试")
    else:
        test_engine(sys.argv[1])
