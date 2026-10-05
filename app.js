const STORAGE = 'ap-study-mock.v1';
const $ = (s, root = document) => root.querySelector(s);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const now = () => new Date().toISOString();
const day = value => { const d = new Date(value); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
const dateText = value => new Date(value).toLocaleDateString('ja-JP', {month:'long', day:'numeric'});
const timeText = value => new Date(value).toLocaleString('ja-JP', {month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
const makeState = () => ({version:1, attempts:[], currentId:null, view:'home', settings:{largeText:false, sessionSize:1}, session:{goal:1, attemptIds:[], topic:null}, readingNotes:{}, overrides:{}});
const complete = a => ['correct','assisted','incorrect','revealed'].includes(a.status);
const labels = {correct:'自力で正解',assisted:'ヒントで正解',incorrect:'不正解',revealed:'解答を確認',in_progress:'途中',postponed:'あとで解く'};
let base = [], state = makeState(), storageOK = true, corruptRaw = null, editId = null;
const main = $('#main');
function question(id) { const q = base.find(q => q.id === id); return q ? {...q, ...(state.overrides[id] || {})} : null; }
function current() { return state.attempts.find(a => a.id === state.currentId); }
function latest(id) { return state.attempts.reduce((last,a) => a.questionId===id && complete(a) && (!last || new Date(a.completedAt)>=new Date(last.completedAt)) ? a : last, null); }
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
function topics() { return [...new Set(base.map(q => q.topic))]; }
function topicPool(topic) { return topic ? base.filter(q => q.topic === topic) : base; }
function sessionCount() { return state.session.attemptIds.filter(id => complete(state.attempts.find(a => a.id === id) || {})).length; }
function hasFreshTopicQuestion() { return topicPool(state.session.topic).some(q => !state.session.attemptIds.some(id => state.attempts.find(a => a.id === id)?.questionId === q.id)); }
function pickQuestion() {
  const scoped = topicPool(state.session.topic);
  const done = new Set();
  for(const id of state.session.attemptIds) {const qid=state.attempts.find(a=>a.id===id)?.questionId;if(scoped.some(q=>q.id===qid))done.add(qid);if(done.size===scoped.length)done.clear();}
  const candidates = scoped.filter(q=>!done.has(q.id));
  const pool = candidates.length ? candidates : scoped;
  return pool.find(q=>reviewInfo(q)?.isDue) || pool.find(q=>!latest(q.id)) || pool.find(q=>reviewInfo(q)?.needs) || pool[0];
}
function render(focus = true, preserveY = null) {
  document.documentElement.classList.toggle('large-text', state.settings.largeText);
  $('#large-text').checked = state.settings.largeText;
  document.querySelectorAll('.nav-item').forEach(b=>{ const active = b.dataset.view === (state.view==='study'?(state.session.topic?'topics':'home'):state.view); b.classList.toggle('active',active); active ? b.setAttribute('aria-current','page') : b.removeAttribute('aria-current'); });
  $('#review-count').textContent = reviewQuestions().length;
  main.innerHTML = state.view==='study' && current() ? studyHTML() : state.view==='topics' ? topicsHTML() : state.view==='review' ? reviewHTML() : state.view==='history' ? historyHTML() : state.view==='materials' ? materialsHTML() : homeHTML();
  if (focus) { main.focus({preventScroll:true}); window.scrollTo(0, preserveY ?? 0); }
}
function go(view) { state.view=view; save(); render(); }
function start(id, newSession = false, options = {}) {
  const old = current(); if(old && !complete(old)) { old.status='postponed'; old.updatedAt=now(); }
  if(newSession) state.session={goal:options.goal || state.settings.sessionSize,attemptIds:[],topic:options.topic || null};
  if(id && state.session.topic && !topicPool(state.session.topic).some(q=>q.id===id)) state.session={goal:1,attemptIds:[],topic:null};
  const q = id ? question(id) : pickQuestion(); if(!q) return;
  const a={id:crypto.randomUUID(),questionId:q.id,questionVersion:q.version,contentRevision:state.overrides[q.id]?.revision || 'original',topic:state.session.topic,readingNote:state.session.topic?(state.readingNotes[state.session.topic] || ''):'',status:'in_progress',startedAt:now(),updatedAt:now(),completedAt:null,selected:null,hintCount:0,hintsBeforeAnswer:null,hintEvents:[],answerViewedBefore:false,confidence:false,scrollY:0,materialSnapshot:{hints:q.hints,summary:q.summary,explanation:q.explanation,takeaway:q.takeaway}};
  state.attempts.push(a); state.currentId=a.id; state.session.attemptIds.push(a.id); state.view='study'; save(); render();
}
function resume(id) { const old=current(); if(old && old.id!==id && !complete(old)) old.status='postponed'; const a=state.attempts.find(a=>a.id===id); if(!a) return; state.currentId=id; if(!state.session.attemptIds.includes(id) || state.session.topic!==(a.topic || null)) state.session={goal:1,attemptIds:[id],topic:a.topic || null}; if(!complete(a)) a.status='in_progress'; state.view='study'; save(); render(true,a.scrollY || 0); }
function finish(status) {
  const a=current(); if(!a || complete(a)) return;
  a.status=status; priorCacheLength=-1; a.completedAt=now(); a.updatedAt=now(); a.hintsBeforeAnswer=a.hintCount; save(); render(false);
  $('#result-heading')?.focus({preventScroll:true}); $('#result')?.scrollIntoView({block:'start'});
}
function rowHTML(q, info, action = 'start', label='解く') {
  return `<div class="row"><div><p class="row-title">${esc(q.title)}</p><p class="row-meta">令和6年 春期 · 問${q.number} · ${esc(q.topic)}</p>${info?`<div class="history-result">${badge(info.a)}<span class="small muted">解答前のヒント ${info.a.hintsBeforeAnswer}/3</span></div>`:''}</div><div class="row-actions"><button class="button secondary" data-action="${action}" data-id="${q.id}">${label}</button></div></div>`;
}
function homeHTML() {
  const paused=state.attempts.filter(a=>!complete(a)).at(-1);
  const reviews = reviewQuestions();
  return `<div class="page-heading"><span class="eyebrow">YOUR OWN PACE</span><h1>まずは、1問だけ。</h1><p class="muted">ヒントを使っても、途中でやめても大丈夫。</p></div>
  ${paused?`<section class="resume-panel"><h2>途中の問題があります</h2><p>${esc(question(paused.questionId).title)} · ヒント ${paused.hintCount}/3 · ${paused.selected===null?'未選択':'選択済み'}</p><button class="button primary" data-action="resume" data-id="${paused.id}">続きから解く</button></section>`:''}
  <section class="panel start-panel quick-start-panel"><div><span class="eyebrow">SMALL START</span><h2 class="start-title">今日は、どれくらいやろう？</h2><p class="muted">押すだけで始まります。途中で終えても大丈夫。</p></div><div class="quick-start" aria-label="問題数を選んで開始">${[1,3,5].map(n=>`<button class="session-button ${n===1?'recommended':''}" data-action="start-session" data-count="${n}"><span>${n}<small>問</small></span><small>${n===1?'まずひとつ':n===3?'少し進める':'まとまって解く'}</small></button>`).join('')}</div></section>
  <section class="panel learn-entry"><div><span class="eyebrow">READ → PRACTICE</span><h2>教科書の続きは、同じ分野の問題で。</h2><p class="muted">手元の教科書で読んだ分野を選んで、過去問を解こう。</p></div><button class="button secondary" data-view="topics">分野を選んで解く →</button></section>
  ${motivationHTML()}
  <section class="panel"><div class="heading-row"><h2>もう一度、考えてみよう</h2><button class="button quiet" data-view="review">一覧へ →</button></div>${reviews.length?reviews.slice(0,2).map(({q,info})=>rowHTML(q,info,'start','解き直す')).join(''):`<div class="empty"><p>解き直す問題は、学習するとここに並びます。</p><span class="small">不正解・ヒント利用・自信がない問題を集めます。</span></div>`}</section><p class="page-note">記録はこのブラウザに保存します。「表示・データ」からバックアップできます。</p>`;
}
function topicsHTML() {
  return `<div class="page-heading"><span class="eyebrow">TEXTBOOK → PRACTICE</span><h1>読んだ分野を、そのまま解く。</h1><p class="muted">手元の教科書で学んだ範囲を選んでください。</p></div><div class="topic-grid">${topics().map(topic=>{
    const pool=topicPool(topic);
    const attempts=state.attempts.filter(a=>complete(a)&&pool.some(q=>q.id===a.questionId));
    const tried=new Set(attempts.map(a=>a.questionId)).size;
    const counts=[...new Set([1,Math.min(3,pool.length),Math.min(5,pool.length)])];
    return `<section class="panel topic-card"><div class="heading-row"><h2>${esc(topic)}</h2><span class="badge">${pool.length}問</span></div><p class="topic-description">${[...new Set(pool.map(q=>q.concept))].map(esc).join(' / ')}</p><p class="page-note">取り組んだ問題 ${tried} / ${pool.length}問</p><details class="reading-note"><summary>読んだ章・ページをメモする（任意）</summary><label class="editor-field"><span>教科書の範囲</span><input type="text" maxlength="200" data-reading-topic="${esc(topic)}" aria-label="${esc(topic)}で読んだ範囲" placeholder="例：第3章、p.40〜48" value="${esc(state.readingNotes[topic] || '')}"></label><p class="small muted">あとから学習の記録で確認できます。</p></details><div class="button-row topic-actions">${counts.map(n=>`<button class="button ${n===1?'primary':'secondary'}" data-action="topic-session" data-topic="${esc(topic)}" data-count="${n}">${n===1?'この分野を1問':n===pool.length?'全'+n+'問を解く':n+'問を解く'}</button>`).join('')}</div></section>`;
  }).join('')}</div><p class="page-note">このモックは全5問・4分野です。選んだ分野以外の問題は出しません。分野内を一巡したら、同じ問題の解き直しになります。</p>`;
}
let priorCacheSource=null, priorCacheLength=-1, priorCache=new Map();
function previousAttempt(a) {
  if(priorCacheSource!==state.attempts || priorCacheLength!==state.attempts.length) {
    priorCacheSource=state.attempts;priorCacheLength=state.attempts.length;priorCache=new Map();const latestByQuestion=new Map();
    for(const x of state.attempts.filter(complete).sort((a,b)=>new Date(a.completedAt)-new Date(b.completedAt))) {priorCache.set(x.id,latestByQuestion.get(x.questionId));latestByQuestion.set(x.questionId,x);}
  }
  return priorCache.get(a.id);
}
function improvement(a) {
  const previous=previousAttempt(a);if(!previous)return null;
  if(a.status==='correct'&&!a.confidence&&previous.status!=='correct') {
    return previous.status==='incorrect'?'前回の不正解から、今回はヒントなしで正解できました。':`前回は${previous.status==='revealed'?'解答を確認':`ヒントを${previous.hintsBeforeAnswer}つ利用`}。今回はヒントなしで正解できました。`;
  }
  if(['correct','assisted'].includes(a.status)&&['correct','assisted'].includes(previous.status)&&a.hintsBeforeAnswer<previous.hintsBeforeAnswer) return `前回のヒント${previous.hintsBeforeAnswer}つ → 今回${a.hintsBeforeAnswer}つ。少ない手がかりで正解できました。`;
  return null;
}
function progressFeedbackHTML(a) { const message=improvement(a);return message?`<p class="progress-feedback"><strong>前回からの一歩</strong>${esc(message)}</p>`:''; }
function sessionMilestoneHTML() {
  if(!state.session.attemptIds.includes(state.currentId)||sessionCount()<state.session.goal)return '';
  return `<div class="session-milestone" role="status"><span class="milestone-icon" aria-hidden="true">✓</span><div><strong>今回の目安、達成！</strong><p>${state.session.goal}問に取り組みました。ここで終えても、もう1問進んでもOK。</p></div></div>`;
}
function achievements() {
  const done=state.attempts.filter(complete);
  const unique=new Set(done.map(a=>a.questionId)).size;
  const days=new Set(done.map(a=>day(a.completedAt))).size;
  const recovered=done.some(a=>a.status==='correct'&&!a.confidence&&previousAttempt(a)?.status==='incorrect');
  return [
    {title:'最初の一歩',detail:'1問に取り組む',earned:done.length>=1},
    {title:'問題を広げた',detail:'違う3問に取り組む',earned:unique>=3},
    {title:'解き直して正解',detail:'不正解の問題を、ヒントなしで正解',earned:recovered},
    {title:'別の日にも一歩',detail:'2日以上、問題に取り組む',earned:days>=2}
  ];
}
function motivationHTML() {
  const done=state.attempts.filter(complete);
  const today=done.filter(a=>day(a.completedAt)===day(now()));
  const unique=new Set(done.map(a=>a.questionId)).size;
  const awards=achievements();
  const earned=awards.filter(a=>a.earned);
  const next=awards.find(a=>!a.earned);
  const recent=done.slice().reverse().find(a=>improvement(a));
  const dates=Array.from({length:7},(_,i)=>{const d=new Date();d.setHours(12,0,0,0);d.setDate(d.getDate()-6+i);return d;});
  const active=dates.filter(d=>done.some(a=>day(a.completedAt)===day(d))).length;
  return `<section class="panel motivation-panel"><div class="heading-row"><div><span class="eyebrow">SMALL WINS</span><h2>${today.length?'今日の一歩、達成。':'今日は1問で、一歩前へ。'}</h2></div><span class="badge ${today.length?'good':''}">${today.length?'✓ 今日'+today.length+'問':'1問から'}</span></div><p class="muted">${today.length?'ヒントを使った問題も、解答を読んだ問題も、取り組んだ記録として残ります。':'短く取り組んだ記録も残ります。空いた日があっても、いつでも再開できます。'}</p><div class="week-calendar" aria-label="この7日間の問題への取り組み">${dates.map(d=>{const count=done.filter(a=>day(a.completedAt)===day(d)).length;return `<div class="calendar-day ${count?'studied':''} ${day(d)===day(now())?'today':''}" aria-label="${dateText(d)}、${count}問に取り組みました"><span>${d.toLocaleDateString('ja-JP',{weekday:'short'})}</span><strong>${count?'✓':'・'}</strong><small>${d.getDate()}日</small></div>`;}).join('')}</div><p class="page-note">この7日間で${active}日、問題に取り組みました。累計${unique}種類・${done.length}回。</p>${recent?`<p class="progress-feedback"><strong>記録に残った前進</strong>${esc(question(recent.questionId).title)}：${esc(improvement(recent))}</p>`:''}<details class="achievements"><summary>小さな達成 ${earned.length} / 4</summary><div class="achievement-list">${earned.map(a=>`<div class="achievement"><span aria-hidden="true">✓</span><div><strong>${a.title}</strong><p>${a.detail}</p></div></div>`).join('')}${next?`<p class="page-note">次の小さな達成：${next.detail}</p>`:'<p class="page-note">4つの達成がそろいました。次は別の日に思い出してみよう。</p>'}</div></details></section>`;
}

function studyHTML() {
  const a=current(); const original=question(a.questionId); const q={...original,...a.materialSnapshot}; const answered=complete(a);
  const count=sessionCount();
  return `<div class="study-toolbar"><button class="button quiet" data-action="pause">← ${answered?'学習ホームへ':'中断してホームへ'}</button><p class="page-note">${state.session.topic?esc(state.session.topic)+'のみ · ':''}今回 ${count}問 · 目安 ${state.session.goal}問 <span class="muted">· いつでも終了OK</span></p></div><article class="panel question-panel"><div class="study-stage"><span class="${!answered?'current':''}">01 考える</span><span class="${answered?'current':''}">02 解説を読む</span></div><div class="question-meta"><span class="badge">${esc(q.topic)}</span><span>令和6年 春期 · 問${q.number}</span></div>${a.readingNote?`<p class="reading-context small">読んだ範囲：${esc(a.readingNote)}</p>`:''}<h1>${esc(q.title)}</h1><p class="question-stem">${esc(q.stem)}</p>
  ${q.image?`<figure class="question-figure"><a class="figure-link" href="${q.image}" target="_blank" rel="noopener"><img src="${q.image}" alt="${esc(q.imageAlt)}"></a><figcaption>図を押すと、大きく開けます。</figcaption></figure>`:''}
  <fieldset class="choices"><legend>${answered?'選択と正解':'答えを1つ選んでください'}</legend>${q.choices.map((c,i)=>`<label class="choice ${a.selected===i?'selected':''} ${answered&&q.answer===i?'correct-choice':''} ${answered&&a.selected===i&&q.answer!==i?'wrong-choice':''}"><input type="radio" name="answer" value="${i}" ${a.selected===i?'checked':''} ${answered?'disabled':''}><span class="choice-code">${c.label}</span><span class="choice-text">${c.image?`<img src="${c.image}" alt="${esc(c.text)}">`:''}${esc(c.text)}${answered&&q.answer===i?' <strong>（正解）</strong>':''}${answered&&a.selected===i?' <span class="small">（あなたの選択）</span>':''}</span></label>`).join('')}</fieldset>
  ${!answered?`<label class="confidence"><input id="confidence" type="checkbox" ${a.confidence?'checked':''}>自信がないので、正解でも解き直したい</label>`:''}
  <section class="hint-section" aria-label="段階的なヒント"><div class="hint-head"><h3>行き詰まったら、ヒント。</h3><span class="hint-count">${a.hintCount} / ${q.hints.length}</span></div><div id="hints" aria-live="polite">${q.hints.slice(0,a.hintCount).map((h,i)=>`<div class="hint-box" tabindex="-1"><h4>${i+1}. ${esc(h.title)}${h.revealsAnswer?'（答えを含む）':''}</h4><p>${esc(h.text)}</p></div>`).join('')}</div>${a.hintCount<q.hints.length?`<button class="button secondary" style="margin-top:14px" data-action="hint">${a.hintCount?'次のヒントを見る':'ヒントを1つ見る'}</button>`:`<p class="page-note" style="margin-top:12px">ヒントはここまで。自分の言葉で考えてみよう。</p>`}${answered?'<p class="page-note" style="margin-top:10px">解答後のヒント閲覧は、解答前の記録に加えません。</p>':''}</section>
  ${answered?resultHTML(q,a):`<div class="answer-actions"><button class="button primary" data-action="submit" ${a.selected===null?'disabled':''}>この答えで確認する</button><button class="button quiet" data-action="reveal">解答を見て学ぶ</button></div><button class="button quiet" style="margin-top:8px" data-action="postpone">この問題はあとで解く</button>`}
  <details class="source-details"><summary>問題の出典と教材について</summary><p>出典：${esc(q.source)}</p><p>${esc(q.adaptation)} ヒント・解説は独自作成で、IPAの公式解説ではありません。</p><div class="link-list"><a href="https://www.ipa.go.jp/shiken/mondai-kaiotu/m42obm000000afqx-att/2024r06h_ap_am_qs.pdf#page=${q.page}" target="_blank" rel="noopener">公式問題PDF</a><a href="https://www.ipa.go.jp/shiken/mondai-kaiotu/m42obm000000afqx-att/2024r06h_ap_am_ans.pdf" target="_blank" rel="noopener">公式解答PDF</a></div></details></article>`;
}
function resultHTML(q,a) {
  const info=reviewInfo(q); const count=sessionCount();
  return `${sessionMilestoneHTML()}<section class="result" id="result" aria-label="解答と解説"><span class="eyebrow">FEEDBACK</span><h2 id="result-heading" tabindex="-1">${labels[a.status]}${a.status==='incorrect'?'。ここから覚えよう。':'。ひと区切り！'}</h2>${progressFeedbackHTML(a)}<p><strong>正解：${q.choices[q.answer].label}</strong> <span class="small muted">· 解答前のヒント ${a.hintsBeforeAnswer}/3${a.confidence?' · 自信なし':''}</span></p><p class="explanation">${esc(q.summary)}</p>${a.selected!==null&&a.selected!==q.answer?`<p class="explanation"><strong>選んだ${q.choices[a.selected].label}は？</strong><br>${esc(q.choiceReasons[a.selected])}</p>`:''}<details ${a.status==='incorrect'||a.status==='revealed'?'open':''}><summary>解き方を順番に読む</summary><p class="explanation">${esc(q.explanation)}</p></details><details><summary>ほかの選択肢も確認する</summary><ul class="reason-list">${q.choiceReasons.map((r,i)=>`<li><b>${q.choices[i].label}</b>${esc(r)}</li>`).join('')}</ul></details><p class="takeaway"><strong>次に使える考え方</strong>${esc(q.takeaway)}</p><p class="review-date">次の復習目安：${dateText(info.due)}<br><span class="small">${info.needs?'明日、ヒントなしで思い出してみよう。':'自信あり・ヒントなしの正解は、別の日に'+info.successes+'回。'} 日付はこのアプリの目安です。</span></p>${q.related.length?`<details><summary>同じ考え方を使う問題</summary>${q.related.map(id=>`<button class="button secondary" style="margin-top:8px" data-action="start" data-id="${id}">${esc(question(id).title)} →</button>`).join('')}</details>`:''}</section>${a.topic?`<button class="button quiet" style="margin-top:14px" data-view="topics">分野の一覧に戻る</button>`:''}<div class="finish-actions"><button class="button secondary" data-action="end">${count>=state.session.goal?'今日のひと区切りを終える':'ここで終える'}</button><button class="button primary" data-action="next">${state.session.topic&&!hasFreshTopicQuestion()?'同じ分野をもう一度':count>=state.session.goal?'もう1問やる':'次の問題へ'}</button></div>`;
}
function reviewHTML() {
  const list=reviewQuestions(); const paused=state.attempts.filter(a=>!complete(a));
  return `<div class="page-heading"><span class="eyebrow">RECALL & RETRY</span><h1>思い出して、もう一度。</h1><p class="muted">不正解・ヒント利用・自信なし・復習日が来た問題。</p></div><section class="panel"><h2>解き直し候補 <span class="badge">${list.length}問</span></h2>${list.length?list.map(({q,info})=>`<div><p class="page-note" style="margin-top:18px">${info.isDue?'復習日が来ています':'復習目安：'+dateText(info.due)+' · 今すぐ解いてもOK'}</p>${rowHTML(q,info,'start','解き直す')}</div>`).join(''):'<div class="empty"><p>いまは候補がありません。</p><p class="small">まず1問解いてみよう。間違えた問題も、ヒントで解けた問題も、ここに残ります。</p><button class="button primary" data-action="start-session">学習を始める</button></div>'}</section>${paused.length?`<section class="panel"><h2>あとで解く・途中の問題</h2><p class="page-note">未解答は、不正解として数えません。</p>${paused.slice().reverse().map(a=>`<div class="row"><div><p class="row-title">${esc(question(a.questionId).title)}</p><p class="row-meta">${timeText(a.updatedAt)} · ヒント ${a.hintCount}/3</p></div><button class="button secondary" data-action="resume" data-id="${a.id}">続きから</button></div>`).join('')}</section>`:''}<p class="page-note">復習目安は、要復習なら翌日。自信ありの自力正解は、別の日に正解した回数に応じて3・7・14日後です。</p>`;
}
function historyHTML() {
  return `<div class="page-heading"><span class="eyebrow">YOUR LEARNING LOG</span><h1>解いた道筋が、残ります。</h1><p class="muted">正誤だけでなく、どこまでヒントを見たかも記録。</p></div><section class="panel"><h2>学習の記録 <span class="badge">${state.attempts.length}回</span></h2>${state.attempts.length?state.attempts.slice().reverse().map(a=>`<div class="row"><div><p class="row-title">${esc(question(a.questionId).title)} <span class="small muted">· 問${question(a.questionId).number}</span></p><p class="row-meta">${timeText(a.completedAt||a.updatedAt)}${a.contentRevision!=='original'?' · 編集した教材':''}${a.topic?' · 分野別演習':''}</p>${a.readingNote?`<p class="row-meta">読んだ範囲：${esc(a.readingNote)}</p>`:''}<div class="history-result">${badge(a)} <span class="small muted">${complete(a)?'解答前の':''}ヒント ${a.hintsBeforeAnswer??a.hintCount}/3${a.confidence?' · 自信なし':''}</span></div>${complete(a)&&a.hintCount>a.hintsBeforeAnswer?`<p class="row-meta">解答後にヒント ${a.hintCount-a.hintsBeforeAnswer}つを追加閲覧</p>`:''}</div><div class="row-actions"><button class="button secondary" data-action="resume" data-id="${a.id}">${complete(a)?'解説を見る':'続きから'}</button>${complete(a)?`<button class="button quiet" data-action="start" data-id="${a.questionId}">解き直す</button>`:''}</div></div>`).join(''):'<div class="empty"><p>まだ学習記録はありません。</p><button class="button primary" data-action="start-session">まず1問、始める</button></div>'}</section><p class="page-note">「自力で正解」は、解答前のヒント利用も答えの閲覧もなかった記録です。習得を保証する判定ではありません。</p>`;
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
  if(!s||s.version!==1||!Array.isArray(s.attempts)||s.attempts.length>20000||!['home','study','review','history','materials','topics'].includes(s.view)||!s.settings||typeof s.settings.largeText!=='boolean'||![1,3,5].includes(s.settings.sessionSize)||!s.session||!Number.isInteger(s.session.goal)||s.session.goal<1||s.session.goal>5||!Array.isArray(s.session.attemptIds)||!s.overrides||Array.isArray(s.overrides)||typeof s.overrides!=='object') fail();
  s.readingNotes ??= {}; s.session.topic ??= null;
  if(typeof s.readingNotes!=='object' || s.readingNotes===null || Array.isArray(s.readingNotes) || !(s.session.topic===null||topics().includes(s.session.topic))) fail();
  for(const [topic,note] of Object.entries(s.readingNotes)) if(!topics().includes(topic)||!validText(note,200)) fail();
  const ids=new Set();
  for(const a of s.attempts) {
    if(a && !(a.topic===undefined||a.topic===null||topics().includes(a.topic)) || a && !(a.readingNote===undefined||validText(a.readingNote,200))) fail();
    if(!a||!validText(a.id,100)||!/^[a-zA-Z0-9-]+$/.test(a.id)||ids.has(a.id)||!base.some(q=>q.id===a.questionId)||!Object.hasOwn(labels,a.status)||!validDate(a.startedAt)||!validDate(a.updatedAt)||!(a.selected===null||Number.isInteger(a.selected)&&a.selected>=0&&a.selected<4)||!Number.isInteger(a.hintCount)||a.hintCount<0||a.hintCount>3||typeof a.confidence!=='boolean'||typeof a.answerViewedBefore!=='boolean'||!Number.isFinite(a.scrollY)||a.scrollY<0||!validText(a.contentRevision,100)||!Number.isInteger(a.questionVersion)||!validMaterial(a.materialSnapshot)) fail();
    if(complete(a)?!validDate(a.completedAt)||!Number.isInteger(a.hintsBeforeAnswer)||a.hintsBeforeAnswer<0||a.hintsBeforeAnswer>a.hintCount:a.completedAt!==null||a.hintsBeforeAnswer!==null) fail();
    if(!Array.isArray(a.hintEvents)||a.hintEvents.length!==a.hintCount||a.hintEvents.some((e,i)=>!e||e.step!==i+1||!validDate(e.at)||!['before','after'].includes(e.phase))) fail();
    const q=base.find(q=>q.id===a.questionId);
    if(a.topic && a.topic!==q.topic)fail();
    if(a.status==='correct'&&(a.selected!==q.answer||a.hintsBeforeAnswer!==0||a.answerViewedBefore)||a.status==='assisted'&&(a.selected!==q.answer||a.hintsBeforeAnswer===0||a.answerViewedBefore)||a.status==='incorrect'&&(a.selected===null||a.selected===q.answer)||a.status==='revealed'&&!a.answerViewedBefore) fail();
    ids.add(a.id);
  }
  if(s.currentId!==null&&!ids.has(s.currentId)||s.session.attemptIds.some(id=>!ids.has(id))||new Set(s.session.attemptIds).size!==s.session.attemptIds.length) fail();
  if(s.session.topic && s.session.attemptIds.some(id=>base.find(q=>q.id===s.attempts.find(a=>a.id===id).questionId).topic!==s.session.topic))fail();
  for(const [id,m] of Object.entries(s.overrides)) if(!base.some(q=>q.id===id)||!validMaterial(m)||!validText(m.revision,100)||Object.keys(m).some(k=>!['hints','summary','explanation','takeaway','revision'].includes(k))) fail();
  return s;
}
main.addEventListener('click',e=>{
  const el=e.target.closest('[data-action],[data-view]'); if(!el) return;
  if(el.dataset.view) { go(el.dataset.view); return; }
  const action=el.dataset.action; const a=current();
  if(action==='start-session') { const goal=Number(el.dataset.count || 1);state.settings.sessionSize=goal;start(null,true,{goal}); }
  else if(action==='topic-session') { if(!topics().includes(el.dataset.topic))return;start(null,true,{goal:Number(el.dataset.count),topic:el.dataset.topic}); }
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
main.addEventListener('input',e=>{if(e.target.dataset.readingTopic){state.readingNotes[e.target.dataset.readingTopic]=e.target.value.trim().slice(0,200);save();}});
main.addEventListener('change',e=>{
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
