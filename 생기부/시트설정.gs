/**
 * 생기부 비서 — 구글 시트 설정 스크립트
 *
 * 설치: 빈 구글 시트 → 확장 프로그램 → Apps Script → 이 파일 내용 전체 붙여넣기 → 저장
 *       → 시트 새로고침 → 상단 메뉴 [생기부 비서] → ① 시트 만들기
 *
 * 체크 항목을 바꾸려면 아래 CHECKS 만 고치고 ① 시트 만들기를 다시 실행한다.
 * (이미 입력한 내용이 있으면 덮어쓰기 전에 물어본다.)
 */

const LIMIT_BYTES = 1500;
const MAX_STUDENTS = 35;
const HEADER_ROWS = 2;

// 탭 이름 → 대상 반 (학년, 반)
const TABS = [
  { name: '세특_중1', type: '세특', classes: [[1, 1], [1, 4]] },
  { name: '세특_중3', type: '세특', classes: [[3, 6], [3, 7], [3, 8]] },
  { name: '자율_중3', type: '자율', classes: [[3, 7]] },
  { name: '행발_중3', type: '행발', classes: [[3, 7]] },
];

const CHECKS = {
  세특: [
    { group: 'A 탐구 과정', color: '#dbeafe', items: [
      '가설을 세우고 근거를 제시함',
      '변인을 구분하여 실험을 설계함',
      '측정값을 표로 정리하여 기록함',
      '결과를 그래프로 나타내고 경향성을 설명함',
      '예상과 다른 결과의 원인을 찾아 제시함',
      '오차 원인과 개선 방법을 제시함',
      '실험 도구를 안전 수칙에 맞게 다룸',
    ] },
    { group: 'B 개념 표현', color: '#dcfce7', items: [
      '과학 용어를 정확히 사용하여 설명함',
      '개념을 그림·모형으로 표현함',
      '일상 현상을 개념과 연결하여 설명함',
      '두 개념의 차이를 비교하여 제시함',
    ] },
    { group: 'C 소통·협력', color: '#fef3c7', items: [
      '모둠에서 역할을 맡아 수행함',
      '결과를 근거를 들어 발표함',
      '다른 모둠 발표에 질문·의견을 제시함',
      '동료의 설명을 듣고 자기 생각을 수정함',
    ] },
    { group: 'D 확장', color: '#fce7f3', items: [
      '수업 후 추가 자료를 찾아 정리함',
      '활동지 외 추가 탐구 질문을 제시함',
    ] },
  ],
  자율: [
    { group: '학급·학교 활동', color: '#dbeafe', items: [
      '학급 회의에서 안건을 제안함',
      '회의에서 의견을 조율하여 결론을 정리함',
      '학급 행사 준비에서 역할을 맡아 수행함',
      '학교 캠페인·행사에 참여함',
      '학급 규칙을 만들고 지키는 활동에 참여함',
    ] },
  ],
  행발: [
    { group: '인성', color: '#dbeafe', items: [
      '규칙을 지키고 친구에게 안내함',
      '공용 물품을 먼저 정리함',
      '맡은 일을 기한 내 완수함',
      '예의 바른 언어를 사용함',
      '잘못을 인정하고 바로잡음',
    ] },
    { group: '교우관계', color: '#dcfce7', items: [
      '어려워하는 친구를 도움',
      '모둠에서 의견을 모아 역할을 나눔',
      '다른 의견을 끝까지 듣고 반응함',
      '친구 간 갈등을 중재함',
      '새로운 친구에게 먼저 다가감',
    ] },
    { group: '학업', color: '#fef3c7', items: [
      '수업 중 질문함',
      '과제를 꾸준히 제출함',
      '모르는 내용을 물어 해결함',
      '학습 계획을 세워 실천함',
      '수업 내용을 자기 말로 설명함',
    ] },
  ],
};

// 체크 앞/뒤에 들어가는 입력 칸
const TEXT_COLS = {
  세특: { before: [], after: ['활동1 판독요약', '활동2 판독요약', '교사 메모'] },
  자율: { before: ['역할(임원·부서)'], after: ['참여 행사 번호(쉼표)', '교사 메모'] },
  행발: { before: [], after: ['관심 분야', '특기·재능', '보완점', '보완점 변화 사례', '구체 사례 메모(필수)'] },
};
const KEY_COLS = ['학년', '반', '번호'];
const TAIL_COLS = ['초안', '검수경고', '최종본', '바이트', '확정'];

function onOpen() {
  SpreadsheetApp.getUi().createMenu('생기부 비서')
    .addItem('① 시트 만들기 (처음 한 번)', 'setupSheets')
    .addItem('② 초안 불러오기', 'importDrafts')
    .addItem('③ 입력용 내보내기', 'exportForPaste')
    .addToUi();
}

// ---------- ① 시트 만들기 ----------

function setupSheets() {
  const ss = SpreadsheetApp.getActive();
  const ui = SpreadsheetApp.getUi();

  const filled = TABS.filter(t => {
    const sh = ss.getSheetByName(t.name);
    return sh && sh.getLastRow() > HEADER_ROWS;
  }).map(t => t.name);
  if (filled.length) {
    const ok = ui.alert('덮어쓰기 확인',
      filled.join(', ') + ' 탭에 내용이 있습니다. 새로 만들면 모두 지워집니다. 계속할까요?',
      ui.ButtonSet.YES_NO);
    if (ok !== ui.Button.YES) return;
  }

  TABS.forEach(t => buildTab(ss, t));
  buildEventTab(ss);

  const blank = ss.getSheetByName('시트1') || ss.getSheetByName('Sheet1');
  if (blank && blank.getLastRow() === 0 && ss.getSheets().length > 1) ss.deleteSheet(blank);

  ui.alert('완료', '탭 ' + (TABS.length + 1) + '개를 만들었습니다. 빈 번호 행은 지워도 됩니다.', ui.ButtonSet.OK);
}

function layout(type) {
  // 열 구성: [{group, header, kind, color}]
  const cols = [];
  KEY_COLS.forEach(h => cols.push({ group: '학생', header: h, kind: 'key', color: '#e5e7eb' }));
  TEXT_COLS[type].before.forEach(h => cols.push({ group: '입력', header: h, kind: 'text', color: '#f3f4f6' }));
  CHECKS[type].forEach(g => g.items.forEach(i => cols.push({ group: g.group, header: i, kind: 'check', color: g.color })));
  TEXT_COLS[type].after.forEach(h => cols.push({ group: '입력', header: h, kind: 'text', color: '#f3f4f6' }));
  TAIL_COLS.forEach(h => cols.push({ group: '작성·확정', header: h, kind: 'tail', color: '#ede9fe' }));
  return cols;
}

function buildTab(ss, tab) {
  let sh = ss.getSheetByName(tab.name);
  if (sh) sh.clear(); else sh = ss.insertSheet(tab.name);
  sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns()).clearDataValidations();
  sh.clearConditionalFormatRules();

  const cols = layout(tab.type);
  const n = cols.length;
  if (sh.getMaxColumns() < n) sh.insertColumnsAfter(sh.getMaxColumns(), n - sh.getMaxColumns());

  // 1행: 그룹 이름(같은 그룹은 병합), 2행: 항목
  sh.getRange(1, 1, 1, n).breakApart();
  let start = 0;
  for (let c = 1; c <= n; c++) {
    if (c === n || cols[c].group !== cols[start].group) {
      const r = sh.getRange(1, start + 1, 1, c - start);
      if (c - start > 1) r.merge();
      r.getCell(1, 1).setValue(cols[start].group);
      start = c;
    }
  }
  sh.getRange(2, 1, 1, n).setValues([cols.map(c => c.header)]);
  cols.forEach((c, i) => sh.getRange(1, i + 1, 2, 1).setBackground(c.color));
  sh.getRange(1, 1, 2, n).setFontWeight('bold').setVerticalAlignment('middle').setHorizontalAlignment('center');
  sh.getRange(2, 1, 1, n).setWrap(true);
  sh.setRowHeight(2, 90);

  // 학생 행
  const rows = [];
  tab.classes.forEach(([g, c]) => { for (let i = 1; i <= MAX_STUDENTS; i++) rows.push([g, c, i]); });
  const first = HEADER_ROWS + 1;
  if (sh.getMaxRows() < first + rows.length) sh.insertRowsAfter(sh.getMaxRows(), first + rows.length - sh.getMaxRows());
  sh.getRange(first, 1, rows.length, 3).setValues(rows);

  const col = h => cols.findIndex(c => c.header === h) + 1;

  // 체크박스
  cols.forEach((c, i) => {
    if (c.kind === 'check') sh.getRange(first, i + 1, rows.length, 1).insertCheckboxes();
  });
  sh.getRange(first, col('확정'), rows.length, 1).insertCheckboxes();

  // 바이트 (최종본 기준, 나이스: 한글·특수문자 3 / ASCII 1 / 줄바꿈 2)
  const fin = col('최종본');
  const byteCol = col('바이트');
  const formulas = rows.map((_, i) => {
    const ref = sh.getRange(first + i, fin).getA1Notation();
    return ['=IF(' + ref + '="","",LEN(' + ref + ')+2*LEN(REGEXREPLACE(' + ref + ',"[\\x00-\\x7F]",""))' +
      '+LEN(' + ref + ')-LEN(SUBSTITUTE(' + ref + ',CHAR(10),"")))'];
  });
  sh.getRange(first, byteCol, rows.length, 1).setFormulas(formulas);

  const byteRange = sh.getRange(first, byteCol, rows.length, 1);
  const doneRange = sh.getRange(first, 1, rows.length, n);
  const doneRef = sh.getRange(first, col('확정')).getA1Notation().replace(/\d+$/, '');
  sh.setConditionalFormatRules([
    SpreadsheetApp.newConditionalFormatRule().whenNumberGreaterThan(LIMIT_BYTES)
      .setBackground('#fecaca').setFontColor('#991b1b').setRanges([byteRange]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenFormulaSatisfied('=$' + doneRef + first + '=TRUE')
      .setBackground('#f0fdf4').setRanges([doneRange]).build(),
  ]);

  // 폭·줄바꿈
  sh.setColumnWidths(1, 3, 44);
  cols.forEach((c, i) => {
    if (c.kind === 'check') sh.setColumnWidth(i + 1, 64);
    if (c.kind === 'text') sh.setColumnWidth(i + 1, 200);
  });
  ['초안', '최종본'].forEach(h => sh.setColumnWidth(col(h), 380));
  sh.setColumnWidth(col('검수경고'), 220);
  sh.setColumnWidth(byteCol, 60);
  sh.setColumnWidth(col('확정'), 50);
  sh.getRange(first, 1, rows.length, n).setVerticalAlignment('top');
  cols.forEach((c, i) => {
    if (c.kind === 'text' || c.header === '초안' || c.header === '최종본' || c.header === '검수경고') {
      sh.getRange(first, i + 1, rows.length, 1).setWrap(true);
    }
  });
  sh.setFrozenRows(HEADER_ROWS);
  sh.setFrozenColumns(3);
}

function buildEventTab(ss) {
  const name = '행사목록';
  let sh = ss.getSheetByName(name);
  if (sh && sh.getLastRow() > 1) return; // 이미 적은 행사는 지우지 않음
  if (!sh) sh = ss.insertSheet(name);
  sh.getRange(1, 1, 1, 5).setValues([['번호', '날짜', '행사명', '공통 문구 (교사 작성, ~함.)', '비고']])
    .setFontWeight('bold').setBackground('#e5e7eb');
  sh.setColumnWidths(1, 2, 80);
  sh.setColumnWidth(3, 200);
  sh.setColumnWidth(4, 420);
  sh.setFrozenRows(1);
}

// ---------- ② 초안 불러오기 ----------
// 초안 파일(Claude가 드라이브에 만든 시트) 열: 탭, 학년, 반, 번호, 초안, 검수경고

function importDrafts() {
  const ui = SpreadsheetApp.getUi();
  const res = ui.prompt('초안 불러오기', '초안 파일의 주소(URL)를 붙여 넣으세요.', ui.ButtonSet.OK_CANCEL);
  if (res.getSelectedButton() !== ui.Button.OK) return;
  const m = res.getResponseText().match(/[-\w]{25,}/);
  if (!m) { ui.alert('주소에서 파일 ID를 찾지 못했습니다.'); return; }

  const src = SpreadsheetApp.openById(m[0]).getSheets()[0].getDataRange().getValues();
  const head = src[0].map(String);
  const idx = h => head.indexOf(h);
  ['탭', '학년', '반', '번호', '초안'].forEach(h => {
    if (idx(h) < 0) throw new Error('초안 파일에 "' + h + '" 열이 없습니다.');
  });

  const ss = SpreadsheetApp.getActive();
  const stats = { 반영: 0, 확정건너뜀: 0, 못찾음: [] };
  const byTab = {};
  src.slice(1).forEach(r => {
    const t = String(r[idx('탭')]).trim();
    (byTab[t] = byTab[t] || []).push(r);
  });

  Object.keys(byTab).forEach(tabName => {
    const sh = ss.getSheetByName(tabName);
    if (!sh) { stats.못찾음.push(tabName + ' 탭'); return; }
    const header = sh.getRange(HEADER_ROWS, 1, 1, sh.getLastColumn()).getValues()[0].map(String);
    const c = h => header.indexOf(h);
    const nRows = sh.getLastRow() - HEADER_ROWS;
    const data = sh.getRange(HEADER_ROWS + 1, 1, nRows, header.length).getValues();

    const rowOf = {};
    data.forEach((r, i) => { rowOf[r[0] + '-' + r[1] + '-' + r[2]] = i; });

    byTab[tabName].forEach(r => {
      const key = Number(r[idx('학년')]) + '-' + Number(r[idx('반')]) + '-' + Number(r[idx('번호')]);
      const i = rowOf[key];
      if (i === undefined) { stats.못찾음.push(tabName + ' ' + key); return; }
      if (data[i][c('확정')] === true) { stats.확정건너뜀++; return; }
      const draft = String(r[idx('초안')] || '');
      data[i][c('초안')] = draft;
      data[i][c('검수경고')] = idx('검수경고') >= 0 ? String(r[idx('검수경고')] || '') : '';
      if (!String(data[i][c('최종본')]).trim()) data[i][c('최종본')] = draft;
      stats.반영++;
    });

    ['초안', '검수경고', '최종본'].forEach(h => {
      sh.getRange(HEADER_ROWS + 1, c(h) + 1, nRows, 1).setValues(data.map(r => [r[c(h)]]));
    });
  });

  ui.alert('불러오기 완료',
    '반영 ' + stats.반영 + '명 / 확정이라 건너뜀 ' + stats.확정건너뜀 + '명' +
    (stats.못찾음.length ? '\n못 찾음: ' + stats.못찾음.join(', ') : '') +
    '\n\n이미 고쳐 둔 최종본은 덮어쓰지 않았습니다.', ui.ButtonSet.OK);
}

// ---------- ③ 입력용 내보내기 ----------

function exportForPaste() {
  const ss = SpreadsheetApp.getActive();
  const out = [['영역', '학년', '반', '번호', '최종본', '바이트']];
  TABS.forEach(t => {
    const sh = ss.getSheetByName(t.name);
    if (!sh || sh.getLastRow() <= HEADER_ROWS) return;
    const header = sh.getRange(HEADER_ROWS, 1, 1, sh.getLastColumn()).getValues()[0].map(String);
    const c = h => header.indexOf(h);
    const data = sh.getRange(HEADER_ROWS + 1, 1, sh.getLastRow() - HEADER_ROWS, header.length).getValues();
    data.forEach(r => {
      const text = String(r[c('최종본')] || '').trim();
      if (r[c('확정')] === true && text) out.push([t.name, r[0], r[1], r[2], text, r[c('바이트')]]);
    });
  });

  let sh = ss.getSheetByName('입력용');
  if (sh) sh.clear(); else sh = ss.insertSheet('입력용');
  sh.getRange(1, 1, out.length, out[0].length).setValues(out);
  sh.getRange(1, 1, 1, out[0].length).setFontWeight('bold').setBackground('#e5e7eb');
  sh.setColumnWidth(5, 480);
  sh.getRange(2, 5, Math.max(out.length - 1, 1), 1).setWrap(true);
  sh.setFrozenRows(1);
  ss.setActiveSheet(sh);

  SpreadsheetApp.getUi().alert('입력용 내보내기',
    '확정된 ' + (out.length - 1) + '명을 [입력용] 탭에 모았습니다.\n' +
    '파일 → 다운로드 → CSV(현재 시트)로 받아 붙여넣기 도우미에서 여세요.',
    SpreadsheetApp.getUi().ButtonSet.OK);
}
