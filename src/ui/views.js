import {studyEntryButton,studyBackButton,aiQuestionButton} from './study-controls.js';
import {legalContextHTML} from './legal-context.js';
import {isMultiple,chosenIds,correctIds,matchesChoiceAnswer,answerLabels,selectionInstruction,canSubmit} from '../domain/question-format.js';
import {questionTextHTML} from './question-text.js';
import {inlineTextHTML} from './inline-text.js';
import {learningTrendHTML} from './learning-trend.js';
import {imageZoomCue} from './image-zoom.js';
import {fieldBar,fieldLegend,compactFieldProgress} from './field-progress.js';
import {summarizeFields} from '../domain/analytics.js';
import {examPartsFor,dateInZone} from '../domain/planning.js';
import {esc, now, dateText, timeText} from '../utils.js';
import {complete, labels, enriched, hintKind, hintTotal} from '../domain/study.js';
import {canStartDiagnostic} from '../domain/qualification-features.js';

// Render from a snapshot of the current context; this module does not save or navigate.
export function createViews(context) {
 const {studyAllowed=()=>true,state, workspaceViews, base, catalog, PAGE_SIZE, examLabel, question, current, reviewInfo, reviewQuestions, topics, topicPool, latest, improvement, sessionCount, hasFreshTopicQuestion, materialUpdateAvailable, qualification, readNote} = context;
 const {cardsEnabled,recommendation,entryActions,studyContext,contextLabel,homeFields,nextAction,fieldData,fieldPartId,topicPartId,fieldAction,reviewTopicId,reviewPartId}=context;
 const explanationCount=base.reduce((n,q)=>n+Number(enriched(question(q.id)||q)),0),mixedExplanations=explanationCount>0&&explanationCount<base.length;
 const mockSizes=[...new Set((qualification.mockSets?.sets||[]).map(s=>s.size))],mockDescription=mockSizes.length===1?`${mockSizes[0]}問 × ${qualification.mockSets.count}回`:`${qualification.mockSets?.count||0}回`;
 const mocksAvailable=Boolean(qualification.mockSets?.count||workspaceViews?.hasMocks);
 const diagnosticsAvailable=canStartDiagnostic(qualification,base,studyAllowed)||workspaceViews?.hasDiagnostics;
 const activeQuestionIds=new Set(base.map(q=>q.id)),continuedParents=new Set(state.attempts.map(a=>a.continuationOf).filter(Boolean));
 const timeZone=workspaceViews?.timeZone||qualification.timeZone||'Asia/Tokyo',at=now(),todayKey=dateInZone(at,timeZone),completed=state.attempts.filter(a=>complete(a)&&Date.parse(a.completedAt)<=Date.parse(at));
function badge(a) { return `<span class="badge ${a.status==='correct'?'good':a.status==='incorrect'?'wrong':complete(a)?'help':''}">${labels[a.status]}</span>`; }
function rowHTML(q, info, action = 'start', label='解く') {
  return `<div class="row"><div><p class="row-title">${esc(q.title)}</p><p class="row-meta">${examLabel(q)} · 問${q.number} · ${esc(q.topic)}</p>${state.settings.paperMode==='paperless'?`<p class="small muted">${esc(contextLabel(q))}</p>`:''}${info?badge(info.a):''}</div><div class="row-actions"><button class="button secondary" data-action="${action}" data-id="${q.id}">${label}</button></div></div>`;
}
function paperModeHTML(){return qualification.studyContext?`<div class="study-mode" role="group" aria-label="出題する問題">${[['paperless','身軽に'],['desk','書いて考える'],['all','おまかせ']].map(([mode,label])=>`<button class="button secondary" data-action="paper-mode" data-mode="${mode}" aria-pressed="${state.settings.paperMode===mode}">${label}</button>`).join('')}</div>`:'';}
function partSelector(name,value){const parts=examPartsFor(qualification).filter(p=>p.practiceAvailable);return parts.length>1?`<label class="field-part">対象パート <select name="${name}"><option value="">全パート</option>${parts.map(p=>`<option value="${esc(p.id)}" ${value===p.id?'selected':''}>${esc(p.label)}</option>`).join('')}</select></label>`:'';}
function fieldButtonData(row,mode,part){
 const action=fieldAction(row.topicId,part,mode);
 return {action,attributes:`data-action="field-practice" data-topic="${esc(row.label)}" data-topic-id="${esc(row.topicId)}" data-part-id="${esc(part||'')}" data-paper-mode="${mode}" data-id="${esc(action.questionId||'')}" data-resume-id="${esc(action.kind==='resume'?action.attemptId:'')}" ${action.kind==='unavailable'?'disabled':''}`};
}
function homeHTML() {
 const names={paperless:'身軽に1問',desk:'書いて考える1問',all:'おまかせで1問'};
 const entrances=Object.entries(entryActions).map(([mode,a])=>{const selected=mode===state.settings.lastEntry,resume=a.kind==='resume',disabled=a.kind==='unavailable';return studyEntryButton({label:names[mode],primary:selected,disabled,title:disabled?a.reason:undefined,cue:resume?'続きから ':'',attributes:{'data-action':resume?'entry-resume':'entry-start','data-paper-mode':mode,'data-id':resume?a.attemptId:a.questionId||'','data-topic-id':a.scope?.topicId||'','data-part-id':a.scope?.examPartId||'','data-last-entry':selected?'true':undefined}});}).join('');
 const diagnosticEntry=workspaceViews?.diagnosticEntry()||{view:'diagnostics',label:'診断を受ける'};
 const planRecommendation=recommendation?.kind==='question',paperMode=state.settings.lastEntry,reviews=reviewQuestions();
 const due=homeFields.rows.find(row=>reviews.some(({q,info})=>q.topicId===row.topicId&&info.isDue)&&fieldAction(row.topicId,null,paperMode).kind!=='unavailable');
 const suggestion=due&&!planRecommendation?`<button class="button secondary" ${fieldButtonData(due,paperMode,null).attributes}>${esc(due.label)}を解く</button>`:'';
 const planCard=workspaceViews?.homeSupportHTML({nextTopic:planRecommendation?question(recommendation.questionId)?.topic:null,planRecommendation,paperMode,suggestion});
 return `<div class="home-core"><section class="panel quick-start-panel hero-start"><h1 class="entry-heading">とりあえずはじめる</h1><div class="quick-start entry-list">${entrances}${studyEntryButton({label:'分野を選んで1問',field:true,attributes:{'data-view':'topics','data-paper-mode':state.settings.lastEntry}})}</div>${Object.values(entryActions).every(a=>a.kind==='unavailable')?`<p class="small start-note">${esc(nextAction.reason)}</p>`:''}</section>
 ${diagnosticsAvailable||mocksAvailable?`<div class="home-assessments" role="group" aria-label="診断と模試">${diagnosticsAvailable?`<button class="button assessment-card" data-view="diagnostics"><span class="assessment-title"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20V11M10 20V5M16 20v-8M22 20H2"/></svg><span>実力診断</span></span><span class="assessment-detail"><span>${esc(diagnosticEntry.label)}</span><span class="assessment-arrow" aria-hidden="true">→</span></span></button>`:''}${mocksAvailable?`<button class="button assessment-card" data-view="mocks"><span class="assessment-title"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 4H5v17h14V4h-4M9 2h6v5H9zM8 12h8M8 16h5"/></svg><span>模試</span></span><span class="assessment-detail"><span>${qualification.mockSets?.count?esc(mockDescription):'記録・続きから'}</span><span class="assessment-arrow" aria-hidden="true">→</span></span></button>`:''}</div>`:''}
 <section class="home-shortcuts" aria-label="単語帳・解き直し"><div class="button-row">${cardsEnabled&&qualification.flashcards?.count?'<button class="button secondary" data-action="cards-open">単語帳</button>':''}<button class="button secondary" data-view="review">解き直し</button></div></section>
 ${planCard||suggestion}</div>`;
}
function topicsHTML() {
 const byId=new Map(homeFields.rows.map(row=>[row.topicId,row]));
 return `<div class="page-heading"><h1>分野別に解く</h1></div>${paperModeHTML()}${partSelector('topic-part',topicPartId)}<p class="small muted field-scope">直近${homeFields.days}日の記録</p>
 <div class="field-list">${qualification.topics.map(t=>{
  const row=byId.get(t.id),{action,attributes}=fieldButtonData(row,state.settings.paperMode,topicPartId),note=readNote(t.name);
  return `<section class="topic-card" id="field-${esc(t.id)}"><button class="field-start" ${attributes} aria-label="${esc(t.name)}を${action.kind==='resume'?'再開':'開始'}"><span class="field-copy"><span class="field-title"><strong>${esc(t.name)}</strong></span>${row.focus?'<span class="field-focus-tag">計画の重点</span>':''}${compactFieldProgress(row)}${note.trim()?`<span class="field-note">教科書：${esc(note)}</span>`:''}${action.kind==='unavailable'?`<span class="small muted field-unavailable">${onlineLabel(action.reason)}</span>`:''}</span><span class="field-direction">${action.kind==='resume'?'<span class="field-resume-label">続きから</span>':''}<span class="field-arrow" aria-hidden="true">→</span></span></button></section>`;
 }).join('')}</div><div class="button-row field-links"><button class="button quiet" data-view="history">詳しい分野の記録 →</button><button class="button quiet" data-view="materials" aria-label="問題を探す">問題を探す <span aria-hidden="true">→</span></button></div>`;
}
function onlineLabel(reason){return reason?.includes('保存済み')?'保存済みの問題なし':'この条件の候補なし';}
function fieldRecordsHTML(){
 const data=fieldData,summary=summarizeFields(data),byId=new Map(data.rows.map(row=>[row.topicId,row])),reviews=reviewQuestions();
 return `<div class="page-heading heading-row"><h1>学習記録</h1><button class="button quiet" data-view="topics">分野を選ぶ →</button></div>${assessmentLinksHTML()}
 ${partSelector('field-part',fieldPartId)}<section class="panel overall-accuracy" aria-label="全分野の自力正答率"><h2>自力正答率 <span>· 直近${data.days}日</span></h2><p class="overall-rate">${summary.rate===null?'未確認':`${Math.round(summary.rate*100)}<small>%</small>`}</p><p class="overall-count">${summary.total}問に取り組み · 自力正解 ${summary.correct}問</p></section>${completed.length?motivationHTML():''}${context.trendData&&(context.trendData.topicId||context.trendData.points.filter(point=>point.total).length>1)?`<details class="record-trend" ${context.trendPointDate||context.trendData.topicId?'open':''}><summary>正答率の推移</summary>${learningTrendHTML({data:context.trendData,qualification,date:context.trendPointDate})}</details>`:''}
 <h2 class="field-record-heading">分野別の記録</h2><p class="small muted field-scope">直近${data.days}日 · 問題ごとの最後の完了記録</p>${fieldLegend(false)}<section class="panel field-records">${qualification.topics.map(t=>{
  const row=byId.get(t.id),part=fieldPartId,{action,attributes}=fieldButtonData(row,state.settings.lastEntry,part),count=reviews.filter(x=>x.q.topicId===t.id&&(!part||x.q.examPartId===part)).length;
  const note=readNote(t.name),conflict=context.noteConflictHTML?.(t.id)||'';
  return `<section class="field-record" id="record-field-${esc(t.id)}"><div class="heading-row"><h3>${esc(t.name)}</h3>${count&&action.kind!=='resume'?`<button class="button quiet field-review" data-action="field-review" data-topic-id="${esc(t.id)}" data-part-id="${esc(part||'')}">解き直す · ${count}問</button>`:`<button class="button quiet" ${attributes}>${action.kind==='resume'?'続きから':'学習する'} →</button>`}</div>${row.focus?'<span class="field-focus-tag">計画の重点</span>':''}${fieldBar(row)}<details class="field-note-editor" ${conflict?'open':''}><summary>${note.trim()?esc(note):'教科書メモ'}</summary><input class="field-note-input" type="text" maxlength="200" data-reading-topic="${esc(t.name)}" aria-label="${esc(t.name)}の教科書メモ" placeholder="ページや読んだ範囲" value="${esc(note)}"><div id="note-conflict-${esc(t.id)}">${conflict}</div></details></section>`;
 }).join('')}</section><details class="page-note"><summary>グラフの数え方</summary><p>通常：直近28日の問題ごとの最後の完了記録。自力正解÷（自力・ヒント付き正解・不正解・解答閲覧）。途中・診断・未来の記録は含みません。未確認は0%ではありません。記録少なめは10問未満の目印です。推移は直近6週の各時点で同じ28日間の集計を行います。解答後のヒント閲覧で結果は変わりません。割合だけで習熟・合格は判断しません。</p></details>`;
}
function progressFeedbackHTML(a) { const message=improvement(a);return message?`<p class="progress-feedback">${esc(message)}</p>`:''; }
function motivationHTML() {
  const today=completed.filter(a=>dateInZone(a.completedAt,timeZone)===todayKey).length;
  const unique=new Set(completed.filter(a=>activeQuestionIds.has(a.questionId)).map(a=>a.questionId)).size;
  return `<p class="small muted study-counts">今日 ${today}問 · 取り組んだ問題 ${unique} / ${base.length}問</p>`;
}
function studyHTML() {
  const a=current(); const original=a.questionSnapshot||question(a.questionId); const q={...original,...a.materialSnapshot,choiceReasons:a.materialSnapshot.choiceReasons || [],hintStatus:hintKind(a.materialSnapshot)}; const answered=complete(a);
  const count=sessionCount();
  return `<div class="study-toolbar">${answered?'':studyBackButton({action:'pause',label:'中断'})}${!answered&&state.session.intent==='direct'?`<button class="button secondary" data-action="direct-return">${state.session.returnView==='flashcards'?'単語帳に戻る':state.session.returnView==='study'?'元の学習に戻る':'元の画面に戻る'}</button>`:''}<p class="page-note">${state.session.intent==='review'?'復習 · ':state.session.topic?esc(state.session.topic)+'のみ · ':state.session.topicIds?.length?'計画の重点 · ':''}今回 ${count}問</p></div><article class="panel question-panel"><div class="question-meta"><span class="badge">${esc(q.topic)}</span><span>${examLabel(q)} · 問${q.number}</span></div>${a.readingNote?`<p class="reading-context small">読んだ範囲：${esc(a.readingNote)}</p>`:''}<h1 class="sr-only">${esc(q.title)}</h1>${legalContextHTML(q)}${q.stem?`<div class="question-stem rich-question">${questionTextHTML(q.stem)}</div>`:sourceImagesHTML(q)}
  ${q.image?`<figure class="question-figure"><a class="figure-link image-zoom-target" href="${esc(q.image)}" target="_blank" rel="noopener" aria-label="問題の図を拡大（別タブで開く）"><img src="${esc(q.image)}" alt="${esc(q.imageAlt)}">${imageZoomCue}</a></figure>`:''}
  <fieldset class="choices"><legend>${answered?'選択と正解':selectionInstruction(q)}</legend>${q.choices.map((c,i)=>`<label class="choice ${chosenIds(a).includes(c.id)?'selected':''} ${answered&&correctIds(q).includes(c.id)?'correct-choice':''} ${answered&&chosenIds(a).includes(c.id)&&!correctIds(q).includes(c.id)?'wrong-choice':''}"><input type="${isMultiple(q)?'checkbox':'radio'}" name="answer" value="${i}" ${chosenIds(a).includes(c.id)?'checked':''} ${answered?'disabled':''}><span class="choice-code">${esc(c.label)}</span>${q.choicePresentation!=='codes'&&(c.text||c.image)?`<div class="choice-text rich-question">${c.image?`<img src="${esc(c.image)}" alt="選択肢${esc(c.label)}の図">`:''}${questionTextHTML(c.text)}</div>`:''}${answered&&correctIds(q).includes(c.id)?'<span class="sr-only">（正解）</span>':''}${answered&&chosenIds(a).includes(c.id)?'<span class="sr-only">（あなたの回答）</span>':''}</label>`).join('')}</fieldset>
  ${!answered?`<label class="confidence"><input id="confidence" type="checkbox" ${a.confidence?'checked':''}>自信がないので、正解でも解き直したい</label>`:''}
  ${answered?resultHTML(q,a):hintsHTML(q,a,false)+`<div class="answer-actions"><button class="button primary" data-action="submit" ${canSubmit(a)?'':'disabled'}>回答する</button><button class="button quiet" data-action="reveal">解答を見る</button></div><details class="study-options"><summary>問題の操作</summary><p class="small muted">あとで解く問題は、解き直しから再開できます。</p><div class="button-row"><button class="button secondary" data-action="postpone">あとで解く</button>${(state.session.paperMode||state.settings.paperMode)==='paperless'?'<button class="button secondary paper-required" data-action="desk-later">紙ペンが必要（机で再開）</button>':''}</div></details>`}
  ${sourceDetailsHTML(q)}</article>`;
}
function hintsHTML(q,a,answered) {
  return `${q.hints.length||materialUpdateAvailable(a)?`<section class="hint-section" aria-label="段階的なヒント">${materialUpdateAvailable(a)?`<div class="hint-update"><p class="page-note">${hintKind(a.materialSnapshot)==='topic-guide'?'以前の分野共通ガイドが保存されています。':'この記録には更新前の教材が保存されています。'}</p><button class="button secondary" data-action="latest-hints">最新の教材で${answered?'解き直す':'続ける'}</button></div>`:''}${q.hints.length?`<div class="hint-head"><h3>${hintKind(q)==='individual'?'ヒント':'考える手順（分野共通）'}</h3><span class="hint-count">${a.hintCount} / ${q.hints.length}</span></div><div id="hints" aria-live="polite">${q.hints.slice(0,a.hintCount).map((h,i)=>`<div class="hint-box" tabindex="-1"><h4>${i+1}. ${esc(h.title)}${h.revealsAnswer?'（答えを含む）':''}</h4><p>${inlineTextHTML(h.text)}</p></div>`).join('')}</div>${a.hintCount<q.hints.length?`<button class="button secondary" style="margin-top:14px" data-action="hint">${a.hintCount?'次のヒントを見る':'ヒントを1つ見る'}${q.hints[a.hintCount].revealsAnswer?'（答えを含む）':''}</button>`:''}`:''}</section>`:''}`;
}
function sourceDetailsHTML(q) {
  const original=q.stem&&q.sourceImages?.length;
  return `<details class="source-details ${original?'original-question':''}" data-question-id="${esc(q.id)}"><summary>原本・出典</summary>${q.source?`<p>出典：${esc(q.source)}</p>`:''}${q.syllabus?`<p>${esc(q.syllabus.label)} · ${esc(q.syllabus.language)}</p>`:''}${q.adaptation?`<p>${esc(q.adaptation)}</p>`:''}<div class="link-list">${(q.sourceRefs||[]).filter(url=>url!==q.questionUrl&&url!==q.answerUrl).map((url,i)=>`<a href="${esc(url)}" target="_blank" rel="noopener">参考資料${i+1}</a>`).join('')}${q.questionUrl?`<a href="${esc(q.questionUrl)}${q.page?'#page='+q.page:''}" target="_blank" rel="noopener">${esc(qualification.questionLinkLabel||'問題の出典')}</a>`:''}${q.answerUrl?`<a href="${esc(q.answerUrl)}" target="_blank" rel="noopener">${esc(qualification.answerLinkLabel||'解答の出典')}</a>`:''}</div>${original?'<div class="original-content"></div>':''}</details>`;
}
function choiceReasonsHTML(q,selected){
  const correct=correctIds(q);
  const reasons=q.choices.flatMap((choice,index)=>q.choiceReasons[index]?[{
    choice,text:q.choiceReasons[index],missed:selected.includes(choice.id)&&!correct.includes(choice.id)
  }]:[]);
  if(!reasons.length)return '';
  const chosen=reasons.filter(reason=>reason.missed),others=reasons.filter(reason=>!reason.missed);
  const rows=[...chosen,...others].map(({choice,text})=>`<li><b>${esc(choice.label)}</b>${inlineTextHTML(text)}</li>`).join('');
  return `<details ${chosen.length?'open':''}><summary>選択肢ごとの解説</summary><ul class="reason-list">${rows}</ul></details>`;
}
function resultHTML(q,a) {
  const info=reviewInfo(q);
  const selected=chosenIds(a,q), matched=selected.length>0&&matchesChoiceAnswer(q,selected);
  const direct=state.session.intent==='direct',review=state.session.intent==='review';
  const exit=direct?`<button class="button secondary" data-action="direct-return">${state.session.returnView==='flashcards'?'単語帳に戻る':state.session.returnView==='study'?'元の学習に戻る':'元の画面に戻る'}</button>`:review?`<button class="button secondary" data-view="review" data-review-topic-id="${esc(state.session.topicId||'')}" data-review-part-id="${esc(state.session.examPartId||'')}">解き直しに戻る</button>`:state.session.topicId?'<button class="button secondary" data-view="topics">分野の一覧に戻る</button>':'<button class="button secondary" data-action="end">ホーム</button>';
  return `<section class="result ${matched?'result-correct':'result-incorrect'}" id="result" aria-label="解答と解説"><h2 id="result-heading" tabindex="-1">${labels[a.status]}</h2><div class="answer-selection" aria-label="あなたの回答と正解"><span>あなたの回答：<strong>${esc(answerLabels(q,selected))}</strong></span><span>正解：<strong>${esc(answerLabels(q,correctIds(q)))}</strong></span></div>${!enriched(q)?`<p class="page-note">個別の解答解説は未追加です。正解は${esc(qualification.sourceLabel)}の解答と照合済みです。</p>`:''}${q.summary?`<p class="explanation">${inlineTextHTML(q.summary)}</p>`:''}<details ${a.status==='incorrect'||a.status==='revealed'?'open':''}><summary>${enriched(q)?'解説':'分野の復習メモ'}</summary><p class="explanation">${inlineTextHTML(q.explanation)}</p></details>${choiceReasonsHTML(q,selected)}${q.takeaway?`<p class="takeaway"><strong class="takeaway-label">要点</strong>${inlineTextHTML(q.takeaway)}</p>`:''}${q.related.length?`<details><summary>関連問題</summary>${q.related.filter(id=>activeQuestionIds.has(id)).map(id=>`<button class="button secondary" style="margin-top:8px" data-action="start" data-id="${id}">${esc(question(id).title)} →</button>`).join('')}</details>`:''}${q.hints.length||materialUpdateAvailable(a)?`<details class="result-hints"><summary>解くときのヒント</summary>${hintsHTML(q,a,true)}</details>`:''}</section><div class="ai-explain-entry">${aiQuestionButton({action:'ask-ai'})}</div><details class="result-record"><summary>この回答の記録</summary><p class="small muted">解答前のヒント ${a.hintsBeforeAnswer}/${hintTotal(a)}${a.confidence?' · 自信なし':''}${a.hintCount>a.hintsBeforeAnswer?' · 解答後にヒント '+(a.hintCount-a.hintsBeforeAnswer)+'つ':''} · 次の復習：${esc(info.dueDate||dateText(info.due))}</p>${progressFeedbackHTML(a)}</details><div class="finish-actions">${exit}${!direct&&hasFreshTopicQuestion()?'<button class="button primary" data-action="next">もう1問</button>':''}</div>`;
}
function reviewHTML() {
  const list=reviewQuestions().filter(x=>(!reviewTopicId||x.q.topicId===reviewTopicId)&&(!reviewPartId||x.q.examPartId===reviewPartId)); const paused=state.attempts.filter(a=>!complete(a)&&!continuedParents.has(a.id)&&(!reviewTopicId||a.questionSnapshot?.topicId===reviewTopicId)&&(!reviewPartId||a.questionSnapshot?.examPartId===reviewPartId));const reviewTopic=qualification.topics.find(t=>t.id===reviewTopicId);
  return `<div class="page-heading heading-row"><h1>${reviewTopic?esc(reviewTopic.name)+'の':''}解き直し</h1><button class="button study-back-button" data-view="home">⌂ ホーム</button></div>${reviewTopic?'<p><button class="button secondary" data-view="review">全分野の解き直し</button></p>':''}<section class="panel"><h2>復習候補 <span class="badge">${list.length}問</span></h2>${list.length?list.map(({q,info})=>`<div><p class="page-note" style="margin-top:18px">復習日：${esc(info.dueDate||dateText(info.due))}</p>${rowHTML(q,info,'review-start','解き直す')}</div>`).join(''):'<div class="empty"><p>復習候補はありません。</p><button class="button primary" data-action="start-session">とりあえずはじめる</button></div>'}</section>${paused.length?`<section class="panel"><h2>中断中</h2>${paused.slice().reverse().map(a=>`<div class="row"><div><p class="row-title">${esc(question(a.questionId).title)}</p><p class="row-meta">${timeText(a.updatedAt)} · ヒント ${a.hintCount}/${hintTotal(a)}</p></div><button class="button secondary" data-action="resume" data-id="${a.id}">続きから</button></div>`).join('')}</section>`:''}<details class="page-note"><summary>復習候補と日付</summary><p>不正解だった問題、復習したいと印をつけた問題、復習日が来た問題などを表示します。あとで解く問題もここから再開できます。</p></details>`;
}
function answerHistoryHTML(open=false){
  return `<details class="answer-history" ${open?`open`:``}><summary>回答履歴 · ${state.attempts.length}件</summary><section class="panel">${state.attempts.length?state.attempts.slice().reverse().map(a=>`<div class="row"><div><p class="row-title">${esc(question(a.questionId).title)} <span class="small muted">· 問${question(a.questionId).number}</span></p><p class="row-meta">${timeText(a.completedAt||a.updatedAt)}</p><div class="history-result">${badge(a)}</div></div><div class="row-actions"><button class="button secondary" data-action="resume" data-id="${a.id}">${complete(a)?'解説を見る':'続きから'}</button>${complete(a)&&activeQuestionIds.has(a.questionId)?`<button class="button quiet" data-action="start" data-id="${a.questionId}">解き直す</button>`:''}</div></div>`).join(''):'<div class="empty"><p>まだ学習記録はありません。</p><button class="button primary" data-action="start-session">とりあえずはじめる</button></div>'}</section></details>`;
}
function assessmentLinksHTML(){
  const links=[
    workspaceViews?.hasDiagnosticResults?'<button class="button secondary" data-view="diagnostics">実力診断</button>':'',
    workspaceViews?.hasMocks?'<button class="button secondary" data-view="mocks">模試</button>':''
  ].join('');
  return links?`<div class="button-row record-assessments" aria-label="診断と模試">${links}</div>`:'';
}
function noCompletedHistoryHTML(){
  const content=state.attempts.length?answerHistoryHTML(true):'<section class="panel"><p>まだ学習記録はありません。</p><button class="button primary" data-action="start-session">1問解く</button></section>';
  return `<div class="page-heading heading-row"><h1>学習記録</h1><button class="button quiet" data-view="planning">学習計画</button></div>${assessmentLinksHTML()}${content}`;
}
function historyHTML(){
 if(!completed.length&&!qualification.topics.some(t=>readNote(t.name).trim()))return noCompletedHistoryHTML();
 return `${fieldRecordsHTML()}<section class="panel record-tools"><div class="button-row"><button class="button secondary" data-view="review">解き直し</button><button class="button secondary" data-view="planning">学習計画</button></div></section>${state.attempts.length?answerHistoryHTML():``}`;}

function catalogMatches() {
  const words=catalog.query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  return base.filter(q=>studyAllowed(q)&&(!catalog.year||String(q.year)===catalog.year)&&(!catalog.season||q.season===catalog.season)&&(!catalog.topic||q.topic===catalog.topic)&&(!catalog.enriched||enriched(question(q.id)))&&words.every(w=>`${q.title} ${q.topic} ${q.concept || ''} ${q.searchText || q.stem} ${q.year} ${q.number}`.toLocaleLowerCase().includes(w)));
}
function catalogRowsHTML() {
  const matches=catalogMatches(),pages=Math.max(1,Math.ceil(matches.length/PAGE_SIZE));catalog.page=Math.min(catalog.page,pages);
  const slice=matches.slice((catalog.page-1)*PAGE_SIZE,catalog.page*PAGE_SIZE);
  const packIds=new Set((catalog.year||catalog.season?base.filter(q=>(!catalog.year||String(q.year)===catalog.year)&&(!catalog.season||q.season===catalog.season)):[]).map(q=>q.packId));
  const packId=packIds.size===1?[...packIds][0]:null;
  return `<div class="heading-row catalog-count"><p class="page-note" role="status">${matches.length}問${matches.length?` · ${(catalog.page-1)*PAGE_SIZE+1}〜${(catalog.page-1)*PAGE_SIZE+slice.length}問`:''}</p><button class="button quiet" data-action="reset-filters">絞り込みを解除</button></div>${packId?`<button class="button quiet" data-action="offline-open" data-pack="${esc(packId)}">この試験回を端末に保存</button>`:''}${slice.length?slice.map(q=>`<div class="row"><div><p class="row-title">${esc(q.title)}</p><p class="row-meta">${examLabel(q)} · 問${q.number} · ${esc(q.topic)}</p>${Object.hasOwn(state.overrides,q.id)?'<p class="small muted">自分で編集した教材</p>':mixedExplanations?`<p class="small muted">${enriched(q)?'個別ヒント・解説あり':'解説未追加'}</p>`:''}${latest(q.id)?badge(latest(q.id)):''}</div><div class="row-actions"><details class="catalog-options"><summary aria-label="問${q.number}の操作">⋯</summary><button class="button secondary" data-action="edit" data-id="${q.id}">教材を編集</button></details><button class="button secondary" data-action="start" data-id="${q.id}">解く</button></div></div>`).join(''):'<p class="empty">条件に合う問題はありません。</p>'}<div class="pagination"><button class="button secondary" data-action="catalog-page" data-page="${catalog.page-1}" ${catalog.page===1?'disabled':''}>前の20問</button><span>${catalog.page} / ${pages}</span><button class="button secondary" data-action="catalog-page" data-page="${catalog.page+1}" ${catalog.page===pages?'disabled':''}>次の20問</button></div>`;
}
function materialsHTML() {
  const years=[...new Set(base.map(q=>q.year).filter(Boolean))].sort((a,b)=>b-a),seasons=Object.entries(qualification.seasonLabels||{}).filter(([id])=>base.some(q=>q.season===id));
  return `<div class="page-heading heading-row"><h1>問題と教材</h1><span class="badge">${base.length}問</span></div><section class="panel"><form class="catalog-filters" role="search" id="catalog-form">${years.length?`<label>年度<select name="year"><option value="">全年度</option>${years.map(y=>`<option value="${y}" ${catalog.year===String(y)?'selected':''}>${y}年</option>`).join('')}</select></label>`:''}${seasons.length?`<label>期<select name="season"><option value="">全て</option>${seasons.map(([value,label])=>`<option value="${esc(value)}" ${catalog.season===value?'selected':''}>${esc(label)}</option>`).join('')}</select></label>`:''}<label>分野<select name="topic"><option value="">全分野</option>${topics().map(t=>`<option ${catalog.topic===t?'selected':''}>${esc(t)}</option>`).join('')}</select></label><label class="catalog-search">キーワード<input type="search" name="query" value="${esc(catalog.query)}" placeholder="問題文・用語で探す"></label>${mixedExplanations?`<label class="confidence catalog-enriched"><input type="checkbox" name="enriched" ${catalog.enriched?'checked':''}>個別解説あり</label>`:''}</form><div id="catalog-results">${catalogRowsHTML()}</div></section><details class="page-note"><summary>教材について</summary><p>${esc(qualification.sourceDescription)}</p><a href="${esc(qualification.sourceDoc)}">詳しい出典と利用条件</a></details>`;
}
function sourceImagesHTML(q) {
  return `<div class="source-question">${q.sourceImages.map((src,i)=>`<figure><button type="button" class="source-image-button image-zoom-target" data-action="zoom" data-id="${q.id}" data-image="${i}" aria-label="問題画像を拡大"><img src="${src}" alt="${esc(q.source)}の原本画像${q.sourceImages.length>1?'（'+(i+1)+'/'+q.sourceImages.length+'）':''}" width="${q.imageSizes[i].width}" height="${q.imageSizes[i].height}" decoding="async">${imageZoomCue}</button></figure>`).join('')}</div>`;
}
 return {sourceImagesHTML,homeHTML, topicsHTML, studyHTML, reviewHTML, historyHTML, materialsHTML, catalogRowsHTML};
}
