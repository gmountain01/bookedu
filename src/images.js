import { LIMITS, getProject, imageChars } from './state.js';
import coverWalk from './covers/cover-walk.jpg';
import coverWindow from './covers/cover-window.jpg';
import coverHorizon from './covers/cover-horizon.jpg';
import coverTree from './covers/cover-tree.jpg';
import photoAlley from './photos/photo-alley.jpg';
import photoPots from './photos/photo-pots.jpg';
import photoTree from './photos/photo-tree.jpg';
import photoWindow from './photos/photo-window.jpg';
import photoSea from './photos/photo-sea.jpg';

// Built-in illustrations drawn for this app (no external license needed).
const svg = (body, bg) => `data:image/svg+xml;charset=utf-8,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 260"><rect width="400" height="260" fill="${bg}"/>${body}</svg>`)}`;

export const BUILTINS = {
  'builtin:alley': { name: '골목길', src: svg('<path d="M0 260 L170 120 L230 120 L400 260Z" fill="#c9ced8"/><rect x="20" y="40" width="110" height="170" fill="#8a94a8"/><rect x="270" y="30" width="110" height="180" fill="#6f7a90"/><rect x="45" y="70" width="25" height="30" fill="#ffe36e"/><rect x="300" y="60" width="25" height="30" fill="#ffe36e"/><rect x="340" y="110" width="25" height="30" fill="#ffe36e"/><circle cx="200" cy="70" r="26" fill="#fff"/>', '#dfe4ec') },
  'builtin:tree': { name: '큰 나무', src: svg('<rect x="185" y="140" width="30" height="110" fill="#6b4f3a"/><circle cx="200" cy="110" r="80" fill="#3f7d5a"/><circle cx="140" cy="140" r="50" fill="#4f9469"/><circle cx="262" cy="138" r="52" fill="#4f9469"/><rect y="240" width="400" height="20" fill="#9bb38a"/>', '#e8f0f4') },
  'builtin:night': { name: '별이 뜬 밤', src: svg('<circle cx="320" cy="60" r="30" fill="#ffe36e"/><circle cx="332" cy="52" r="26" fill="#1b2a4a"/><g fill="#fff"><circle cx="60" cy="50" r="3"/><circle cx="120" cy="90" r="2"/><circle cx="200" cy="40" r="3"/><circle cx="250" cy="110" r="2"/><circle cx="90" cy="150" r="2"/></g><path d="M0 260 L0 200 Q100 160 200 200 T400 190 L400 260Z" fill="#0f1830"/>', '#1b2a4a') },
  'builtin:books': { name: '책 더미', src: svg('<rect x="110" y="190" width="180" height="34" fill="#1d4fb8"/><rect x="125" y="156" width="160" height="34" fill="#b3261e"/><rect x="100" y="122" width="170" height="34" fill="#3f7d5a"/><rect x="140" y="88" width="140" height="34" fill="#e0a400"/><g fill="#fff" opacity=".7"><rect x="120" y="203" width="60" height="6"/><rect x="135" y="169" width="60" height="6"/><rect x="110" y="135" width="60" height="6"/><rect x="150" y="101" width="60" height="6"/></g>', '#f2f4f7') },
  'builtin:chart': { name: '막대 그래프', src: svg('<line x1="50" y1="220" x2="360" y2="220" stroke="#1b2230" stroke-width="3"/><rect x="80" y="150" width="50" height="70" fill="#1d4fb8"/><rect x="160" y="100" width="50" height="120" fill="#1d4fb8"/><rect x="240" y="60" width="50" height="160" fill="#b3261e"/>', '#ffffff') },
};

// W-035: body photographs for 「이미지 삽입」 (the sample book's figures among them). Openly licensed, cropped and graded to one
// look by scripts/body_photos.py; name + desc say which scene each suits; credit fills the asset's source note.
// The flat drawings in BUILTINS stay so older saved books keep their pictures, but are no longer offered.
export const BODY_PHOTOS = {
  'builtin:photo-alley': { name: '햇빛이 드는 골목', desc: '흙벽 사이 좁은 골목, 한쪽 담에만 햇빛 (세로) · 장소를 처음 보여 줄 때', src: photoAlley, width: 978, height: 1200,
    credit: 'Visviva, 「Daegu Namgu alley」, 퍼블릭 도메인 (위키미디어 공용)' },
  'builtin:photo-pots': { name: '화분과 나무', desc: '길가에 줄지은 화분, 장미 넝쿨과 큰 나무 (거의 정사각) · 동네 사람들의 손길, 계절', src: photoPots, width: 1200, height: 1098,
    credit: 'socialwalker, 「Sungui-dong」, CC BY 2.0 (위키미디어 공용)' },
  'builtin:photo-tree': { name: '언덕 위의 큰 나무', desc: '봄 잎이 난 큰 나무와 잔디 언덕, 나무에 기댄 사람 (가로) · 쉼, 기다림, 자연', src: photoTree, width: 1200, height: 873,
    credit: 'Kristy Kravchenko (Unsplash), CC0 (위키미디어 공용)' },
  'builtin:photo-window': { name: '창가의 빛', desc: '어두운 방, 초록 창틀 너머 바깥과 식탁 위 그릇 (가로) · 집, 혼자 있는 시간, 생각', src: photoWindow, width: 1200, height: 867,
    credit: 'Florian Pérennès (Unsplash), CC0 (위키미디어 공용)' },
  'builtin:photo-sea': { name: '노을 진 바다', desc: '붉은 하늘과 낮은 구름, 잔잔한 수평선 (가로) · 마무리, 여운, 먼 곳', src: photoSea, width: 1200, height: 935,
    credit: 'Ahmed Saffu (Unsplash), CC0 (위키미디어 공용)' },
};

// Cover-only photographs (W-034; docs/evidence/c18/sources/sources.json). Each carries where its title sits (zone),
// the ink that reads there, the paper colour sampled from the picture (spine, back cover, panel), an accent, and
// its credit line, printed on the back cover. Openly licensed: CC BY 2.0 (credit required) or CC0.
// copyY: where the copy line sits (measured: luminance ≥ 0.6 behind it for the walk photo, below the title block).
// maxLen: the longest title (book.js titleLen s < m < l < xl) the open area holds; past it the cover uses the panel
// layout (MT-18). authorWithTitle: the author goes under the title (the lower part of the picture is busy).
export const COVER_IMAGES = {
  'builtin:cover-walk': { name: '골목 산책 (사진)', src: coverWalk, width: 1500, height: 2128, layout: 'full', textY: 0.565, textAlign: 'right', ink: '#2a221c', paper: '#e6dccf', accent: '#a8322d', focusY: 30, maxLen: 'l', copyY: 0.74,
    credit: '표지 사진: socialwalker, 「Sungui-dong」, CC BY 2.0 (위키미디어 공용, 밝기·색 보정)' },
  'builtin:cover-window': { name: '창가의 빛 (사진)', src: coverWindow, width: 1240, height: 1759, layout: 'full', textY: 0.06, textAlign: 'left', ink: '#f3eee4', paper: '#1f2a24', accent: '#3f8a5a', maxLen: 'm', authorWithTitle: true, copyY: 0.24,
    credit: '표지 사진: Florian Pérennès (Unsplash), CC0' },
  'builtin:cover-horizon': { name: '노을 바다 (사진)', src: coverHorizon, width: 1240, height: 1759, layout: 'full', textY: 0.2, textAlign: 'center', ink: '#fff6ef', paper: '#b94a3f', accent: '#b94a3f', maxLen: 'l', copyY: 0.36,
    credit: '표지 사진: Ahmed Saffu (Unsplash), CC0' },
  'builtin:cover-tree': { name: '큰 나무 (사진)', src: coverTree, width: 1100, height: 1561, layout: 'panel', focusY: 70, ink: '#1e2a1b', paper: '#eceee2', accent: '#3d6b2f',
    credit: '표지 사진: Kristy Kravchenko (Unsplash), CC0' },
};

export function assetSrc(asset) {
  if (!asset) return '';
  return asset.builtin ? (BUILTINS[asset.builtin] || BODY_PHOTOS[asset.builtin] || COVER_IMAGES[asset.builtin])?.src || '' : asset.data;
}
export const assetById = (id) => getProject().assets.find((a) => a.id === id);

// Validate type/size, then downscale the longer edge to LIMITS.imageEdge in the browser.
export async function readImageFile(file) {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type))
    throw new Error(`'${file.name}'은(는) 올릴 수 없는 형식이에요. PNG, JPEG, WebP만 가능해요.`);
  if (file.size > LIMITS.imageBytes)
    throw new Error(`'${file.name}'은(는) ${(file.size / 1048576).toFixed(1)}MB예요. 5MB 이하 이미지를 골라 주세요.`);
  const bitmap = await createImageBitmap(file).catch(() => { throw new Error(`'${file.name}'을(를) 이미지로 읽을 수 없어요. 파일이 손상됐을 수 있어요.`); });
  const scale = Math.min(1, LIMITS.imageEdge / Math.max(bitmap.width, bitmap.height));
  const w = Math.round(bitmap.width * scale);
  const hgt = Math.round(bitmap.height * scale);
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = hgt;
  canvas.getContext('2d').drawImage(bitmap, 0, 0, w, hgt);
  bitmap.close?.();
  // Small PNGs stay PNG (sharp line art); big ones become JPEG so backups stay restorable.
  let mime = file.type === 'image/png' ? 'image/png' : 'image/jpeg';
  let data = canvas.toDataURL(mime, 0.85);
  if (mime === 'image/png' && data.length > 1024 * 1024) { mime = 'image/jpeg'; data = canvas.toDataURL(mime, 0.85); }
  const left = LIMITS.totalImageChars - imageChars();
  if (data.length > left) {
    throw new Error(`그림을 모두 합친 용량이 너무 커져요(남은 공간 약 ${Math.max(0, left / 1048576).toFixed(1)}MB). 다른 그림을 빼거나 더 작은 그림을 골라 주세요.`);
  }
  return { data, mimeType: mime, width: w, height: hgt, name: file.name.slice(0, 120) };
}
