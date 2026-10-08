// Read-only editorial viewer. Do not import app state, auth, sync or persistence.
const $ = id => document.getElementById(id);
const root = new URL('../', location.href);
let entries = [], filtered = [], currentId = '', topics = [], parents = new Map(), sources = [], mockSets = [];
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
async function read(path, base = root) {
  const url = new URL(path, base);
  if (url.origin !== root.origin || !url.pathname.startsWith(root.pathname)) throw new Error('教材の参照先が不正です');
  const response = await fetch(url, {cache: 'no-cache'});
  if (!response.ok) throw new Error(`教材を取得できませんでした（${response.status}）`);
  return response.json();
}
function asset(path) {
  const url = new URL(path, root);
  if (url.origin !== root.origin || !url.pathname.startsWith(`${root.pathname}assets/`)) throw new Error('画像の参照先が不正です');
  return url.href;
}
function imageLink(path, alt, className = 'figure') {
  const link = node('a'); link.href = asset(path); link.target = '_blank'; link.rel = 'noopener';
  const image = node('img', undefined, className); image.src = link.href; image.alt = alt; image.loading = 'lazy';
  link.append(image); return link;
}
function topicName(id) { return topics.find(topic => topic.id === id)?.name || id; }
function pick(id, focus = false) {
  if (!filtered.some(entry => entry.q.id === id)) return;
  currentId = id;
  // A URL fragment permits sharing a review without persisting a learning attempt.
  if (location.hash !== `#${id}`) history.replaceState(null, '', `#${id}`);
  renderList(); renderQuestion();
  if (focus) {
    if (matchMedia('(max-width:760px)').matches) $('list-panel').open = false;
    $('title').focus();
  }
}
function renderList() {
  $('question-list').replaceChildren();
  $('list-heading').textContent = `問題一覧 · ${filtered.length}問`;
  const set = mockSets.find(set => set.id === $('mock-set').value);
  const numbers = new Map((set?.slots || []).map(slot => [slot.questionId,slot.number]));
  for (const {q, status} of filtered) {
    const li = node('li'), button = node('button'); button.type = 'button';
    button.setAttribute('aria-current', String(q.id === currentId));
    button.append(node('span', `${set ? `問${numbers.get(q.id)} · ` : ''}${q.title}`, 'list-title'), node('span', `${topicName(q.topicId)} · ${status === 'draft' ? '確認待ち' : '公開済み'}`, 'muted'), node('div', `${q.id} ← ${q.parentQuestionId}`, 'question-id'));
    button.addEventListener('click', () => pick(q.id, true)); li.append(button); $('question-list').append(li);
  }
}
function renderQuestion() {
  const position = filtered.findIndex(entry => entry.q.id === currentId);
  $('question-panel').hidden = position < 0; $('empty').hidden = position >= 0;
  if (position < 0) return;
  const {q, status, review, progress, batch} = filtered[position], parent = parents.get(q.parentQuestionId);
  $('position').textContent = `${position + 1} / ${filtered.length}`;
  $('previous').disabled = position === 0; $('next').disabled = position === filtered.length - 1;
  $('state').textContent = status === 'draft' ? '確認待ち' : '公開済み'; $('state').className = `badge ${status === 'draft' ? 'draft' : ''}`;
  $('draft-notice').hidden = status !== 'draft'; $('field').textContent = topicName(q.topicId);
  $('title').textContent = q.title; $('identity').textContent = `${q.id} · v${q.version}`; $('stem').textContent = q.stem || '';
  $('figures').replaceChildren();
  if (q.image) $('figures').append(imageLink(q.image, q.imageAlt || '問題の図'));
  for (const path of q.sourceImages || []) $('figures').append(imageLink(path, '問題の原本画像'));
  $('choices').replaceChildren(node('legend', '選択はこの画面内だけです'));
  for (const choice of q.choices) {
    const label = node('label', undefined, 'choice'), radio = node('input'); radio.type = 'radio'; radio.name = 'answer'; radio.value = choice.id;
    const body = node('span', undefined, 'choice-body'); if (choice.text) body.append(node('span', choice.text));
    if (choice.image) body.append(imageLink(choice.image, `${choice.label}の選択肢の図`));
    label.append(radio, node('strong', choice.label), body); $('choices').append(label);
  }
  $('result').hidden = true; $('reveal').setAttribute('aria-expanded', 'false'); $('reveal').textContent = '解答・解説を確認';
  $('adaptation').textContent = q.adaptation; $('source').textContent = q.source;
  $('original-details').open = false;
  $('original-heading').textContent = parent ? `元のIPA問題 · ${parent.packLabel} 問${parent.number}` : `元のIPA問題 · ${q.parentQuestionId}`;
  $('original-images').replaceChildren(); $('source-links').replaceChildren();
  if (parent) {
    for (const path of parent.sourceImages || []) $('original-images').append(imageLink(path, `${parent.packLabel} 問${parent.number}の原本画像`, 'original'));
    for (const source of sources.filter(source => source.year === parent.year && source.season === parent.season)) {
      const url = new URL(source.url); if (url.protocol !== 'https:') continue;
      const link = node('a', source.kind === 'question' ? 'IPA公式問題PDF' : 'IPA公式解答PDF'); link.href = url.href; link.target = '_blank'; link.rel = 'noopener'; $('source-links').append(link);
    }
  }
  $('original-answer').textContent = parent ? `公式正解：${parent.choices.find(choice => choice.id === parent.correctChoiceId)?.label || '不明'}` : '元問題が見つかりません';
  $('evidence').replaceChildren(node('p', `状態：${status === 'draft' ? '作者の自己検算まで。別実行の確認は未実施。' : '確認済みの公開教材。確認方法の実態は以下の記録を参照。'}`));
  $('evidence').append(node('p', `作成：${review?.author || batch?.author || '記録なし'}`));
  if (review) {
    $('evidence').append(node('p', `確認：${review.reviewer} · ${review.checkedAt}`), node('p', review.notes));
    if (review.method) {
      const method = review.method;
      $('evidence').append(node('p', `${method.revisionRecord ? '初版の確認' : '確認'}：別実行 ${method.separateExecution ? 'はい' : 'いいえ'} ／ 別担当 ${method.separateAgent ? 'はい' : 'いいえ'} ／ 盲検 ${method.blindContext ? 'はい' : 'いいえ'}`));
      if (method.revisionRecord) $('evidence').append(node('p', method.independentRevisionReview ? '改訂版には独立した確認記録があります。' : '改訂版の再確認は改訂担当自身による同一実行です。独立した改訂レビューではありません。'));
    }
  }
  $('evidence').append(node('p', `問題SHA-256：${review?.sha256 || progress?.draftSha256 || '記録なし'}`, 'hash'));
  const record = node('a', status === 'draft' ? '草稿のJSONを開く' : '確認記録のJSONを開く');
  record.href = new URL(status === 'draft' ? progress.draftBatchPath : 'content/ap/diagnostic-reviews.json', root).href;
  record.target = '_blank'; record.rel = 'noopener'; $('evidence').append(record);
}
function filter() {
  const text = $('search').value.trim().toLocaleLowerCase();
  const set = mockSets.find(set => set.id === $('mock-set').value);
  const positions = new Map((set?.slots || []).map(slot => [slot.questionId, slot.number]));
  filtered = entries.filter(({q, status}) => (!set || positions.has(q.id)) && (!$('topic').value || q.topicId === $('topic').value) && (!$('status').value || status === $('status').value) && (!text || [q.id, q.parentQuestionId, q.title, q.stem, topicName(q.topicId)].join(' ').toLocaleLowerCase().includes(text)));
  if (set) filtered.sort((a,b) => positions.get(a.q.id) - positions.get(b.q.id));
  $('mock-summary').hidden = !set;
  if (set) {
    const ids = new Set(set.slots.map(slot => slot.questionId));
    const complete = entries.filter(entry => entry.status === 'published' && ids.has(entry.q.id)).length;
    $('mock-summary').textContent = `${set.label} · 完成${complete} / ${set.size}問 · テクノロジ50・マネジメント10・ストラテジ20。ここでは学習記録を付けずに問題を見られます。`;
  }
  if (!filtered.some(entry => entry.q.id === currentId)) currentId = filtered[0]?.q.id || '';
  history.replaceState(null, '', `${location.pathname}${location.search}${currentId ? `#${currentId}` : ''}`);
  renderList(); renderQuestion();
}
function reveal() {
  const {q} = filtered.find(entry => entry.q.id === currentId);
  const correct = q.choices.find(choice => choice.id === q.correctChoiceId), selected = $('choices').querySelector('input:checked');
  $('answer-heading').textContent = `正解：${correct.label}${selected ? (selected.value === correct.id ? ' · 選択と一致' : ' · 選択とは異なります') : ''}`;
  $('summary').textContent = q.summary; $('explanation').textContent = q.explanation; $('takeaway').textContent = q.takeaway;
  $('reasons').replaceChildren();
  q.choices.forEach((choice, index) => {const li = node('li'); li.append(node('strong', `${choice.label}：`), node('span', q.choiceReasons[index])); $('reasons').append(li);});
  $('result').hidden = false; $('reveal').textContent = '解答・解説を閉じる'; $('reveal').setAttribute('aria-expanded', 'true');
}
$('reveal').addEventListener('click', () => {
  if ($('result').hidden) reveal();
  else {$('result').hidden = true; $('reveal').textContent = '解答・解説を確認'; $('reveal').setAttribute('aria-expanded', 'false');}
});
for (const id of ['mock-set', 'topic', 'status', 'search']) $(id).addEventListener(id === 'search' ? 'input' : 'change', filter);
for (const [id, delta] of [['previous', -1], ['next', 1]]) $(id).addEventListener('click', () => {const index = filtered.findIndex(entry => entry.q.id === currentId); if (filtered[index + delta]) pick(filtered[index + delta].q.id, true);});
window.addEventListener('hashchange', () => {
  const id = location.hash.slice(1);
  if (!entries.some(entry => entry.q.id === id)) return;
  const selected = mockSets.find(set => set.id === $('mock-set').value);
  if (selected && !selected.slots.some(slot => slot.questionId === id)) $('mock-set').value = '';
  $('topic').value = ''; $('status').value = ''; $('search').value = ''; currentId = id; filter();
});
try {
  const [qualification, progress, published, reviews, manifest, sourceList] = await Promise.all([
    read('content/ap/qualification.json'), read('content/ap/diagnostic-progress.json'), read('content/ap/diagnostic-questions.json'), read('content/ap/diagnostic-reviews.json'), read('data/qualifications/ap/manifest.json'), read('data/sources.json')
  ]);
  topics = qualification.topics; sources = sourceList;
  if (progress.mockSetsPath) {
    const collection = await read(progress.mockSetsPath);
    if (collection.format !== 'hitomon-mock-sets' || collection.version !== 1 || collection.qualificationId !== qualification.id || !Array.isArray(collection.sets)) throw new Error('模試教材の形式が不正です');
    mockSets = collection.sets;
    for (const set of mockSets) {
      if (!Array.isArray(set.slots) || set.slots.length !== set.size || new Set(set.slots.map(slot => slot.questionId)).size !== set.size) throw new Error('模試教材の出題一覧が不正です');
      const option = node('option', `${set.label}（${set.size}問）`); option.value = set.id; $('mock-set').append(option);
    }
    $('mock-filter').hidden = !mockSets.length;
  }
  const index = await read(manifest.index.url, new URL('data/qualifications/ap/manifest.json', root));
  parents = new Map(index.map(q => [q.id, q]));
  const reviewed = new Map(reviews.map(review => [review.questionId, review]));
  entries = published.map(q => ({q, status:'published', review:reviewed.get(q.id)}));
  // Historical first-round drafts were already published. Only pending ledger IDs are shown.
  const pending = new Map(progress.items.filter(item => item.status === 'awaiting-independent-review').map(item => [item.questionId, item]));
  if (pending.size) {
    const pendingItems = [...pending.values()];
    const paths = pendingItems.every(item => item.draftBatchPath) ? [...new Set(pendingItems.map(item => item.draftBatchPath))] : progress.batchPaths;
    for (const path of paths) {
      const batch = await read(path);
      for (const q of batch.questions) if (pending.has(q.id)) {entries.push({q, status:'draft', progress:pending.get(q.id), batch}); pending.delete(q.id);}
    }
    if (pending.size) throw new Error('確認待ちの草稿が見つかりません');
  }
  if (new Set(entries.map(entry => entry.q.id)).size !== entries.length) throw new Error('問題IDが重複しています');
  if (entries.filter(entry => entry.status === 'draft').length !== progress.pendingReviewCount || published.length !== progress.publishedCount) throw new Error('教材と進捗台帳の件数が一致しません');
  entries.sort((a, b) => topics.findIndex(topic => topic.id === a.q.topicId) - topics.findIndex(topic => topic.id === b.q.topicId) || a.q.id.localeCompare(b.q.id));
  $('counts').replaceChildren(node('span', `公開済み ${published.length}問`, 'badge'), node('span', `確認待ち ${progress.pendingReviewCount}問`, 'badge draft'));
  for (const topic of topics) {
    const option = node('option', topic.name); option.value = topic.id; $('topic').append(option);
    const count = status => entries.filter(entry => entry.q.topicId === topic.id && entry.status === status).length;
    $('topic-counts').append(node('p', `${topic.name}：公開${count('published')} / 待ち${count('draft')}`));
  }
  currentId = entries.some(entry => entry.q.id === location.hash.slice(1)) ? location.hash.slice(1) : entries[0]?.q.id || '';
  $('list-panel').open = !matchMedia('(max-width:760px)').matches;
  $('workspace').hidden = false; filter();
} catch (error) {
  $('counts').textContent = '読み込みに失敗しました'; $('workspace').hidden = true; $('error').textContent = `${error.message}。再読み込みしてください。`; $('error').hidden = false;
}
