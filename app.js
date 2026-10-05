const STORAGE = 'ap-study-mock.v1';
const $ = (s, root = document) => root.querySelector(s);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const now = () => new Date().toISOString();
const day = value => { const d = new Date(value); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
const dateText = value => new Date(value).toLocaleDateString('ja-JP', {month:'long', day:'numeric'});
const timeText = value => new Date(value).toLocaleString('ja-JP', {month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
const makeState = () => ({version:1, attempts:[], currentId:null, view:'home', settings:{largeText:false, sessionSize:1}, session:{goal:1, attemptIds:[]}, overrides:{}});
const complete = a => ['correct','assisted','incorrect','revealed'].includes(a.status);
const labels = {correct:'自力で正解',assisted:'ヒントで正解',incorrect:'不正解',revealed:'解答を確認',in_progress:'途中',postponed:'あとで解く'};
let base = [], state = makeState(), storageOK = true, corruptRaw = null, editId = null;
const main = $('#main');
function question(id) { const q = base.find(q => q.id === id); return q ? {...q, ...(state.overrides[id] || {})} : null; }
function current() { return state.attempts.find(a => a.id === state.currentId); }
function latest(id) { return state.attempts.filter(a => a.questionId === id && complete(a)).at(-1); }
function notice(message) { $('#notice').textContent = message; $('#notice').hidden = !message; }
function save() {
  if (corruptRaw !== null) { notice('保存データを読み取れませんでした。表示・データから書き出すか、読み込み・初期化で復旧できます。元の記録は上書きしていません。'); return false; }
  try { localStorage.setItem(STORAGE, JSON.stringify(state)); storageOK = true; $('#save-state').textContent = 'このブラウザに保存済み'; return true; }
  catch { storageOK = false; $('#save-state').textContent = '保存できていません'; notice('ブラウザに保存できません。いまの学習は続けられます。「表示・データ」から記録を書き出してください。'); return false; }
}
function badge(a) { return `<span class="badge ${a.status==='correct'?'good':a.status==='incorrect'?'wrong':complete(a)?'help':''}">${labels[a.status]}</span>`; }
function reviewInfo(q) {
  const a = latest(q.id); if (!a) return null;
  const successes = new Set(state.attempts.filter(x => x.questionId===q.id && x.status==='correct' && !x.confidence).map(x => day(x.completedAt))).size;
  const needs = a.status !== 'correct' || a.confidence;
  const days = needs ? 1 : [3,7,14][Math.min(Math.max(successes-1,0),2)];
  const due = new Date(a.completedAt); due.setHours(0,0,0,0); due.setDate(due.getDate()+days);
  return {a, successes, needs, due, isDue:day(now()) >= day(due)};
}
function reviewQuestions() { return base.map(q=>({q, info:reviewInfo(q)})).filter(x=>x.info && (x.info.needs || x.info.isDue)).sort((a,b)=>Number(b.info.isDue)-Number(a.info.isDue)||a.info.due-b.info.due); }
function pickQuestion() {
  const done = new Set(state.session.attemptIds.map(id => state.attempts.find(a=>a.id===id)?.questionId));
  const candidates = base.filter(q=>!done.has(q.id));
  const pool = candidates.length ? candidates : base;
  return pool.find(q=>reviewInfo(q)?.isDue) || pool.find(q=>!latest(q.id)) || pool.find(q=>reviewInfo(q)?.needs) || pool[0];
}
function render(focus = true, preserveY = null) {
  document.documentElement.classList.toggle('large-text', state.settings.largeText);
  $('#large-text').checked = state.settings.largeText;
  document.querySelectorAll('.nav-item').forEach(b=>{ const active = b.dataset.view === (state.view==='study'?'home':state.view); b.classList.toggle('active',active); active ? b.setAttribute('aria-current','page') : b.removeAttribute('aria-current'); });
  $('#review-count').textContent = reviewQuestions().length;
  main.innerHTML = state.view==='study' && current() ? studyHTML() : state.view==='review' ? reviewHTML() : state.view==='history' ? historyHTML() : state.view==='materials' ? materialsHTML() : homeHTML();
  if (focus) { main.focus({preventScroll:true}); window.scrollTo(0, preserveY ?? 0); }
}
function go(view) { state.view=view; save(); render(); }
function start(id, newSession = false) {
  const old = current(); if(old && !complete(old)) { old.status='postponed'; old.updatedAt=now(); }
  if(newSession) state.session={goal:state.settings.sessionSize,attemptIds:[]};
  const q = id ? question(id) : pickQuestion(); if(!q) return;
  const a={id:crypto.randomUUID(),questionId:q.id,questionVersion:q.version,contentRevision:state.overrides[q.id]?.revision || 'original',status:'in_progress',startedAt:now(),updatedAt:now(),completedAt:null,selected:null,hintCount:0,hintsBeforeAnswer:null,hintEvents:[],answerViewedBefore:false,confidence:false,scrollY:0,materialSnapshot:{hints:q.hints,summary:q.summary,explanation:q.explanation,takeaway:q.takeaway}};
  state.attempts.push(a); state.currentId=a.id; state.session.attemptIds.push(a.id); state.view='study'; save(); render();
}
function resume(id) { const old=current(); if(old && old.id!==id && !complete(old)) old.status='postponed'; const a=state.attempts.find(a=>a.id===id); if(!a) return; state.currentId=id; if(!complete(a)) a.status='in_progress'; state.view='study'; save(); render(true,a.scrollY || 0); }
function finish(status) {
  const a=current(); if(!a || complete(a)) return;
  a.status=status; a.completedAt=now(); a.updatedAt=now(); a.hintsBeforeAnswer=a.hintCount; save(); render(false);
  $('#result-heading')?.focus({preventScroll:true}); $('#result')?.scrollIntoView({block:'start'});
}
function rowHTML(q, info, action = 'start', label='解く') {
  return `<div class="row"><div><p class="row-title">${esc(q.title)}</p><p class="row-meta">令和6年 春期 · 問${q.number} · ${esc(q.topic)}</p>${info?`<div class="history-result">${badge(info.a)}<span class="small muted">解答前のヒント ${info.a.hintsBeforeAnswer}/3</span></div>`:''}</div><div class="row-actions"><button class="button secondary" data-action="${action}" data-id="${q.id}">${label}</button></div></div>`;
}
function homeHTML() {
  const paused=state.attempts.filter(a=>!complete(a)).at(-1);
  const today=state.attempts.filter(a=>complete(a)&&day(a.completedAt)===day(now()));
  const unique = new Set(state.attempts.filter(complete).map(a=>a.questionId)).size;
  const reviews = reviewQuestions();
  return `<div class="page-heading"><span class="eyebrow">YOUR OWN PACE</span><h1>まずは、1問だけ。</h1><p class="muted">ヒントを使っても、途中でやめても大丈夫。</p></div>
  ${paused?`<section class="resume-panel"><h2>途中の問題があります</h2><p>${esc(question(paused.questionId).title)} · ヒント ${paused.hintCount}/3 · ${paused.selected===null?'未選択':'選択済み'}</p><button class="button primary" data-action="resume" data-id="${paused.id}">続きから解く</button></section>`:''}
  <section class="panel start-panel"><div><span class="eyebrow">SMALL START</span><h2 class="start-title">短く始めて、ひと区切り。</h2><p class="muted">1問ずつ、自分のペースで進めよう。<br>時間制限はありません。</p></div><div class="session-number">${state.settings.sessionSize}<small>問から</small></div><div class="start-actions"><button class="button light" data-action="start-session">${paused?'別の問題を始める':'学習を始める'}</button><label><span class="sr-only">今回の目安</span><select id="session-size" class="session-choice" aria-label="今回の目安">${[1,3,5].map(n=>`<option value="${n}" ${state.settings.sessionSize===n?'selected':''}>${n}問でひと区切り</option>`).join('')}</select></label></div></section>
  <div class="stats"><div class="stat"><span class="stat-value">${today.length}<small> 回</small></span><span class="stat-label">今日の解答</span></div><div class="stat"><span class="stat-value">${unique}<small> / ${base.length}</small></span><span class="stat-label">解いた問題</span></div><div class="stat"><span class="stat-value">${reviews.length}<small> 問</small></span><span class="stat-label">解き直し候補</span></div></div>
  <section class="panel"><div class="heading-row"><h2>もう一度、考えてみよう</h2><button class="button quiet" data-view="review">一覧へ →</button></div>${reviews.length?reviews.slice(0,2).map(({q,info})=>rowHTML(q,info,'start','解き直す')).join(''):`<div class="empty"><p>解き直す問題は、学習するとここに並びます。</p><span class="small">不正解・ヒント利用・自信がない問題を集めます。</span></div>`}</section><p class="page-note">記録はこのブラウザに保存します。「表示・データ」からバックアップできます。</p>`;
}
function studyHTML() {
  const a=current(); const original=question(a.questionId); const q={...original,...a.materialSnapshot}; const answered=complete(a);
  const count=state.session.attemptIds.filter(id=>complete(state.attempts.find(a=>a.id===id) || {})).length;
  return `<div class="study-toolbar"><button class="button quiet" data-action="pause">← ${answered?'学習ホームへ':'中断してホームへ'}</button><p class="page-note">今回 ${count}問 · 目安 ${state.session.goal}問 <span class="muted">· いつでも終了OK</span></p></div><article class="panel question-panel"><div class="study-stage"><span class="${!answered?'current':''}">01 考える</span><span class="${answered?'current':''}">02 解説を読む</span></div><div class="question-meta"><span class="badge">${esc(q.topic)}</span><span>令和6年 春期 · 問${q.number}</span></div><h1>${esc(q.title)}</h1><p class="question-stem">${esc(q.stem)}</p>
  ${q.image?`<figure class="question-figure"><a class="figure-link" href="${q.image}" target="_blank" rel="noopener"><img src="${q.image}" alt="${esc(q.imageAlt)}"></a><figcaption>図を押すと、大きく開けます。</figcaption></figure>`:''}
  <fieldset class="choices"><legend>${answered?'選択と正解':'答えを1つ選んでください'}</legend>${q.choices.map((c,i)=>`<label class="choice ${a.selected===i?'selected':''} ${answered&&q.answer===i?'correct-choice':''} ${answered&&a.selected===i&&q.answer!==i?'wrong-choice':''}"><input type="radio" name="answer" value="${i}" ${a.selected===i?'checked':''} ${answered?'disabled':''}><span class="choice-code">${c.label}</span><span class="choice-text">${c.image?`<img src="${c.image}" alt="${esc(c.text)}">`:''}${esc(c.text)}${answered&&q.answer===i?' <strong>（正解）</strong>':''}${answered&&a.selected===i?' <span class="small">（あなたの選択）</span>':''}</span></label>`).join('')}</fieldset>
  ${!answered?`<label class="confidence"><input id="confidence" type="checkbox" ${a.confidence?'checked':''}>自信がないので、正解でも解き直したい</label>`:''}
  <section class="hint-section" aria-label="段階的なヒント"><div class="hint-head"><h3>行き詰まったら、ヒント。</h3><span class="hint-count">${a.hintCount} / ${q.hints.length}</span></div><div id="hints" aria-live="polite">${q.hints.slice(0,a.hintCount).map((h,i)=>`<div class="hint-box" tabindex="-1"><h4>${i+1}. ${esc(h.title)}${h.revealsAnswer?'（答えを含む）':''}</h4><p>${esc(h.text)}</p></div>`).join('')}</div>${a.hintCount<q.hints.length?`<button class="button secondary" style="margin-top:14px" data-action="hint">${a.hintCount?'次のヒントを見る':'ヒントを1つ見る'}</button>`:`<p class="page-note" style="margin-top:12px">ヒントはここまで。自分の言葉で考えてみよう。</p>`}${answered?'<p class="page-note" style="margin-top:10px">解答後のヒント閲覧は、解答前の記録に加えません。</p>':''}</section>
  ${answered?resultHTML(q,a):`<div class="answer-actions"><button class="button primary" data-action="submit" ${a.selected===null?'disabled':''}>この答えで確認する</button><button class="button quiet" data-action="reveal">解答を見て学ぶ</button></div><button class="button quiet" style="margin-top:8px" data-action="postpone">この問題はあとで解く</button>`}
  <details class="source-details"><summary>問題の出典と教材について</summary><p>出典：${esc(q.source)}</p><p>${esc(q.adaptation)} ヒント・解説は独自作成で、IPAの公式解説ではありません。</p><div class="link-list"><a href="https://www.ipa.go.jp/shiken/mondai-kaiotu/m42obm000000afqx-att/2024r06h_ap_am_qs.pdf#page=${q.page}" target="_blank" rel="noopener">公式問題PDF</a><a href="https://www.ipa.go.jp/shiken/mondai-kaiotu/m42obm000000afqx-att/2024r06h_ap_am_ans.pdf" target="_blank" rel="noopener">公式解答PDF</a></div></details></article>`;
}
function resultHTML(q,a) {
  const info=reviewInfo(q); const count=state.session.attemptIds.filter(id=>complete(state.attempts.find(a=>a.id===id)||{})).length;
  return `<section class="result" id="result" aria-label="解答と解説"><span class="eyebrow">FEEDBACK</span><h2 id="result-heading" tabindex="-1">${labels[a.status]}${a.status==='incorrect'?'。ここから覚えよう。':'。ひと区切り！'}</h2><p><strong>正解：${q.choices[q.answer].label}</strong> <span class="small muted">· 解答前のヒント ${a.hintsBeforeAnswer}/3${a.confidence?' · 自信なし':''}</span></p><p class="explanation">${esc(q.summary)}</p>${a.selected!==null&&a.selected!==q.answer?`<p class="explanation"><strong>選んだ${q.choices[a.selected].label}は？</strong><br>${esc(q.choiceReasons[a.selected])}</p>`:''}<details ${a.status==='incorrect'||a.status==='revealed'?'open':''}><summary>解き方を順番に読む</summary><p class="explanation">${esc(q.explanation)}</p></details><details><summary>ほかの選択肢も確認する</summary><ul class="reason-list">${q.choiceReasons.map((r,i)=>`<li><b>${q.choices[i].label}</b>${esc(r)}</li>`).join('')}</ul></details><p class="takeaway"><strong>次に使える考え方</strong>${esc(q.takeaway)}</p><p class="review-date">次の復習目安：${dateText(info.due)}<br><span class="small">${info.needs?'明日、ヒントなしで思い出してみよう。':'自信あり・ヒントなしの正解は、別の日に'+info.successes+'回。'} 日付はこのアプリの目安です。</span></p>${q.related.length?`<details><summary>同じ考え方を使う問題</summary>${q.related.map(id=>`<button class="button secondary" style="margin-top:8px" data-action="start" data-id="${id}">${esc(question(id).title)} →</button>`).join('')}</details>`:''}</section><div class="finish-actions"><button class="button secondary" data-action="end">${count>=state.session.goal?'今日のひと区切りを終える':'ここで終える'}</button><button class="button primary" data-action="next">${count>=state.session.goal?'もう1問やる':'次の問題へ'}</button></div>`;
}
function reviewHTML() {
  const list=reviewQuestions(); const paused=state.attempts.filter(a=>!complete(a));
  return `<div class="page-heading"><span class="eyebrow">RECALL & RETRY</span><h1>思い出して、もう一度。</h1><p class="muted">不正解・ヒント利用・自信なし・復習日が来た問題。</p></div><section class="panel"><h2>解き直し候補 <span class="badge">${list.length}問</span></h2>${list.length?list.map(({q,info})=>`<div><p class="page-note" style="margin-top:18px">${info.isDue?'復習日が来ています':'復習目安：'+dateText(info.due)+' · 今すぐ解いてもOK'}</p>${rowHTML(q,info,'start','解き直す')}</div>`).join(''):'<div class="empty"><p>いまは候補がありません。</p><p class="small">まず1問解いてみよう。間違えた問題も、ヒントで解けた問題も、ここに残ります。</p><button class="button primary" data-action="start-session">学習を始める</button></div>'}</section>${paused.length?`<section class="panel"><h2>あとで解く・途中の問題</h2><p class="page-note">未解答は、不正解として数えません。</p>${paused.slice().reverse().map(a=>`<div class="row"><div><p class="row-title">${esc(question(a.questionId).title)}</p><p class="row-meta">${timeText(a.updatedAt)} · ヒント ${a.hintCount}/3</p></div><button class="button secondary" data-action="resume" data-id="${a.id}">続きから</button></div>`).join('')}</section>`:''}<p class="page-note">復習目安は、要復習なら翌日。自信ありの自力正解は、別の日に正解した回数に応じて3・7・14日後です。</p>`;
}
function historyHTML() {
  return `<div class="page-heading"><span class="eyebrow">YOUR LEARNING LOG</span><h1>解いた道筋が、残ります。</h1><p class="muted">正誤だけでなく、どこまでヒントを見たかも記録。</p></div><section class="panel"><h2>学習の記録 <span class="badge">${state.attempts.length}回</span></h2>${state.attempts.length?state.attempts.slice().reverse().map(a=>`<div class="row"><div><p class="row-title">${esc(question(a.questionId).title)} <span class="small muted">· 問${question(a.questionId).number}</span></p><p class="row-meta">${timeText(a.completedAt||a.updatedAt)}${a.contentRevision!=='original'?' · 編集した教材':''}</p><div class="history-result">${badge(a)} <span class="small muted">${complete(a)?'解答前の':''}ヒント ${a.hintsBeforeAnswer??a.hintCount}/3${a.confidence?' · 自信なし':''}</span></div>${complete(a)&&a.hintCount>a.hintsBeforeAnswer?`<p class="row-meta">解答後にヒント ${a.hintCount-a.hintsBeforeAnswer}つを追加閲覧</p>`:''}</div><div class="row-actions"><button class="button secondary" data-action="resume" data-id="${a.id}">${complete(a)?'解説を見る':'続きから'}</button>${complete(a)?`<button class="button quiet" data-action="start" data-id="${a.questionId}">解き直す</button>`:''}</div></div>`).join(''):'<div class="empty"><p>まだ学習記録はありません。</p><button class="button primary" data-action="start-session">まず1問、始める</button></div>'}</section><p class="page-note">「自力で正解」は、解答前のヒント利用も答えの閲覧もなかった記録です。習得を保証する判定ではありません。</p>`;
}
function materialsHTML() {
  return `<div class="page-heading"><span class="eyebrow">QUESTION LIBRARY</span><h1>小さな問題集から始めよう。</h1><p class="muted">令和6年度 春期 午前の5問。図を使う問題もあります。</p></div><section class="panel"><h2>問題と教材 <span class="badge">${base.length}問</span></h2><p class="material-intro">IPA公式問題を転記し、3段階のヒントと解説を独自に用意しました。問題文・正解は公式資料と照合済みです。</p>${base.map(q=>`<div class="row"><div><p class="row-title">${esc(q.title)}</p><p class="row-meta">問${q.number} · ${esc(q.topic)} · ${state.overrides[q.id]?'編集した教材':'初期教材'}</p></div><div class="row-actions"><button class="button quiet" data-action="edit" data-id="${q.id}">教材を編集</button><button class="button secondary" data-action="start" data-id="${q.id}">解く</button></div></div>`).join('')}</section><section class="panel"><h2>問題を増やすには</h2><p class="material-intro">このモックでは、問題集はリポジトリの <code>data/questions.json</code> で管理します。編集したヒント・解説も含めて書き出せます。</p><button class="button secondary" data-action="export-materials">教材を書き出す</button><details><summary>教材の出典と編集範囲</summary><p>問題出典：IPA 令和6年度 春期 応用情報技術者試験 午前 問1・10・21・36・37。過去問道場の解説や問題データは転載していません。</p><p>この画面で編集できるのは、自作のヒント・要約・解説・覚え方です。問題文や正解の変更はリポジトリで行います。学習済みの記録には当時の教材を残します。</p><a href="docs/SOURCES.md">詳しい出典と利用条件</a></details></section>`;
}
function download(data,name,raw=false) { const url=URL.createObjectURL(new Blob([raw?data:JSON.stringify(data,null,2)],{type:'application/json'})); const a=document.createElement('a'); a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000); }
function openEditor(id) {
  editId=id; const q=question(id); $('#editor-title').textContent=`${q.title}：教材を編集`;
  $('#editor-fields').innerHTML=q.hints.map((h,i)=>`<label class="editor-field"><span>ヒント${i+1}：${esc(h.title)}</span><textarea name="hint${i}" required maxlength="10000" rows="3">${esc(h.text)}</textarea></label><label class="confidence"><input type="checkbox" name="reveal${i}" ${h.revealsAnswer?'checked':''}>このヒントは答えを含む</label>`).join('')+[['summary','ひとことで'],['explanation','順番に読む解説'],['takeaway','次に使える考え方']].map(([key,label])=>`<label class="editor-field"><span>${label}</span><textarea name="${key}" required maxlength="20000" rows="${key==='explanation'?6:3}">${esc(q[key])}</textarea></label>`).join('');
  $('#editor-dialog').showModal();
}
function validText(v,max=20000) { return typeof v==='string' && v.length<=max; }
function validateState(s) {
  const fail=()=>{throw new Error('このアプリの有効な学習記録ファイルではありません。現在の記録は変更していません。');};
  const validDate=v=>typeof v==='string'&&!Number.isNaN(new Date(v).valueOf());
  const validHints=h=>Array.isArray(h)&&h.length===3&&h.every(x=>x&&validText(x.title,100)&&validText(x.text,10000)&&typeof x.revealsAnswer==='boolean');
  const validMaterial=m=>m&&Object.keys(m).every(k=>['hints','summary','explanation','takeaway','revision'].includes(k))&&validHints(m.hints)&&['summary','explanation','takeaway'].every(k=>validText(m[k]));
  if(!s||s.version!==1||!Array.isArray(s.attempts)||s.attempts.length>20000||!['home','study','review','history','materials'].includes(s.view)||!s.settings||typeof s.settings.largeText!=='boolean'||![1,3,5].includes(s.settings.sessionSize)||!s.session||![1,3,5].includes(s.session.goal)||!Array.isArray(s.session.attemptIds)||!s.overrides||Array.isArray(s.overrides)||typeof s.overrides!=='object') fail();
  const ids=new Set();
  for(const a of s.attempts) {
    if(!a||!validText(a.id,100)||!/^[a-zA-Z0-9-]+$/.test(a.id)||ids.has(a.id)||!base.some(q=>q.id===a.questionId)||!Object.hasOwn(labels,a.status)||!validDate(a.startedAt)||!validDate(a.updatedAt)||!(a.selected===null||Number.isInteger(a.selected)&&a.selected>=0&&a.selected<4)||!Number.isInteger(a.hintCount)||a.hintCount<0||a.hintCount>3||typeof a.confidence!=='boolean'||typeof a.answerViewedBefore!=='boolean'||!Number.isFinite(a.scrollY)||a.scrollY<0||!validText(a.contentRevision,100)||!Number.isInteger(a.questionVersion)||!validMaterial(a.materialSnapshot)) fail();
    if(complete(a)?!validDate(a.completedAt)||!Number.isInteger(a.hintsBeforeAnswer)||a.hintsBeforeAnswer<0||a.hintsBeforeAnswer>a.hintCount:a.completedAt!==null||a.hintsBeforeAnswer!==null) fail();
    if(!Array.isArray(a.hintEvents)||a.hintEvents.length!==a.hintCount||a.hintEvents.some((e,i)=>!e||e.step!==i+1||!validDate(e.at)||!['before','after'].includes(e.phase))) fail();
    const q=base.find(q=>q.id===a.questionId);
    if(a.status==='correct'&&(a.selected!==q.answer||a.hintsBeforeAnswer!==0||a.answerViewedBefore)||a.status==='assisted'&&(a.selected!==q.answer||a.hintsBeforeAnswer===0||a.answerViewedBefore)||a.status==='incorrect'&&(a.selected===null||a.selected===q.answer)||a.status==='revealed'&&!a.answerViewedBefore) fail();
    ids.add(a.id);
  }
  if(s.currentId!==null&&!ids.has(s.currentId)||s.session.attemptIds.some(id=>!ids.has(id))||new Set(s.session.attemptIds).size!==s.session.attemptIds.length) fail();
  for(const [id,m] of Object.entries(s.overrides)) if(!base.some(q=>q.id===id)||!validMaterial(m)||!validText(m.revision,100)||Object.keys(m).some(k=>!['hints','summary','explanation','takeaway','revision'].includes(k))) fail();
  return s;
}
main.addEventListener('click',e=>{
  const el=e.target.closest('[data-action],[data-view]'); if(!el) return;
  if(el.dataset.view) { go(el.dataset.view); return; }
  const action=el.dataset.action; const a=current();
  if(action==='start-session') start(null,true);
  else if(action==='start') start(el.dataset.id);
  else if(action==='resume') resume(el.dataset.id);
  else if(action==='next') start();
  else if(['pause','postpone','end'].includes(action)) { if(a&&!complete(a)) {a.status='postponed';a.updatedAt=now();} state.currentId=null;go('home'); }
  else if(action==='hint'&&a) {
    const q=a.materialSnapshot; if(a.hintCount>=q.hints.length) return;
    const phase=complete(a)?'after':'before'; a.hintCount++;a.hintEvents.push({step:a.hintCount,at:now(),phase});a.updatedAt=now();
    if(phase==='before'&&q.hints[a.hintCount-1].revealsAnswer) a.answerViewedBefore=true;
    const y=window.scrollY;save();render(false);window.scrollTo(0,y); const shown=document.querySelectorAll('.hint-box');shown[shown.length-1]?.focus({preventScroll:true});
  }
  else if(action==='submit'&&a&&!complete(a)&&a.selected!==null) { const correct=a.selected===question(a.questionId).answer; finish(a.answerViewedBefore?'revealed':correct?(a.hintCount?'assisted':'correct'):'incorrect'); }
  else if(action==='reveal'&&a&&!complete(a)) { a.answerViewedBefore=true;finish('revealed'); }
  else if(action==='edit') openEditor(el.dataset.id);
  else if(action==='export-materials') download(base.map(q=>question(q.id)),'ap-study-questions.json');
});
document.querySelectorAll('header [data-view], .sidebar [data-view]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();go(b.dataset.view);}));
main.addEventListener('change',e=>{
  if(e.target.id==='session-size') { state.settings.sessionSize=Number(e.target.value);save();render(false);return; }
  const a=current();if(!a||complete(a))return;
  if(e.target.name==='answer') {a.selected=Number(e.target.value);document.querySelectorAll('.choice').forEach(l=>l.classList.toggle('selected',$('input',l).checked)); $('[data-action="submit"]').disabled=false;}
  else if(e.target.id==='confidence') a.confidence=e.target.checked;
  a.updatedAt=now();save();
});
$('#settings-button').addEventListener('click',()=>$('#settings-dialog').showModal());
$('#large-text').addEventListener('change',e=>{state.settings.largeText=e.target.checked;save();render(false);});
$('#export-state').addEventListener('click',()=>download(corruptRaw??state,`ap-study-record-${day(now())}.json`,corruptRaw!==null));
$('#import-state').addEventListener('change',async e=>{
  const file=e.target.files[0];if(!file)return;
  try { if(file.size>8*1024*1024) throw new Error('ファイルが大きすぎます。8MB以下の学習記録を選んでください。'); const candidate=validateState(JSON.parse(await file.text()));
    if((state.attempts.length||corruptRaw!==null)&&!confirm('いまの学習記録と教材編集を、ファイルの内容で置き換えます。先に書き出しておくと安心です。読み込みますか？'))return;
    corruptRaw=null;state=candidate;notice('');save();render();$('#settings-status').textContent=storageOK?'学習記録を読み込みました。':'読み込みましたが、ブラウザに保存できていません。書き出して保管してください。';
  } catch(error) { $('#settings-status').textContent=error instanceof SyntaxError?'JSONを読み取れませんでした。現在の記録は変更していません。':error.message; }
  finally {e.target.value='';}
});
$('#clear-state').addEventListener('click',()=>{if(!confirm('このブラウザの学習記録を削除します。問題と教材の編集は残します。よろしいですか？'))return;const {settings,overrides}=state;corruptRaw=null;state={...makeState(),settings,overrides};notice('');save();render();$('#settings-status').textContent=storageOK?'学習記録を削除しました。':'記録を初期化しましたが、保存に失敗しました。ブラウザの保存設定を確認してください。';});
$('#close-editor').addEventListener('click',()=>$('#editor-dialog').close());
$('#editor-form').addEventListener('submit',e=>{e.preventDefault();const f=new FormData(e.target);const q=question(editId);const changes={hints:q.hints.map((h,i)=>({...h,text:String(f.get(`hint${i}`)).trim(),revealsAnswer:f.has(`reveal${i}`)})),revision:now()};for(const k of ['summary','explanation','takeaway'])changes[k]=String(f.get(k)).trim();if(changes.hints.some(h=>!h.text)||['summary','explanation','takeaway'].some(k=>!changes[k])){alert('空欄を埋めてから保存してください。');return;}state.overrides[editId]=changes;save();$('#editor-dialog').close();render(false);});
$('#reset-material').addEventListener('click',()=>{if(!confirm('この問題のヒントと解説を、初期教材に戻しますか？'))return;delete state.overrides[editId];save();$('#editor-dialog').close();render(false);});
let scrollTimer;
window.addEventListener('scroll',()=>{if(state.view!=='study')return;clearTimeout(scrollTimer);scrollTimer=setTimeout(()=>{const a=current();if(a){a.scrollY=window.scrollY;save();}},200);},{passive:true});
function saveScroll(){if(state.view==='study'&&current()){current().scrollY=window.scrollY;save();}}
window.addEventListener('pagehide',saveScroll);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveScroll();});
try {
  const response=await fetch('data/questions.json');if(!response.ok)throw new Error('問題データを読み込めませんでした。');base=await response.json();
  try { const raw=localStorage.getItem(STORAGE);if(raw){try{state=validateState(JSON.parse(raw));}catch{corruptRaw=raw;}} } catch {storageOK=false;notice('このブラウザでは記録を保存できません。学習後に記録を書き出してください。');}
  if(state.view==='study'&&!current())state.view='home'; render(true,state.view==='study'?current()?.scrollY:0);
  if(corruptRaw!==null)save();else if(!storageOK)$('#save-state').textContent='保存できていません';
  if(navigator.modelContext?.registerTool) {
    navigator.modelContext.registerTool({name:'get_study_summary',description:'Read counts of local study attempts and review candidates. Does not modify study records.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:async()=>({content:[{type:'text',text:JSON.stringify({totalAttempts:state.attempts.length,completed:state.attempts.filter(complete).length,reviewCandidates:reviewQuestions().map(({q})=>({id:q.id,title:q.title})),storageSaved:storageOK&&corruptRaw===null})}]})});
  }
} catch(error) { main.innerHTML='<div class="empty"><h1>問題を読み込めませんでした。</h1><p>接続を確認し、このページを再読み込みしてください。</p><button class="button primary" id="reload">再読み込み</button></div>';$('#reload').addEventListener('click',()=>location.reload());console.error(error); }
