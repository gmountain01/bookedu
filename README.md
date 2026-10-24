# 책공방 (bookedu)

중·고등학생이 **출판의 전체 과정**을 배우고, **8단계를 따라 나만의 디지털 책**을 만들어 보는 교육용 웹앱입니다.

- 공개 사이트: https://gmountain01.github.io/bookedu/
- 서버가 없습니다. 만든 책은 사용 중인 브라우저의 저장소(IndexedDB)에만 저장되고 어디로도 전송되지 않습니다.

## 무엇을 할 수 있나

**책은 어떻게 만들어질까** — 기획과 집필 → 편집과 디자인 → 인쇄와 제작 → 유통과 홍보의 4단계를 정거장처럼 따라갑니다.
- 단계마다 세부 절차, 같은 예시 책이 바뀌어 가는 과정, 함께 일하는 사람들의 연속 장면, 상황 판단 문제와 퀴즈
- 전체 과정 지도와 역할 관계도(저자·기획편집자·편집자·북디자이너·제작 담당자·인쇄·제본 기술자·출판 마케터·서점 담당자)

**나만의 책 만들기** — 기획 → 원고 → 조판 → 이미지 준비 → 본문 배치 → 앞부속 → 목차 → 표지와 완성의 8단계.
- 쓰는 동안 실제 인쇄 쪽과 같은 미리보기가 옆에서 따라옵니다(쪽 넘김, 한 쪽/펼침면, 확대).
- 디자인 3종, 표지 배치 4종, 표지 글(제목·부제·카피·지은이)과 편집된 뒤표지, 기본 사진 라이브러리
- 완성본은 전자책처럼 넘겨 읽고(차례·키보드·스와이프), 인쇄 / PDF로 저장할 수 있습니다.
- 「책 파일 → JSON 백업」으로 내보내고 「JSON 불러오기」로 다른 브라우저·컴퓨터에서 이어서 작업할 수 있습니다.

## 바로 쓰기

1. 공개 사이트를 엽니다: https://gmountain01.github.io/bookedu/ (크롬·엣지 권장)
2. 또는 아래처럼 빌드한 `dist/index.html` 한 파일을 더블클릭해 **오프라인**으로 씁니다. 글꼴·사진·그림이 모두 파일 안에 들어 있어 인터넷 연결이 필요 없습니다.

**다른 곳에서 만든 책 옮기기:** 브라우저 저장소는 사이트 주소마다 따로이므로, 예전 파일(또는 다른 브라우저)에서 만든 책은 자동으로 옮겨지지 않습니다. 원래 쓰던 곳에서 「책 파일 → JSON 백업」으로 파일을 받은 뒤, 새 주소에서 「책 파일 → JSON 불러오기」를 누르면 됩니다. 사진이 포함된 책은 파일이 수 MB가 될 수 있습니다.

## 로컬 실행과 빌드

```bash
npm install          # Vite 8 (개발 도구만)
npm run dev          # 개발 서버 (http://localhost:5173)
npm run build        # dist/index.html 한 파일로 빌드 (스크립트·스타일·글꼴·이미지를 모두 인라인)
```

- 공개 사이트와 같은 **공개 빌드**는 `VITE_PUBLIC=1 npm run build` 입니다. 이 빌드에는 관리자(발표) 화면의 코드와 데이터가 들어가지 않습니다(`src/pages/admin.js` 대신 `src/pages/admin.public.js`가 쓰입니다). 이 저장소에는 관리자 화면 모듈이 없으므로 저장소에서 받은 코드는 `VITE_PUBLIC=1`로 빌드합니다.
- 검사 스크립트는 `tests/`에 있습니다(Python Playwright + PyMuPDF). 예: `python tests/qa.py <결과 폴더>`.
- 기술: Vite + 순수 JavaScript(ES 모듈) + CSS 변수 + IndexedDB. 런타임에 AI API나 외부 CDN을 쓰지 않습니다.

## 배포 (GitHub Pages)

`main` 브랜치에 푸시하면 `.github/workflows/pages.yml`이 공개 빌드를 만들어 GitHub Pages에 배포합니다(Pages 소스: GitHub Actions). 수동 실행은 Actions 탭의 **Run workflow**로 할 수 있습니다. 배포되는 폴더에는 `dist/index.html` 한 파일만 들어갑니다.

## 공개 저장소에 포함하지 않은 것

개발 과정의 작업 로그, 회의록, 프롬프트 원문, 사용자 대화 기록, 관리자(발표) 화면의 코드와 데이터, 테스트 증거 화면, 백업 폴더는 만든 사람의 기록이라 공개하지 않습니다. 공개 사이트에서 관리자 주소를 열면 안내 문구만 보입니다.

## 글꼴·사진·그림의 출처와 라이선스

- **글꼴:** 본문 고딕은 [Pretendard](https://github.com/orioncactus/pretendard)(SIL OFL 1.1), 본문 명조는 Noto Serif KR(SIL OFL 1.1)의 **서브셋**입니다. OFL의 예약 글꼴 이름 규정에 따라 수정본은 각각 「Chaekgongbang Sans」·「Chaekgongbang Serif」로 이름을 바꿔 넣었습니다. 라이선스 전문: `src/fonts/Pretendard-LICENSE.txt`, `src/fonts/ChaekgongbangSerif-LICENSE.txt`.
- **사진(표지·본문 기본 사진):** 모두 위키미디어 공용에서 가져온 공개 라이선스 사진이며, 앱이 뒤표지와 캡션에 출처를 자동으로 적습니다.
  - Visviva, 「Daegu Namgu alley」 — 퍼블릭 도메인 (https://commons.wikimedia.org/wiki/File:Daegu_Namgu_alley.jpg)
  - socialwalker, 「Sungui-dong」 (9654084092, 9654101736) — CC BY 2.0, 밝기·색 보정 (https://commons.wikimedia.org/wiki/File:Sungui-dong_(9654084092).jpg)
  - Kristy Kravchenko, Florian Pérennès, Ahmed Saffu — Unsplash 사진(위키미디어 공용 수록본), CC0
- **그림:** 정거장·역할·협업 장면의 리소그래프풍 SVG 일러스트는 이 프로젝트에서 만든 것입니다.
- **교육 내용의 출처:** `docs/SOURCES.md`

## 라이선스

코드의 별도 라이선스는 아직 정하지 않았습니다(저작권: gmountain01). 글꼴·사진은 위의 각 라이선스를 따릅니다.
