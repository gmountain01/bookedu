"""W-050: walk every slide of both admin decks (main track + appendix) at 1440×900 and 1280×720 full-screen-like box,
measure overflow / smallest text after fit, and save screenshots of the slides named in WANT plus any overflowing slide.
Usage: python tests/admin_decks.py [outdir]"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else LAB / 'docs' / 'evidence' / 'c32' / 'decks'
OUT.mkdir(parents=True, exist_ok=True)
WANT = ['한눈에 보기 ②', '3차 팀 회의 ①', '3차 팀 회의 ②', '3차에 추가한 자동 검사', '돌아보기 ②', '보완한 것과 다음 계획', '역할을 나눈 AI 팀',
        '3차 ② 출판 과정', '3차 ④ 협업', 'MT-22 · 완성본', 'MT-22 · 지적', 'BA-15', '가로 스크롤 띠', '3차 ① 디자인 개선 요청문', '범위 확장: 모든 책', '실제로 쓴 기법', '내가 쓴 프롬프트 ']
MEASURE = """() => { const s = document.querySelector('.slide-frame .slide'); const r = s.getBoundingClientRect(); const z = r.width / s.offsetWidth;
  const els = [...s.querySelectorAll('*')];
  const over = els.filter((e) => e.scrollHeight > e.clientHeight + 2 && getComputedStyle(e).overflow !== 'visible').length
    + els.filter((e) => { const b = e.getBoundingClientRect(); return b.width && (b.right > r.right + 1 || b.bottom > r.bottom + 1); }).length;
  const fonts = els.filter((e) => [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())).map((e) => parseFloat(getComputedStyle(e).fontSize) * z);
  const fit = parseFloat(getComputedStyle(s.querySelector('.sl-main') || s).getPropertyValue('--fit')) || 1;
  return { title: s.querySelector('.sl-title')?.textContent.trim(), kicker: s.querySelector('.sl-kicker')?.textContent.trim(), overflow: over, minFontPx: Math.round(Math.min(...fonts) * 10) / 10, fit }; }"""
errors, rows = [], []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    pg.on('console', lambda m: m.type == 'error' and errors.append(m.text)); pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.get_by_role('button', name='관리자 모드').click(); pg.wait_for_selector('.slide')
    for deck, route in (('process', '#/admin/process'), ('prompts', '#/admin/prompts')):
        pg.evaluate(f"location.hash = '{route}'"); pg.wait_for_timeout(500); pg.wait_for_selector('.slide-frame .slide')
        for track in ('main', 'appendix'):
            btn = pg.locator(f'.track-tabs button[data-t="{track}"]')
            if not btn.count(): continue
            btn.click(); pg.wait_for_timeout(200); pg.keyboard.press('Home'); pg.wait_for_timeout(120)
            seen = None; k = 0
            while True:
                pg.wait_for_timeout(60); m = pg.evaluate(MEASURE); counter = pg.locator('.deck-count').inner_text()
                if counter == seen: break
                seen = counter; k += 1
                m.update({'deck': deck, 'track': track, 'n': k, 'counter': counter}); rows.append(m)
                name = f"{deck}-{track}-{k:03d}"
                if m['overflow'] or any(w in (m['title'] or '') or w in (m['kicker'] or '') for w in WANT):
                    pg.locator('.slide-frame').screenshot(path=str(OUT / f"{name}{'-OVER' if m['overflow'] else ''}.png"))
                pg.keyboard.press('ArrowRight')
    b.close()
(OUT / 'decks.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
over = [r for r in rows if r['overflow']]; small = [r for r in rows if r['minFontPx'] < 12]
print(f"slides {len(rows)} | overflow {len(over)} | min font < 12px: {len(small)} | console errors {len(errors)}")
for r in over[:20]: print('  OVER', r['deck'], r['track'], r['n'], r['title'], r['overflow'])
for r in small[:10]: print('  SMALL', r['deck'], r['track'], r['n'], r['title'], r['minFontPx'])
for e in errors[:5]: print('  ERR', e[:160])
sys.exit(1 if over or errors else 0)
