import { blankProject, SCHEMA_VERSION } from './state.js';

// Sample book written for this app (original text, no third-party copyright). W-035: rewritten as one essay that reads
// from the first page to the last (an arrival, close observation, the shops, the tree and its people, a return), keeping
// the sentences the learning screens quote. The people, shops and alley are invented for teaching (said on the copyright
// page); the photographs are captioned as reference photos with their credits, not as the narrator's own record.
export function sampleProject() {
  const p = blankProject();
  let n = 0;
  const id = () => `s${++n}`;
  const H = (level, text) => ({ id: id(), type: 'heading', level, text });
  const P = (text) => ({ id: id(), type: 'paragraph', text });
  return {
    ...p,
    id: `sample-${p.id}`,
    schemaVersion: SCHEMA_VERSION,
    meta: {
      title: '골목에서 찾은 이야기',
      authorAlias: '책공방 편집부',
      genre: '수필',
      topic: '학교 앞 골목을 천천히 걸으며 발견한 작은 가게와 사람들',
      targetReader: '매일 같은 길로 등교하는 중학생',
    },
    assets: [
      // W-035: the figures are photographs (reference photos with credits); the old flat drawings stay available for old files
      { id: 'a-alley', builtin: 'builtin:photo-alley', name: '햇빛이 드는 골목 (자료 사진)', sourceNote: 'Visviva, 「Daegu Namgu alley」, 퍼블릭 도메인 (위키미디어 공용)', mimeType: 'image/jpeg', width: 978, height: 1200 },
      { id: 'a-tree', builtin: 'builtin:photo-pots', name: '화분과 나무 (자료 사진)', sourceNote: 'socialwalker, 「Sungui-dong」, CC BY 2.0 (위키미디어 공용)', mimeType: 'image/jpeg', width: 1200, height: 1098 },
      // W-034: a cover-only photograph; credit printed on the back cover
      { id: 'a-cover', builtin: 'builtin:cover-walk', name: '골목 산책 (표지 사진)', sourceNote: 'socialwalker, 「Sungui-dong」, CC BY 2.0 (위키미디어 공용)', mimeType: 'image/jpeg', width: 1500, height: 2128 },
    ],
    imagePrompt: '해 질 무렵 좁은 골목길, 양쪽에 낮은 건물과 노란 불빛 창문, 차분한 색연필 그림체, 가로 그림',
    blocks: [
      H(1, '1장 늘 지나던 길'),
      P('아침마다 지나는 골목이 있다. 교문까지 걸어서 칠 분. 나는 그 칠 분 동안 거의 땅만 보고 걸었다. 그러던 어느 날, 학교가 일찍 끝나서 처음으로 그 길을 천천히 걸어 보았다.'),
      P('오후의 골목은 아침과 달랐다. 해가 낮게 기울어 담벼락 한쪽만 노랗게 밝았고, 그늘진 쪽 바닥에는 아침에 뿌린 물기가 아직 남아 있었다. 매일 밟고 지나던 보도블록에는 금이 간 자리마다 작은 풀이 올라와 있었다.'),
      H(2, '천천히 걸으면 보이는 것'),
      P('빠르게 지나갈 때는 몰랐던 간판, 화분, 고양이가 눈에 들어왔다. 같은 길인데도 걸음의 속도가 바뀌니 전혀 다른 장소처럼 느껴졌다.'),
      { id: id(), type: 'image', assetId: 'a-alley', caption: '그림 1. 햇빛이 비스듬히 드는 골목 (자료 사진: Visviva, 대구, 퍼블릭 도메인)', alt: '양쪽에 낡은 흙벽과 대문이 있고, 오른쪽 담벼락에만 햇빛이 든 좁은 골목길 사진' },
      P('그날부터 나는 아침에는 늘 하던 대로 서둘러 걷고, 수업이 일찍 끝나는 날에는 같은 길을 거꾸로, 천천히 걸었다. 휴대전화 대신 작은 수첩을 들고 다니며 눈에 띄는 것을 한 줄씩 적었다. 처음 며칠은 적을 것이 별로 없었다. 그런데 일주일쯤 지나자 수첩의 한 쪽이 금방 찼다.'),
      P('수첩에는 이런 것들이 적혔다. 세탁소 앞 의자에 늘 같은 시간에 앉아 있는 고양이, 비가 온 다음 날에만 문을 활짝 열어 두는 문구점, 담장 위로 넘어온 장미 넝쿨. 하나하나는 사소했지만 모아 놓고 보니 골목에도 하루의 순서가 있었다.'),
      H(3, '골목의 가게들'),
      P('골목에는 작은 가게가 세 곳 있었다. 나는 가게마다 들러 사장님께 직접 여쭈어 보고, 수첩에 가게 이름과 문을 연 해를 적었다.'),
      { id: id(), type: 'table', caption: '표 1. 골목 가게 조사', rows: [['가게', '하는 일', '문을 연 해'], ['동네 문구점', '학용품 판매', '1998년'], ['작은 세탁소', '옷 수선과 세탁', '2005년'], ['꽃집', '화분과 꽃다발', '2019년']] },
      P('가장 오래된 곳은 문구점이었다. 사장님은 내가 태어나기 훨씬 전부터 같은 자리에서 연필과 공책을 팔았다고 하셨다. 진열대 아래쪽에는 요즘은 잘 쓰지 않는 펜촉과 색 분필이 아직 남아 있었다. 꽃집은 반대로 가장 늦게 생긴 가게였는데, 골목에서 유일하게 가게 앞을 매일 물청소하는 곳이었다.'),
      H(4, '조사하며 배운 점'),
      P('사람에게 묻고, 들은 것을 그대로 적는 일은 생각보다 조심스러웠다. 날짜 하나도 다시 확인해야 했다.'),
      P('세탁소 사장님은 처음에 가게를 연 해를 2004년이라고 하셨다가, 다음 날 지나가는 나를 불러 세워 2005년이 맞다고 고쳐 주셨다. 그 뒤로 나는 들은 말을 적을 때 날짜를 함께 적고, 헷갈리는 것은 한 번 더 여쭈어 보았다. 기록은 기억보다 정확해야 했고, 그 기억을 나누어 준 사람에게 예의를 지키는 일이기도 했다.'),
      H(1, '2장 골목의 나무'),
      P('골목 끝에는 큰 나무가 한 그루 있다. 평상에 앉아 계시던 할머니 한 분이 나무를 올려다보며 말씀하셨다.'),
      { id: id(), type: 'paragraph', style: 'quote', text: '“내가 너만 할 때도 이 나무는 여기 있었어. 그때는 지금보다 훨씬 작았지.”' },
      { id: id(), type: 'image', assetId: 'a-tree', caption: '그림 2. 화분과 장미 너머로 가지를 뻗은 나무 (자료 사진: socialwalker, 인천 숭의동, CC BY 2.0)', alt: '길가에 화분이 줄지어 있고, 그 뒤로 빨간 장미 넝쿨과 잎이 무성한 나무가 서 있는 골목 사진' },
      P('나무 아래에는 누군가 내놓은 화분들이 줄지어 있었다. 고무 대야에 심은 고추, 금 간 항아리에 담긴 국화, 이름을 모르는 다육식물. 주인이 누구냐고 여쭈자 할머니는 다 같이 키우는 거라며 웃으셨다. 여름이면 나무 그늘이 화분까지 닿고, 지나가는 사람들이 한 번씩 물을 준다고 했다.'),
      H(2, '나무 아래의 사람들'),
      P('나무 아래 평상은 골목의 쉼터였다. 오전에는 할머니들이, 오후에는 학원에 가기 전의 초등학생들이 앉아 있었다. 나는 몇 번 그 옆에 앉아 수첩을 펼쳤지만, 대부분은 아무것도 적지 않고 이야기를 들었다. 날씨 이야기, 손주 이야기, 새로 생긴 가게 이야기. 골목의 소식은 이 평상에서 가장 먼저 퍼졌다.'),
      P('하루는 평상에 앉아 있던 아저씨가 내 수첩을 보고 무엇을 적느냐고 물었다. 골목에서 본 것을 적는다고 하자, 아저씨는 잠시 생각하더니 나무 둥치의 오래된 상처를 가리켰다. 오래전 태풍에 큰 가지가 부러진 자리라고 했다. 그 이야기를 듣고 다시 보니, 나무는 부러진 쪽을 비켜 반대편으로 더 넓게 가지를 뻗고 있었다.'),
      H(2, '다시 걷는 길'),
      P('아침에는 여전히 서둘러 걷는다. 하지만 이제는 바닥만 보지 않는다. 문구점 셔터가 반쯤 올라가 있으면 사장님이 일찍 나오셨구나 하고, 꽃집 앞이 젖어 있으면 방금 물청소를 했구나 한다. 같은 길이 매일 조금씩 다르다는 것을 알게 되자, 칠 분은 더 이상 지루한 시간이 아니었다.'),
      P('이제 나는 등굣길 칠 분을 조금 다르게 쓴다. 매일 하나씩, 어제 보지 못한 것을 찾는다. 이 책은 그 기록이다.'),
    ],
    layout: { pageSize: 'A5', theme: 'classic', fontFamily: 'myeongjo', fontSize: 10, lineHeight: 1.75, margin: 18 },
    frontMatter: {
      titlePage: '등굣길 칠 분의 기록',
      copyrightText: '골목에서 찾은 이야기\n지은이 책공방 편집부\n펴낸 곳 책공방 교실(교육용 예시)\n\n이 책은 수업용 예시이며 실제로 발행된 책이 아닙니다.\n책 속 인물과 가게, 골목은 학습용으로 꾸민 것입니다.\n본문 사진은 책 속 골목을 떠올리게 하는 자료 사진이며, 출처는 각 사진 설명에 적었습니다.\nISBN은 발급받지 않았습니다.',
      preface: '한 학생이 매일 지나치던 골목을 천천히 걸으며 수첩에 적은 것들을 엮었습니다. 가게에서 들은 이야기, 나무 아래 평상에서 들은 이야기, 그리고 걸음을 늦추자 보이기 시작한 작은 것들입니다.\n읽는 여러분의 등굣길에도 그런 것이 하나쯤 있을 것입니다.',
    },
    // W-035: the front carries title, subtitle (the title page's subtitle), a short copy line and the author, each in its own
    // place; the back carries a headline, the introduction and the reader it suits (meta.targetReader).
    cover: {
      backgroundColor: '#e6dccf', accentColor: '#a8322d', layout: 'full', focusX: 50, focusY: 30, textY: 0.565, textAlign: 'right', ink: '#2a221c', imageId: 'a-cover',
      copy: '같은 길도 천천히 걸으면 다른 이야기가 보인다',
      backHeadline: '땅만 보고 걷던 칠 분이, 어느 날 조금 느려졌다.',
      backText: '학교가 일찍 끝난 날, 한 학생이 매일 지나던 골목을 처음으로 천천히 걷는다. 그날부터 수첩을 들고 다니며 문구점과 세탁소 사장님께 이야기를 듣고, 골목 끝 큰 나무 아래 평상에서 동네 사람들의 이야기를 듣는다.\n작은 관찰이 모여 골목의 하루가 되는 과정을 담은 수필이다. 들은 말을 다시 확인하며 기록하는 법도 함께 배울 수 있다.',
    },
    reflection: { designReason: '' },
    progress: { currentStep: 1, tocReviewed: false },
  };
}
