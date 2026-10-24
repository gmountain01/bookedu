"""Subset Pretendard Variable (OFL-1.1) to the characters this app needs, so the single HTML stays small.
Keeps: ASCII, Latin-1 punctuation, all 2,350 KS X 1001 Hangul syllables (common student input), Hangul jamo,
and every character that appears in src/ (UI text, data). Run: python scripts/subset_font.py"""
from pathlib import Path
from fontTools import subset

LAB = Path(__file__).resolve().parent.parent
SRC = LAB / 'node_modules' / 'pretendard' / 'dist' / 'web' / 'variable' / 'woff2' / 'PretendardVariable.woff2'
OUT = LAB / 'src' / 'fonts' / 'ChaekgongbangSans-Variable.woff2'

chars = set(chr(c) for c in range(0x20, 0x7F)) | set(chr(c) for c in range(0xA0, 0x100))
for hi in range(0xB0, 0xC9):  # KS X 1001 Hangul block: rows 0xB0-0xC8 -> 2,350 syllables
    for lo in range(0xA1, 0xFF):
        chars.add(bytes([hi, lo]).decode('euc_kr'))
chars |= set(chr(c) for c in range(0x3131, 0x318F))  # compatibility jamo
chars |= set('‘’“”…·•–—→←↑↓↷∨✓✗①②③④⑤×％％。、「」『』《》〈〉※○●□■△▲▽▼◆◇★☆')
for f in (LAB / 'src').rglob('*'):
    if f.suffix in ('.js', '.json', '.css') and 'fonts' not in f.parts:
        chars |= set(f.read_text(encoding='utf-8'))
chars = {c for c in chars if c.isprintable()}

opts = subset.Options()
opts.flavor = 'woff2'
opts.layout_features = ['*']
opts.name_IDs = ['*']
opts.notdef_outline = True
font = subset.load_font(str(SRC), opts)
sub = subset.Subsetter(opts)
sub.populate(text=''.join(chars))
sub.subset(font)
# OFL: a subset is a Modified Version, so it may not keep the Reserved Font Name "Pretendard".
NEW = 'Chaekgongbang Sans'
for rec in font['name'].names:
    if rec.nameID in (1, 3, 4, 16, 17, 21, 22):
        rec.string = NEW if rec.nameID in (1, 16, 21) else (f'{NEW} Variable' if rec.nameID == 4 else (f'{NEW};subset' if rec.nameID == 3 else rec.toUnicode().replace('Pretendard', NEW)))
    elif rec.nameID == 6:
        rec.string = 'ChaekgongbangSans-Variable'
subset.save_font(font, str(OUT), opts)
print(f'{len(chars)} chars -> {OUT.name} {OUT.stat().st_size / 1024:.0f} KB')
