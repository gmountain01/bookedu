"""W-035: body photographs (the sample book's figures and the 「이미지 삽입」 library), separate from the cover crops.
Sources and licenses: docs/evidence/c18/sources/sources.json (public domain, CC BY 2.0, CC0; verified on Wikimedia
Commons). Each photo is cropped to its subject (no signage, no cut heads), lightly graded toward one shared warm,
low-contrast look so the book's pictures read as one set, and saved at a size that holds when placed large in the
body (about 1100-1200 px on the long side; ~250 ppi at A5 text width). Run: python scripts/body_photos.py"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageEnhance

LAB = Path(__file__).resolve().parent.parent
SRC = LAB / 'docs' / 'evidence' / 'c18' / 'sources'
DST = LAB / 'src' / 'photos'
DST.mkdir(exist_ok=True)


def look(im):
    """One shared grade: slightly lifted shadows, a touch warmer, saturation a little down."""
    a = np.asarray(im.convert('RGB')).astype(np.float32) / 255
    a = 0.04 + a * 0.95                                   # lift blacks a little (printed-paper feel)
    a[..., 0] = np.clip(a[..., 0] * 1.02, 0, 1)            # warmer
    a[..., 2] = np.clip(a[..., 2] * 0.97, 0, 1)
    out = Image.fromarray((a * 255).astype(np.uint8))
    return ImageEnhance.Color(out).enhance(0.9)


def crop(name, box_frac, long_side, out, quality=78):
    im = ImageOps.exif_transpose(Image.open(SRC / name))
    w, h = im.size
    x0, y0, x1, y1 = box_frac
    im = im.crop((round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h)))
    s = long_side / max(im.size)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    look(im).save(DST / out, quality=quality, optimize=True, progressive=True)
    print(out, im.size, round((DST / out).stat().st_size / 1024), 'KB')


# the sample book's two figures
crop('daegu-namgu-alley.jpg', (0, 0.04, 1, 0.96), 1200, 'photo-alley.jpg')                 # portrait: the lit wall and the narrow path
crop('sungui-9654101736.jpg', (0, 0.05, 0.69, 1), 1200, 'photo-pots.jpg', quality=70)                   # tree, roses, pots; buildings with signage cut off
# the rest of the library (different subjects, not colour variants)
crop('unsplash-big-tree.jpg', (0.08, 0, 1, 1), 1200, 'photo-tree.jpg', quality=70)          # landscape: the tree on the hill
crop('unsplash-green-window.jpg', (0.12, 0.05, 0.95, 0.95), 1200, 'photo-window.jpg')       # landscape: window, lamp and bowl
crop('unsplash-new-horizons.jpg', (0, 0.28, 1, 0.80), 1200, 'photo-sea.jpg', quality=92)   # MT-19: banding at 78                 # landscape-ish: horizon and sky band
