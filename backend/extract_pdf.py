import fitz
doc = fitz.open(r"F:\Scan\_000045.pdf")
pix = doc[0].get_pixmap(matrix=fitz.Matrix(3,3)) # 三倍采样极高保真
pix.save(r"tmp_000045.png")
print("PAGE_EXTRACTED_OK")
