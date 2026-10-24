"""W-033: the book's serif (명조) face, embedded so every device shows the same type (no silent fallback).
Source: Noto Serif KR variable (SIL OFL 1.1; Adobe / Sandoll hangul), the copy installed in C:/Windows/Fonts.
Keeps the same characters as scripts/subset_font.py (ASCII, Latin-1, KS X 1001 2,350 Hangul syllables, jamo,
punctuation, every character in src/), as two static instances (400, 700): Chromium embeds a variable font in a
PDF as Type3 glyphs (MT-15, T-045 #7; checked in a scratch test), static instances as real TrueType fonts. A subset is a Modified Version under the
OFL and "Noto" is a trademark, so the family is renamed "Chaekgongbang Serif".
Run: python scripts/subset_serif.py"""
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

LAB = Path(__file__).resolve().parent.parent
SRC = Path('C:/Windows/Fonts/NotoSerifKR-VF.ttf')
OUTS = {400: LAB / 'src' / 'fonts' / 'ChaekgongbangSerif-Regular.woff2', 700: LAB / 'src' / 'fonts' / 'ChaekgongbangSerif-Bold.woff2'}

chars = set(chr(c) for c in range(0x20, 0x7F)) | set(chr(c) for c in range(0xA0, 0x100))
for hi in range(0xB0, 0xC9):  # KS X 1001 Hangul rows 0xB0-0xC8 -> 2,350 syllables
    for lo in range(0xA1, 0xFF):
        chars.add(bytes([hi, lo]).decode('euc_kr'))
chars |= set(chr(c) for c in range(0x3131, 0x318F))
chars |= set('‘’“”…·•–—「」『』《》〈〉※○●□■△▲◆◇★☆①②③④⑤')
for f in (LAB / 'src').rglob('*'):
    if f.suffix in ('.js', '.json', '.css') and 'fonts' not in f.parts:
        chars |= set(f.read_text(encoding='utf-8'))
chars = {c for c in chars if c.isprintable()}

opts = subset.Options()
opts.flavor = 'woff2'
opts.layout_features = ['kern', 'liga', 'locl', 'palt', 'halt', 'vert', 'vrt2']
opts.name_IDs = ['*']
opts.notdef_outline = True
for wght, out in OUTS.items():
    font = TTFont(str(SRC))
    sub = subset.Subsetter(opts)
    sub.populate(text=''.join(chars))
    sub.subset(font)
    font = instancer.instantiateVariableFont(font, {'wght': wght})
    NEW = 'Chaekgongbang Serif'
    style = 'Regular' if wght == 400 else 'Bold'
    for rec in font['name'].names:
        if rec.nameID in (1, 16, 21):
            rec.string = NEW
        elif rec.nameID in (2, 17, 22):
            rec.string = style
        elif rec.nameID == 3:
            rec.string = f'{NEW} {style};subset'
        elif rec.nameID == 4:
            rec.string = f'{NEW} {style}'
        elif rec.nameID in (6, 25):
            rec.string = f'ChaekgongbangSerif-{style}'
    font.flavor = 'woff2'
    font.save(str(out))
    check = TTFont(str(out))
    assert check['name'].getName(1, 3, 1, 0x409).toUnicode() == NEW and 'fvar' not in check
    print(f'{len(chars)} chars -> {out.name} {out.stat().st_size / 1024:.0f} KB (static {wght})')
