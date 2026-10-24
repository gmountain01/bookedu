"""W-038 baseline: the finished-book dialog before the e-book reader (screenshots + scroll facts).
Usage: python tests/reader_before.py <outdir>"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
rep = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (390, 844)]:
        pg = b.new_page(viewport={'width': w, 'height': hh})
        pg.goto(URL + '#/studio'); pg.wait_for_selector('.stepper')
        pg.get_by_role('button', name='완성본 보기').first.click(); pg.wait_for_selector('dialog[open]'); pg.wait_for_timeout(800)
        pg.screenshot(path=str(OUT / f'{w}-open.png'))
        # a free scroll (trackpad / swipe) can stop between pages
        pg.evaluate("document.querySelector('dialog .pv-scroll').scrollLeft += 137"); pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / f'{w}-free-scroll.png'))
        rep[w] = pg.evaluate("""() => { const s = document.querySelector('dialog .pv-scroll');
          return { overflowX: getComputedStyle(s).overflowX, scrollLeft: s.scrollLeft, where: document.querySelector('dialog .pv-where').textContent }; }""")
        pg.close()
    b.close()
(OUT / 'facts.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(rep, ensure_ascii=False))
