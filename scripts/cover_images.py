"""W-034: cover images made from openly licensed photographs (sources and licenses: docs/evidence/c18/sources/sources.json).
A — photograph: Sungui-dong alley pavement (socialwalker, CC BY 2.0), upright, cropped to the A5 cover ratio,
    gently graded toward late-afternoon warmth; the bright empty pavement is kept as the title area.
B — illustration: Sungui-dong tree, roses and flowerpots (socialwalker, CC BY 2.0), cropped to the subject (no
    building signage), turned into a painterly print: edge-preserving smoothing, a limited palette (k-means),
    dark ink edges and paper grain. Run: python scripts/cover_images.py  (writes to docs/evidence/c18/drafts/)"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageOps

LAB = Path(__file__).resolve().parent.parent
SRC = LAB / 'docs' / 'evidence' / 'c18' / 'sources'
OUT = LAB / 'docs' / 'evidence' / 'c18' / 'drafts'
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)


def to_cv(im): return cv2.cvtColor(np.array(im.convert('RGB')), cv2.COLOR_RGB2BGR)
def to_pil(a): return Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))


def grain(a, amount):
    n = rng.normal(0, amount, a.shape[:2]).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), 0.8)
    return np.clip(a.astype(np.float32) + n[..., None], 0, 255).astype(np.uint8)


# ---- A: photograph ----
im = ImageOps.exif_transpose(Image.open(SRC / 'sungui-9654084092.jpg'))
w, h = im.size                      # 2000 x 3008 upright
ch = round(w / (148 / 210))         # A5 ratio
top = (h - ch) // 2
a = to_cv(im.crop((0, top, w, top + ch))).astype(np.float32) / 255
# late-afternoon grade: slightly warmer highlights, a touch of contrast in the mid tones, shadows kept soft
a = np.clip((a - .5) * 1.06 + .5, 0, 1)
a[..., 2] = np.clip(a[..., 2] * 1.04 + .01, 0, 1)   # red
a[..., 0] = np.clip(a[..., 0] * 0.95, 0, 1)         # blue
# MT-17 (T-049 #2, #3): warmer highlights; the blue water meter quieter; the hard shutter block at the top right toned down
hl = np.clip((a.mean(axis=2, keepdims=True) - .55) / .45, 0, 1)
a[..., 2:3] = np.clip(a[..., 2:3] + hl * .025, 0, 1); a[..., 0:1] = np.clip(a[..., 0:1] - hl * .03, 0, 1)
hsv = cv2.cvtColor((a * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
blue = ((hsv[..., 0] > 95) & (hsv[..., 0] < 130)).astype(np.float32)
hsv[..., 1] *= 1 - .45 * cv2.GaussianBlur(blue, (0, 0), 3)
a = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32) / 255
H, W = a.shape[:2]
m = np.zeros((H, W), np.float32); m[int(H * .015):int(H * .175), int(W * .62):int(W * .965)] = 1
m = cv2.GaussianBlur(m, (0, 0), W * .02)[..., None]
wall = np.array([.80, .82, .86], np.float32)  # the pale wall colour around the shutter (BGR)
a = a * (1 - .62 * m) + wall * (.62 * m)   # MT-18: further, it still pulled the eye at thumbnail size
a = (a * 255).astype(np.uint8)
a = grain(a, 2.2)
pa = to_pil(a).resize((1700, round(1700 * 210 / 148)), Image.LANCZOS)   # about 292 ppi on A5 (T-049 #4)
pa.save(OUT / 'A-photo.jpg', quality=80, optimize=True, progressive=True)

# ---- B: painterly print ----
im = ImageOps.exif_transpose(Image.open(SRC / 'sungui-9654101736.jpg'))   # 3008 x 2000
b = to_cv(im.crop((0, 0, 2080, 2000)))      # tree, roses, pots, sky gap and road; no buildings or signage
b = cv2.resize(b, (1352, 1300), interpolation=cv2.INTER_AREA)
b = np.clip(((b.astype(np.float32) / 255) ** 0.78) * 255, 0, 255).astype(np.uint8)   # open the shadows
smooth = b
for _ in range(4):
    smooth = cv2.bilateralFilter(smooth, 11, 46, 11)
smooth = cv2.stylization(smooth, sigma_s=80, sigma_r=0.42)
# limited palette, like a print with a few inks
Z = smooth.reshape(-1, 3).astype(np.float32)
_, labels, centers = cv2.kmeans(Z, 12, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, .5), 3, cv2.KMEANS_PP_CENTERS)
post = centers.astype(np.uint8)[labels.flatten()].reshape(smooth.shape)
post = cv2.medianBlur(post, 7)
# ink edges from the smoothed image
gray = cv2.cvtColor(smooth, cv2.COLOR_BGR2GRAY)
edges = cv2.adaptiveThreshold(cv2.medianBlur(gray, 9), 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 9)
ink = np.array([38, 34, 30], np.float32)   # warm dark ink (BGR)
pf = post.astype(np.float32)
# keep only real contours: drop ink specks smaller than ~40 px so the foliage reads as shapes, not noise
dark = (edges < 128).astype(np.uint8)
n, lab, stats, _ = cv2.connectedComponentsWithStats(dark, 8)
keep = np.zeros_like(dark)
keep[np.isin(lab, np.where(stats[:, cv2.CC_STAT_AREA] >= 40)[0][1:])] = 1
mask = keep.astype(bool)[..., None]
pf = np.where(mask, pf * .55 + ink * .45, pf)
# warm paper under the colours and fine grain, so the image reads as printed
paper = np.full_like(pf, (232, 241, 246))
pf = pf * .84 + paper * .16
pb = grain(np.clip(pf, 0, 255).astype(np.uint8), 5)
pbi = to_pil(pb).resize((1248, 1200), Image.LANCZOS)
pbi.save(OUT / 'B-illustration.jpg', quality=86, optimize=True, progressive=True)
for f in ('A-photo.jpg', 'B-illustration.jpg'):
    print(f, Image.open(OUT / f).size, round((OUT / f).stat().st_size / 1024), 'KB')

# ---- shipped cover-only images (src/covers/): A plus three CC0 photographs, A5 crops around the subject ----
DST = LAB / 'src' / 'covers'
DST.mkdir(exist_ok=True)
pa.resize((1500, round(1500 * 210 / 148)), Image.LANCZOS).save(DST / 'cover-walk.jpg', quality=80, optimize=True, progressive=True)


def a5(path, cx, cy=0.5, grade=None, width=1240):
    """Portrait A5 crop centred on (cx, cy) as fractions of the image; 1240 px wide (about 213 ppi on A5) to keep the single HTML small."""
    im = ImageOps.exif_transpose(Image.open(SRC / path)).convert('RGB')
    w, h = im.size
    r = 148 / 210
    cw, ch = (round(h * r), h) if w / h > r else (w, round(w / r))
    x0 = min(max(0, round(cx * w - cw / 2)), w - cw); y0 = min(max(0, round(cy * h - ch / 2)), h - ch)
    out = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((width, round(width / r)), Image.LANCZOS)
    if grade:
        out = to_pil(grain(cv2.cvtColor(np.clip(np.array(out, np.float32) * grade, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR), 1.6))
    return out


a5('unsplash-big-tree.jpg', .56, width=1100).save(DST / 'cover-tree.jpg', quality=72, optimize=True, progressive=True)   # foliage compresses poorly
a5('unsplash-green-window.jpg', .55).save(DST / 'cover-window.jpg', quality=80, optimize=True, progressive=True)
a5('unsplash-new-horizons.jpg', .5, .5).save(DST / 'cover-horizon.jpg', quality=80, optimize=True, progressive=True)
for f in sorted(DST.glob('*.jpg')):
    print('ship', f.name, Image.open(f).size, round(f.stat().st_size / 1024), 'KB')
