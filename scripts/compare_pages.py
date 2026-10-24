"""Before/after sheet of real printed pages (evidence helper, W-033).
Usage: python scripts/compare_pages.py <before.pdf> <pages,comma> <after.pdf> <pages,comma> <out.png>
Top row: the before pages; bottom row: the after pages (1-based page numbers)."""
import sys
import fitz

bpdf, bpages, apdf, apages, out = sys.argv[1:6]
rows = [[fitz.open(bpdf)[int(n) - 1] for n in bpages.split(',')], [fitz.open(apdf)[int(n) - 1] for n in apages.split(',')]]
z = 1.1
pix = [[pg.get_pixmap(matrix=fitz.Matrix(z, z)) for pg in row] for row in rows]
w = max(p.width for r in pix for p in r); h = max(p.height for r in pix for p in r); cols = max(len(r) for r in pix)
sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, cols * (w + 16) + 16, 2 * (h + 16) + 16), False); sheet.clear_with(150)
for y, row in enumerate(pix):
    for x, px in enumerate(row):
        px.set_origin(16 + x * (w + 16), 16 + y * (h + 16)); sheet.copy(px, px.irect)
sheet.save(out); print(out)
