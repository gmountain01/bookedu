"""Contact sheet of a PDF's pages (evidence helper). Usage: python scripts/pdf_sheet.py <pdf> <out.png> [cols] [zoom]"""
import math
import sys
import fitz

doc = fitz.open(sys.argv[1]); cols = int(sys.argv[3]) if len(sys.argv) > 3 else 5; z = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
pix = [p.get_pixmap(matrix=fitz.Matrix(z, z)) for p in doc]
w, h = max(p.width for p in pix), max(p.height for p in pix); rows = math.ceil(len(pix) / cols)
sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, cols * (w + 12), rows * (h + 12)), False); sheet.clear_with(170)
for i, px in enumerate(pix):
    px.set_origin((i % cols) * (w + 12), (i // cols) * (h + 12)); sheet.copy(px, px.irect)
sheet.save(sys.argv[2]); print(len(pix), 'pages ->', sys.argv[2])
