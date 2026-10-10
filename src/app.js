import {createLearningFeature} from './features/learning.js';
import {initPWA, savedAssetURLs} from '../pwa.js';
import {$,esc,now,day,dateText,timeText} from './utils.js';
import {makeState,complete,labels,hintTotal,enriched,hintKind,createAttempt,openHint,gradeAttempt,finalizeAttempt,selectAnswer} from './domain/study.js';
import {createProgress} from './domain/review.js';
import {learningFields,diagnosticFields} from './domain/analytics.js';
import {allowsQuestion,contextLabel,attemptEntryMode} from './domain/study-context.js';
import {createCardFeature} from './features/cards.js';
import {chooseNextAction,chooseFieldAction} from './domain/next-action.js';
import {practicePool,selectPractice} from './domain/practice.js';
import {activePhase} from './domain/analytics.js';
import {createViews} from './ui/views.js';
import {createStateValidator} from './storage/validate.js';
import {createLocalStore} from './storage/local.js';
import {loadCatalog,appRoot} from './content/catalog.js';
import {initAccountControls,guestAttemptId} from './sync/account.js';
import {createPlanningFeature} from './features/planning.js';

let store, content, qualification, account, planner, cards, learning;
let studyContext=null;
let fieldMode='learning',fieldPartId=null,topicPartId=null,reviewTopicId=null,reviewPartId=null,displayedNextAction=null,displayedEntryActions=null;
let questionIndex = new Map(), progress = createProgress([]);
let catalog = {year:'', season:'', topic:'', query:'', enriched:false, page:1};
const PAGE_SIZE=20;
const examLabel=q=>esc(q.packLabel || `${q.year}年 ${qualification.seasonLabels?.[q.season] || q.season}`);
let base = [], state = makeState(), storageOK = true, corruptRaw = null, editId = null;
const main = $('#main');

const validateState=createStateValidator({getQuestions:()=>base,getTopics:topics,getQualification:()=>qualification});
const validateDiagnosticState=createStateValidator({getQuestions:()=>base,getTopics:topics,getQualification:()=>qualification,allowDiagnosticOnly:true});
const validateDiagnosticAttempt=a=>validateDiagnosticState({...makeState(),attempts:[structuredClone(a)]});
function rebuildProgress(){progress=createProgress(planner?.allAttempts()||state.attempts,{timeZone:planner?.plan()?.timeZone||qualification?.timeZone||'Asia/Tokyo'});}
const latest=id=>progress.latest(id);
const previousAttempt=a=>progress.previousAttempt(a);
const improvement=a=>progress.improvement(a);
const reviewInfo=q=>progress.reviewInfo(q);
function nextAction(ignorePaused=false,mode=state.settings.paperMode,entry=false){return chooseNextAction({qualification,questions:base,attempts:planner?.allAttempts()||state.attempts,plan:planner?.plan(),reviewInfo,available:usableOffline,practiceAllowed:q=>allowsQuestion(q,mode,studyContext,state.settings.deskQuestionIds),paperless:mode==='paperless',ignorePaused,online,excludedQuestionIds:learning?.deferredIds()||[],resumeAllowed:a=>!entry||resumeMode(a)===mode});}
function resumeMode(a){const mode=attemptEntryMode(a,state.session),q=question(a.questionId)||a.questionSnapshot;return q&&!allowsQuestion(q,mode,studyContext,state.settings.deskQuestionIds)?'all':mode;}
function entryActions(){return Object.fromEntries((qualification.studyContext?['paperless','desk','all']:['all']).map(mode=>[mode,nextAction(false,mode,true)]));}
function views(){
 const phase=activePhase(planner?.plan()),recommendation=phase?selectPractice({qualification,questions:base,attempts:planner.allAttempts(),reviewInfo,scope:{topicIds:phase.focusTopicIds,examPartIds:phase.examPartIds},excludedQuestionIds:learning?.deferredIds()||[],available:usableOffline,practiceAllowed:q=>allowsQuestion(q,state.settings.lastEntry,studyContext,state.settings.deskQuestionIds)}):null;
 const diagnosis=planner?.latestDiagnosis(),homeFields=learningFields({qualification,questions:base,attempts:state.attempts,plan:planner?.plan()}),fieldData=fieldMode==='diagnostic'?diagnosticFields(diagnosis,qualification):fieldPartId?learningFields({qualification,questions:base,attempts:state.attempts,plan:planner?.plan(),examPartId:fieldPartId}):homeFields;
 return createViews({cardsEnabled:!!cards,recommendation,homeTopicPool:(topic,id)=>topicPool(topic,id,null,state.settings.lastEntry),entryActions:displayedEntryActions||entryActions(),studyContext,contextLabel:q=>contextLabel(q,studyContext,state.settings.deskQuestionIds),homeFields,nextAction:displayedNextAction||nextAction(),fieldData,fieldMode,fieldPartId,topicPartId,fieldAction,reviewTopicId,reviewPartId,diagnosis,normalAttempts:state.attempts.filter(a=>!a.diagnosticRunId&&!a.questionSnapshot?.diagnosticOnly),state:{...state,attempts:planner?.allAttempts()||state.attempts},workspaceViews:planner?.store()?planner.views():null,base,catalog,PAGE_SIZE,examLabel,question,current,reviewInfo,reviewQuestions,topics,topicPool:state.view==='study'?topicPool:(topic,id,part)=>topicPool(topic,id,part,state.settings.paperMode),latest,previousAttempt,improvement,sessionCount,hasFreshTopicQuestion,materialUpdateAvailable,qualification,readNote});
}
let offlineQuestionIds = new Set();
let online = navigator.onLine;
initPWA({beforeUpdate:()=>store?save():true});
function usableOffline(q) { return online || offlineQuestionIds.has(q.id); }
async function refreshOfflineQuestions() {
  if (!online) {
    const saved = await savedAssetURLs();
    offlineQuestionIds = new Set(base.filter(q => {
      const assets = [...(q.stem ? [] : q.sourceImages), q.image, ...q.choices.map(c => c.image)].filter(Boolean);
      return saved.has(content.packs.get(q.packId)?.url) && assets.every(src => saved.has(new URL(src, document.baseURI).href));
    }).map(q => q.id));
  }
  $('#offline-status').hidden = online;
  $('#offline-status').textContent = 'オフライン · 保存済みの問題を解けます。';
}
async function setConnection(available) {
  available = available && navigator.onLine;
  if (online === available) return;
  online = available; await refreshOfflineQuestions();
  if (base.length && state.view!=='planning') render(false);
}
window.addEventListener('offline', () => setConnection(false));
window.addEventListener('online', () => setConnection(true));
navigator.serviceWorker?.addEventListener('message', event => {
  if (event.data?.type === 'NETWORK_STATUS' && typeof event.data.online === 'boolean') setConnection(event.data.online);
});
// Image failures must explain what happened rather than leave a broken-image symbol.
document.addEventListener('error', event => {
  const img=event.target;
  if (!(img instanceof HTMLImageElement) || !img.closest('.source-question,.question-figure,.choice,#image-scroll')) return;
  const container=img.closest('figure') || img.parentElement;
  if (container.querySelector('.image-error')) return;
  img.hidden=true;
  const message=document.createElement('p'); message.className='page-note image-error'; message.setAttribute('role','status');
  message.textContent=online ? '問題画像を読み込めませんでした。接続を確認して開き直してください。'
    : 'この問題画像はまだ保存されていません。オンラインで一度開いてください。';
  container.append(message);
}, true);
function question(id) { const q=questionIndex.get(id)||(planner?.allAttempts()||state.attempts).find(a=>a.questionId===id&&a.questionSnapshot)?.questionSnapshot,override=Object.hasOwn(state.overrides,id)?state.overrides[id]:null;return q?{...q,...(override||{}),...(override?{enrichment:'personal',hintStatus:'individual'}:{})}:null; }
function current() { return state.attempts.find(a => a.id === state.currentId); }

function materialUpdateAvailable(a) {
  if(!questionIndex.has(a.questionId))return false;
  const q=question(a.questionId);
  if(!q?.hints)return false;
  const previous=a.materialSnapshot;
  return hintKind(previous)!==hintKind(q) || ['enrichment','summary','explanation','takeaway'].some(k=>previous[k]!==q[k]) || JSON.stringify(previous.hints)!==JSON.stringify(q.hints) || JSON.stringify(previous.choiceReasons || [])!==JSON.stringify(q.choiceReasons);
}
async function useLatestHints() {
  const old=current(); if(!old || !materialUpdateAvailable(old)) return;
  const carrySelection=!complete(old), selected=old.selected, selectedId=old.selectedChoiceId??old.questionSnapshot?.choices[selected]?.id, confidence=old.confidence;
  const created=await start(old.questionId);if(!created)return;
  // A new attempt keeps the previous hint history intact; unseen new hints start closed.
  if(carrySelection) { const a=current();const index=selectedId?a.questionSnapshot.choices.findIndex(c=>c.id===selectedId):selected;selectAnswer(a,index);a.confidence=confidence;save();render(); }
}
function notice(message) { $('#notice').textContent = message; $('#notice').hidden = !message; }
let saves=Promise.resolve(),saveVersion=0,recordMaintenance=null;
function save(options={}) {
  if(recordMaintenance)return Promise.resolve(false);
  rebuildProgress();const version=++saveVersion;
  if (corruptRaw !== null) { notice('保存データを読み取れませんでした。表示・データから書き出すか、読み込み・初期化で復旧できます。元の記録は上書きしていません。'); return Promise.resolve(false); }
  $('#save-state').textContent='保存中…';
  const operation=store.write(state,options).then(async result=>{
    for(const [before,after] of Object.entries(result.remap)){
      const local=state.attempts.find(a=>a.id===before);if(local){local.id=after;local.continuationOf=before;local.continuedAt=result.attempts.find(a=>a.id===after)?.continuedAt||now();}
      if(state.currentId===before)state.currentId=after;state.session.attemptIds=state.session.attemptIds.map(id=>id===before?after:id);
    }
    const ids=new Set(state.attempts.map(a=>a.id));for(const a of result.attempts)if(!ids.has(a.id)){state.attempts.push(a);ids.add(a.id);}
    state.attempts.sort((a,b)=>a.startedAt.localeCompare(b.startedAt)||a.id.localeCompare(b.id));rebuildProgress();
    if(version===saveVersion){storageOK=true;$('#save-state').textContent='この端末に保存済み';}
    if(result.learningChanges?.length){await learning?.accept(result.learningChanges);account?.learningChanged();}
    account?.changed();
    return true;
  }).catch(error=>{
    if(version===saveVersion){storageOK=false;$('#save-state').textContent='保存できていません';notice(`${error.message || 'ブラウザに保存できません。'} いまの学習は続けられます。「表示・データ」から記録を書き出してください。`);}
    return false;
  });saves=operation;return operation;
}

function reviewQuestions() { return practicePool({qualification,questions:base}).map(q=>({q, info:reviewInfo(q)})).filter(x=>x.info && (x.info.needs || x.info.isDue)).sort((a,b)=>Number(b.info.isDue)-Number(a.info.isDue)||a.info.due-b.info.due); }
function topics() { return [...new Set(base.map(q => q.topic))]; }
function readNote(topic){const id=qualification.topics.find(t=>t.name===topic)?.id;return Object.hasOwn(state.readingNotes,id)?state.readingNotes[id]:Object.hasOwn(state.readingNotes,topic)?state.readingNotes[topic]:'';}
function scopeOf(session){return {topicId:session.topicId||qualification.topics.find(t=>t.name===session.topic)?.id||null,topicIds:session.topicIds||[],examPartId:session.examPartId||null,examPartIds:session.examPartIds||[]};}
function eligible(session){return practicePool({qualification,questions:base,scope:scopeOf(session),available:usableOffline,practiceAllowed:q=>allowsQuestion(q,session.paperMode||'all',studyContext,state.settings.deskQuestionIds)});}
function topicPool(topic,topicId=null,examPartId=null,paperMode=state.settings.paperMode){return practicePool({qualification,questions:base,scope:{topicId:topicId||qualification.topics.find(t=>t.name===topic)?.id||null,examPartId},available:usableOffline,practiceAllowed:q=>allowsQuestion(q,paperMode,studyContext,state.settings.deskQuestionIds)});}
function fieldAction(topicId,examPartId=null,paperMode=state.settings.paperMode){return chooseFieldAction({qualification,questions:base,attempts:state.attempts,reviewInfo,topicId,examPartId,paperMode,available:usableOffline,practiceAllowed:q=>allowsQuestion(q,paperMode,studyContext,state.settings.deskQuestionIds),paperless:paperMode==='paperless',online,excludedQuestionIds:learning?.deferredIds()||[],entryModeFor:resumeMode});}
function sessionCount(){return state.session.attemptIds.filter(id=>complete(state.attempts.find(a=>a.id===id)||{})).length;}
function visitedQuestions(session){
 const pool=eligible(session),ids=new Set(pool.map(q=>q.id)),seen=new Set();
 for(const id of session.attemptIds){const a=state.attempts.find(a=>a.id===id);if(a&&ids.has(a.questionId))seen.add(a.questionId);if(session.intent!=='review'&&seen.size===pool.length)seen.clear();}
 return [...seen];
}
function pickQuestion(session=state.session){return selectPractice({qualification,questions:base,attempts:planner?.allAttempts()||state.attempts,reviewInfo,scope:scopeOf(session),available:usableOffline,practiceAllowed:q=>allowsQuestion(q,session.paperMode||'all',studyContext,state.settings.deskQuestionIds),intent:session.intent||'normal',excludedQuestionIds:[...(session.excludedQuestionIds||[]),...(learning?.deferredIds()||[])],visitedQuestionIds:visitedQuestions(session)});}
function hasFreshTopicQuestion(){return pickQuestion().kind==='question';}

function render(focus = true, preserveY = null) {
  const memo=!focus&&document.activeElement?.matches('input[data-reading-topic]')?{topic:document.activeElement.dataset.readingTopic,start:document.activeElement.selectionStart,end:document.activeElement.selectionEnd}:null;
  document.documentElement.classList.toggle('large-text', state.settings.largeText);
  $('#large-text').checked = state.settings.largeText;
  document.querySelectorAll('.nav-item').forEach(b=>{ const active = b.dataset.view === (state.view==='study'?'home':['planning','diagnostics','diagnostic','review'].includes(state.view)?'history':state.view==='materials'||state.view==='flashcards'?'topics':state.view); b.classList.toggle('active',active); active ? b.setAttribute('aria-current','page') : b.removeAttribute('aria-current'); });
  if(state.view==='home'){displayedEntryActions=entryActions();displayedNextAction=displayedEntryActions[state.settings.lastEntry]||nextAction();}
  main.innerHTML = state.view==='flashcards'&&cards?cards.html():state.view==='planning'&&planner ? planner.views().planningHTML() : state.view==='diagnostics'&&planner ? planner.views().diagnosticsHTML() : state.view==='diagnostic'&&planner ? planner.views().diagnosticHTML() : state.view==='study' && current() ? views().studyHTML() : state.view==='topics' ? views().topicsHTML() : state.view==='review' ? views().reviewHTML() : state.view==='history' ? views().historyHTML() : state.view==='materials' ? views().materialsHTML() : views().homeHTML();
  if(state.view==='planning')planner?.restoreDrafts();
  if(memo){const input=[...main.querySelectorAll('input[data-reading-topic]')].find(el=>el.dataset.readingTopic===memo.topic);if(input){input.focus({preventScroll:true});input.setSelectionRange(memo.start,memo.end);}}
  if (focus) { main.focus({preventScroll:true}); window.scrollTo(0, preserveY ?? 0); }
}
let navigation=0;
function go(view,options={}) { if(!store)return;
 if(view==='topics'&&state.view!=='topics')state.settings.paperMode=state.settings.lastEntry;
 if(view==='history'){fieldMode='learning';fieldPartId=null;}
 if(view==='review'){reviewTopicId=options.reviewTopicId||null;reviewPartId=options.reviewPartId||null;}
 if(view!=='home'){displayedNextAction=null;displayedEntryActions=null;}navigation++;main.setAttribute('aria-busy','false');state.view=view; learning?.apply();save(); render();
}
let opening=false;
async function start(id, newSession = false, options = {}) {
  if(opening)return;opening=true;const token=++navigation;main.setAttribute('aria-busy','true');notice('教材を読み込んでいます。');
  try {
  let session=newSession?{attemptIds:[],topic:options.topic||null,topicId:qualification.topics.find(t=>t.name===options.topic)?.id||null,topicIds:options.topicIds||[],examPartId:options.examPartId||null,examPartIds:options.examPartIds||[],paperMode:options.paperMode||state.settings.paperMode,intent:options.intent||(options.topic?'topic':'normal'),excludedQuestionIds:[],returnView:options.returnView||'home',returnRunId:options.returnRunId||null,...(options.returnSession?{returnSession:options.returnSession,returnAttemptId:options.returnAttemptId||null}:{})}:state.session;
  if(id && session.topic && (session.topicId?question(id)?.topicId!==session.topicId:question(id)?.topic!==session.topic)) session={...session,attemptIds:[],topic:null,topicId:null};
  if(id&&session.examPartId&&(question(id)?.examPartId||qualification.defaultExamPartId)!==session.examPartId)session={...session,attemptIds:[],topic:null,topicId:null,examPartId:null};
  if(session.topicId)session={...session,topic:qualification.topics.find(t=>t.id===session.topicId)?.name||session.topic};
  const selection=id?{kind:'question',questionId:id}:pickQuestion(session),q=selection.kind==='question'?question(selection.questionId):null;
  if(!q){notice(selection.reason||'この範囲には現在利用できる問題がありません。');return;}
  if(!practicePool({qualification,questions:[q]}).length){notice('この問題のパートは通常演習に対応していません。');return;}
  if(!allowsQuestion(q,session.paperMode||state.settings.paperMode,studyContext,state.settings.deskQuestionIds)){notice(`この問題は「${session.paperMode==='paperless'?'身軽に1問':'書いて考える1問'}」の候補ではありません。ホームで「おまかせで1問」を選ぶと、すべての問題を解けます。記録は変更していません。`);return;}
  if(!usableOffline(q)) {notice('この問題はまだオフライン用に保存されていません。接続後に開いてください。');return;}
  await content.ensure(q.id);if(token!==navigation)return;
  const full=question(q.id);
  state.session=session;if(session.intent!=='direct'){state.settings.lastEntry=session.paperMode||state.settings.paperMode;if(newSession)state.settings.paperMode=state.settings.lastEntry;}
  const old = current(); if(old && !complete(old)) { old.status='postponed'; old.updatedAt=now(); }
  const a=createAttempt(full,{topic:state.session.topic,readingNote:state.session.topic?readNote(state.session.topic):'',contentRevision:state.overrides[q.id]?.revision||'original'});
  a.entryMode=session.paperMode||state.settings.paperMode;a.practiceScope={...scopeOf(session),intent:session.intent||'normal',paperMode:a.entryMode,returnView:session.returnView||'home',returnRunId:session.returnRunId||null};a.deferred=false;state.attempts.push(a); state.currentId=a.id; state.session.attemptIds.push(a.id); state.view='study';
  const clears=learning?.clearDeferredOperations(q.id)||[];if(clears.length){for(const old of state.attempts)if(old.questionId===q.id)old.deferred=false;state.session.excludedQuestionIds=state.session.excludedQuestionIds.filter(id=>id!==q.id);}
  await save({learningOperations:[learning?.contextOperation(a),...clears].filter(Boolean)});render();return a;
  }catch(error){notice(error.message);}finally{opening=false;if(token===navigation)main.setAttribute('aria-busy','false');if(token===navigation&&$('#notice').textContent==='教材を読み込んでいます。')notice('');}
}
async function resume(id,entryMode=null) {
 const token=++navigation,boundStore=store,identity=await boundStore.identity(),source=await boundStore.remoteDevice(id);if(token!==navigation||boundStore!==store)return;
 if(!complete(state.attempts.find(a=>a.id===id)||{})&&identity.owner.startsWith('uid:')&&source&&source!==identity.deviceId&&!learning?.hasContext(id)&&learning?.status()!=='synced')await account?.prepareLearning?.();
 if(token!==navigation||boundStore!==store)return;learning?.apply();
 const runId=planner?.derivedRun(id);if(runId){await planner.action({dataset:{action:'resume-diagnostic',id:runId}});const detail=document.querySelector(`[data-diagnostic-slot="${id}"]`);if(detail){detail.open=true;detail.scrollIntoView({block:'start'});}return;}
 const target=state.attempts.find(a=>a.id===id);if(!target)return;if(!complete(target)&&!practicePool({qualification,questions:[question(target.questionId)||target.questionSnapshot]}).length){notice('この記録のパートは通常演習に対応していません。回答とヒントは保持しています。');return;}const savedMode=target.entryMode||target.practiceScope?.paperMode,mode=resumeMode(target);if(!complete(target)&&!allowsQuestion(question(target.questionId)||target.questionSnapshot,mode,studyContext,state.settings.deskQuestionIds)){notice('この問題は今の入口の候補ではありません。分野画面で「おまかせ」を選んで、記録から再開できます。記録はそのまま残っています。');return;}main.setAttribute('aria-busy','true');
 try {
  if(questionIndex.has(target.questionId))await content.ensure(target.questionId);if(token!==navigation)return;
  const old=current();if(old&&old.id!==id&&!complete(old))old.status='postponed';
  let a=state.attempts.find(a=>a.id===id);if(!a)return;
  // A synchronized checkpoint belongs to its creating device. Continue under
  // a fresh UUID so two devices can both answer without overwriting each other.
  const targetStore=store,identity=await targetStore.identity(),remote=(await targetStore.remoteDevice?.(id));if(token!==navigation||targetStore!==store)return;
  if(!complete(a)&&identity.owner.startsWith('uid:')&&remote&&remote!==identity.deviceId&&learning&&learning.status()!=='synced'&&!learning.hasContext(id)){notice('別端末の再開範囲をまだ取得できません。表示・データの同期状態を確認してください。回答・ヒントは保持しています。');return;}
  if(!complete(a)&&remote&&remote!==identity.deviceId){a={...structuredClone(a),id:crypto.randomUUID(),continuationOf:id,continuedAt:now(),scrollY:0};state.attempts.push(a);id=a.id;}
  state.currentId=id;if(a.practiceScope?.intent!=='direct'){state.settings.paperMode=mode;state.settings.lastEntry=mode;}a.entryMode=mode;
  const saved=a.practiceScope||{intent:a.topic?'topic':'normal',topicId:a.topicId||null,topicIds:[],examPartId:a.questionSnapshot?.examPartId||qualification.defaultExamPartId,examPartIds:[],paperMode:mode,returnView:'home'};
  if(!complete(a))a.practiceScope={...saved,paperMode:mode};
  const same=state.session.attemptIds.includes(id)&&(state.session.paperMode||'all')===mode&&(state.session.intent||'normal')===saved.intent&&['topicId','examPartId'].every(key=>(state.session[key]||null)===(saved[key]||null))&&['topicIds','examPartIds'].every(key=>JSON.stringify(state.session[key]||[])===JSON.stringify(saved[key]||[]));
  state.session={...(same?state.session:{}),...saved,attemptIds:same?state.session.attemptIds:[id],topic:qualification.topics.find(t=>t.id===saved.topicId)?.name||a.topic||null,paperMode:mode,excludedQuestionIds:(same?state.session.excludedQuestionIds||[]:[]).filter(q=>q!==a.questionId)};
  if(!complete(a)){a.status='in_progress';a.deferred=false;}state.view='study';const clears=learning?.clearDeferredOperations(a.questionId)||[];if(clears.length){for(const old of state.attempts)if(old.questionId===a.questionId)old.deferred=false;state.session.excludedQuestionIds=state.session.excludedQuestionIds.filter(q=>q!==a.questionId);}
  await save({learningOperations:[!complete(a)?learning?.contextOperation(a):null,...clears].filter(Boolean)});if(token===navigation){render(true,a.scrollY||0);if(savedMode&&mode!==savedMode)notice('紙ペン指定が変わったため、この中断は「おまかせ」で再開しました。回答・ヒント・分野指定は保持しています。');else if(!savedMode)notice('保存された回答・ヒントで再開しました。入口の情報がない記録は「おまかせ」で、この問題のパートから続けます。保存された分野指定があれば保持します。');return a;}
 }catch(error){notice(error.message);}finally{if(token===navigation)main.setAttribute('aria-busy','false');}
}

function finish(status) {
  const a=current(); if(!a || complete(a)) return;
  finalizeAttempt(a,status);const clears=learning?.clearDeferredOperations(a.questionId)||[];if(clears.length){for(const old of state.attempts)if(old.questionId===a.questionId)old.deferred=false;state.session.excludedQuestionIds=(state.session.excludedQuestionIds||[]).filter(q=>q!==a.questionId);}save({learningOperations:clears});render(false);
  $('#result-heading')?.focus({preventScroll:true}); $('#result')?.scrollIntoView({block:'start'});
}

function openImage(id,index) {
  const q=question(id),src=q.sourceImages[index];if(!src)return;
  $('#image-title').textContent=`${examLabel(q)} 問${q.number}`;
  $('#image-scroll').innerHTML=`<img src="${src}" alt="${esc(q.source)}の拡大画像" style="width:${Math.max(900,q.imageSizes[index].width)}px">`;
  $('#image-dialog').showModal();$('#image-scroll').scrollTo(0,0);
}
function download(data,name,raw=false) { const url=URL.createObjectURL(new Blob([raw?data:JSON.stringify(data,null,2)],{type:'application/json'})); const a=document.createElement('a'); a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000); }
async function openEditor(id) {
  try{await content.ensure(id);}catch(error){notice(error.message);return;}
  editId=id; const q=question(id); $('#editor-title').textContent=`${q.title}：教材を編集`;
  $('#editor-fields').innerHTML=q.hints.map((h,i)=>`<label class="editor-field"><span>ヒント${i+1}：${esc(h.title)}</span><textarea name="hint${i}" required maxlength="10000" rows="3">${esc(h.text)}</textarea></label><label class="confidence"><input type="checkbox" name="reveal${i}" ${h.revealsAnswer?'checked':''}>このヒントは答えを含む</label>`).join('')+[['summary','要約'],['explanation','解説'],['takeaway','要点']].map(([key,label])=>`<label class="editor-field"><span>${label}</span><textarea name="${key}" required maxlength="20000" rows="${key==='explanation'?6:3}">${esc(q[key])}</textarea></label>`).join('');
  $('#editor-dialog').showModal();
}

main.addEventListener('click',async e=>{
  const el=e.target.closest('[data-action],[data-view]'); if(!el) return;
  if(el.dataset.view) { if(['all','paperless','desk'].includes(el.dataset.paperMode))state.settings.paperMode=el.dataset.paperMode;go(el.dataset.view,{reviewTopicId:el.dataset.reviewTopicId,reviewPartId:el.dataset.reviewPartId});if(el.dataset.openAi)await planner?.action({dataset:{action:'open-ai'}});return; }
  const action=el.dataset.action; const a=current();
  try {
  if(await cards?.action(el))return;
  if(await planner?.action(el))return;
  if(action==='entry-start'||action==='entry-resume'){const mode=el.dataset.paperMode;if(!['all','paperless','desk'].includes(mode))return;if(mode!=='all'&&!studyContext)studyContext=await content.loadStudyContext();if(action==='entry-resume')await resume(el.dataset.id,mode);else await start(el.dataset.id,true,{topic:qualification.topics.find(t=>t.id===el.dataset.topicId)?.name||null,examPartId:el.dataset.partId||null,paperMode:mode});}
  else if(action==='paper-mode'){const mode=['paperless','desk'].includes(el.dataset.mode)?el.dataset.mode:'all',token=++navigation;if(mode!=='all'){studyContext=await content.loadStudyContext();if(token!==navigation)return;}state.settings.paperMode=mode;if(await save())notice('');render(false);}
  else if(action==='clear-desk'){const before=state.settings.deskQuestionIds;state.settings.deskQuestionIds=[];if(!await save({learningOperations:before.map(questionId=>learning?.operation('desk',{questionId,value:false})).filter(Boolean)})){state.settings.deskQuestionIds=before;render(false);return;}render(false);notice('机指定を解除しました。回答記録は保持しています。');}
  else if(action==='desk-later'&&a&&!complete(a)){const before={attempt:structuredClone(a),deskQuestionIds:state.settings.deskQuestionIds};state.settings.deskQuestionIds=[...new Set([...state.settings.deskQuestionIds,a.questionId])];a.status='postponed';a.entryMode='desk';if(a.practiceScope)a.practiceScope.paperMode='desk';a.updatedAt=now();state.currentId=null;if(!await save({learningOperations:[learning?.operation('desk',{questionId:a.questionId,value:true}),learning?.contextOperation(a)].filter(Boolean)})){Object.assign(a,before.attempt);state.settings.deskQuestionIds=before.deskQuestionIds;state.currentId=a.id;render(false);return;}go('home');notice('紙なしの候補から外して中断しました。回答候補とヒントは保存済みです。「書いて考える1問」から再開できます。');}
  else if(action==='start-session') {const candidate=nextAction(false,state.settings.paperMode,true);if(candidate.kind==='resume'){await resume(candidate.attemptId);return;}if(candidate.kind==='question')await start(candidate.questionId,true,{topic:qualification.topics.find(t=>t.id===candidate.scope.topicId)?.name||null,examPartId:candidate.scope.examPartId,paperMode:el.dataset.paperMode||state.settings.paperMode});else notice(candidate.reason);}
  else if(action==='field-mode'){fieldMode=el.dataset.mode==='diagnostic'?'diagnostic':'learning';render(false);document.querySelector(`[data-action=field-mode][data-mode=${fieldMode}]`)?.focus({preventScroll:true});}
  else if(action==='field-focus'){go('history');document.getElementById('record-field-'+el.dataset.topicId)?.scrollIntoView({block:'start'});}
  else if(action==='field-review'){if(qualification.topics.some(t=>t.id===el.dataset.topicId))go('review',{reviewTopicId:el.dataset.topicId,reviewPartId:el.dataset.partId});}
  else if(action==='field-practice'){if(!qualification.topics.some(t=>t.id===el.dataset.topicId))return;const mode=el.dataset.paperMode||state.settings.lastEntry;if(mode!=='all'&&!studyContext)studyContext=await content.loadStudyContext();if(el.dataset.resumeId)await resume(el.dataset.resumeId,mode);else await start(el.dataset.id||null,true,{topic:el.dataset.topic,examPartId:el.dataset.partId||null,paperMode:mode,returnView:state.view});}
  else if(action==='topic-session') { if(!topics().includes(el.dataset.topic))return;start(null,true,{topic:el.dataset.topic,examPartId:el.dataset.partId||null,paperMode:el.dataset.paperMode||state.settings.paperMode}); }
  else if(action==='zoom') openImage(el.dataset.id,Number(el.dataset.image));
  else if(action==='catalog-page'){catalog.page=Number(el.dataset.page);render();}
  else if(action==='reset-filters'){catalog={year:'',season:'',topic:'',query:'',enriched:false,page:1};render();}
  else if(action==='plan-start'){const phase=activePhase(planner?.plan());if(!phase){notice('現在の期間の計画はありません。ホームから1問始められます。');return;}await start(null,true,{intent:'topic',topicIds:phase.focusTopicIds,examPartIds:phase.examPartIds,paperMode:el.dataset.paperMode||state.settings.paperMode});}
  else if(action==='review-start')await start(el.dataset.id,true,{intent:'review',topic:qualification.topics.find(t=>t.id===reviewTopicId)?.name||null,examPartId:reviewPartId,paperMode:'all',returnView:'review'});
  else if(action==='start'){const direct=state.session.intent==='direct'&&state.view==='study',returnView=direct?state.session.returnView:state.view==='study'?'study':state.view,returnSession=state.view==='study'?(direct?state.session.returnSession:structuredClone(state.session)):null,returnAttemptId=direct?state.session.returnAttemptId:state.currentId;await start(el.dataset.id,true,{intent:'direct',paperMode:'all',returnView,returnSession,returnAttemptId,returnRunId:state.currentRunId});}
  else if(action==='direct-return'){const session=state.session,old=current();if(old&&!complete(old)){old.status='postponed';old.updatedAt=now();}if(session.returnSession){state.session=session.returnSession;const target=state.attempts.find(a=>a.id===session.returnAttemptId);if(target&&!complete(target))await resume(target.id);else {state.currentId=null;const next=pickQuestion();if(next.kind==='question')await start();else {go(state.session.intent==='review'?'review':'home');notice(next.reason);}}}else {state.currentId=null;if(session.returnRunId)state.currentRunId=session.returnRunId;if(session.returnView==='flashcards')await cards.action({dataset:{action:'cards-open'}});else go(session.returnView==='study'?'home':session.returnView||'home');}}

  else if(action==='resume') await resume(el.dataset.id);
  else if(action==='latest-hints') await useLatestHints();
  else if(action==='next') start();
  else if(action==='postpone'&&a&&!complete(a)){const before={status:a.status,deferred:a.deferred,updatedAt:a.updatedAt,excludedQuestionIds:state.session.excludedQuestionIds};a.status='postponed';a.deferred=true;a.updatedAt=now();state.session.excludedQuestionIds=[...new Set([...(state.session.excludedQuestionIds||[]),a.questionId])];state.currentId=null;if(!await save({learningOperations:[learning?.operation('deferred',{questionId:a.questionId,value:true})].filter(Boolean)})){Object.assign(a,{status:before.status,deferred:before.deferred,updatedAt:before.updatedAt});state.currentId=a.id;state.session.excludedQuestionIds=before.excludedQuestionIds||[];render(false);return;}if(state.session.intent==='direct'){go(state.session.returnView==='study'?'home':state.session.returnView||'home');notice('先送りした問題は記録から再開できます。');}else if(pickQuestion().kind==='question')await start();else {const reason=pickQuestion().reason;go('home');notice(reason);}}
  else if(['pause','end'].includes(action)) { if(a&&!complete(a)) {a.status='postponed';a.updatedAt=now();} state.currentId=null;go('home'); }
  else if(action==='hint'&&a) {
    if(!openHint(a))return;
    const y=window.scrollY;save();render(false);window.scrollTo(0,y); const shown=document.querySelectorAll('.hint-box');shown[shown.length-1]?.focus({preventScroll:true});
  }
  else if(action==='submit'&&a&&!complete(a)&&a.selected!==null) { finish(gradeAttempt(a,question(a.questionId).answer)); }
  else if(action==='reveal'&&a&&!complete(a)) { a.answerViewedBefore=true;finish('revealed'); }
  else if(action==='edit') openEditor(el.dataset.id);
  else if(action==='export-materials') {await content.loadAll();download(base.map(q=>question(q.id)),`${qualification.id}-study-questions.json`);}
  }catch(error){notice(error.message);}
});
document.querySelectorAll('header [data-view], .sidebar [data-view]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();go(b.dataset.view);}));
main.addEventListener('toggle',e=>planner?.toggle(e.target),true);
main.addEventListener('input',e=>{if(planner?.input(e.target))return;if(e.target.closest('#catalog-form')){const f=new FormData($('#catalog-form'));catalog={year:String(f.get('year')),season:String(f.get('season')),topic:String(f.get('topic')),query:String(f.get('query')),enriched:f.has('enriched'),page:1};$('#catalog-results').innerHTML=views().catalogRowsHTML();return;}if(e.target.dataset.readingTopic){const topic=qualification.topics.find(t=>t.name===e.target.dataset.readingTopic);state.readingNotes[topic?.id||e.target.dataset.readingTopic]=e.target.value.slice(0,200);save();}});
main.addEventListener('change',async e=>{
  if(e.target.id==='import-cards'){try{await cards.importFile(e.target.files[0]);}catch(error){notice(error.message+' 現在の記録は変更していません。');}finally{e.target.value='';}return;}
  if(await cards?.change(e.target))return;
  if(e.target.name==='topic-part'){topicPartId=e.target.value||null;render(false);return;}
  if(e.target.name==='field-part'){fieldPartId=e.target.value||null;render(false);return;}
  if(await planner?.change(e.target))return;
  if(e.target.closest('#catalog-form'))return;
  const a=current();if(!a||complete(a))return;
  if(e.target.name==='answer') {selectAnswer(a,Number(e.target.value),question(a.questionId));document.querySelectorAll('.choice').forEach(l=>l.classList.toggle('selected',$('input',l).checked)); $('[data-action="submit"]').disabled=false;}
  else if(e.target.id==='confidence') a.confidence=e.target.checked;
  a.updatedAt=now();save();
});
$('#catalog-form')?.addEventListener('submit',e=>e.preventDefault());
main.addEventListener('submit',async e=>{if(['catalog-form','exam-form','phase-form'].includes(e.target.id)||e.target.dataset.planningForm)e.preventDefault();await planner?.submit(e.target);});
$('#close-image').addEventListener('click',()=>$('#image-dialog').close());
$('#image-zoom-in').addEventListener('click',()=>{const img=$('#image-scroll img');img.style.width=`${Math.min(4000,img.clientWidth*1.25)}px`;});
$('#image-zoom-out').addEventListener('click',()=>{const img=$('#image-scroll img');img.style.width=`${Math.max(600,img.clientWidth/1.25)}px`;});
$('#settings-button').addEventListener('click',()=>$('#settings-dialog').showModal());
$('#large-text').addEventListener('change',e=>{state.settings.largeText=e.target.checked;save();render(false);});
$('#export-state').addEventListener('click',async()=>{await saves;download(corruptRaw??{...state,workspaceBackup:planner?.backup(),learningBackup:learning?.backup()},`${qualification.id}-study-record-${day(now())}.json`,corruptRaw!==null);});
// Full record replacement is guest-only. Keep navigation, background saves and
// owner changes behind this short maintenance barrier, then display committed data.
async function maintainRecords(operation){
 if(recordMaintenance)throw new Error('記録の取り込み中です。完了してから操作してください。');
 let release;recordMaintenance=new Promise(resolve=>release=resolve);
 navigation++;
 const previousInert=[main.inert,document.querySelector('.sidebar').inert],ids=['import-state','export-state','clear-state','large-text','google-login','google-logout','sync-now','import-guest'],disabled=ids.map(id=>[id,$('#'+id)?.disabled]);
 main.inert=true;document.querySelector('.sidebar').inert=true;main.setAttribute('aria-busy','true');for(const [id] of disabled)if($('#'+id))$('#'+id).disabled=true;
 clearTimeout(scrollTimer);
 try{return await operation();}finally{
  main.inert=previousInert[0];document.querySelector('.sidebar').inert=previousInert[1];main.setAttribute('aria-busy','false');for(const [id,value] of disabled)if($('#'+id))$('#'+id).disabled=value;
  recordMaintenance=null;release();
 }
}
$('#import-state').addEventListener('change',async e=>{
 const file=e.target.files[0];if(!file)return;
 try{await maintainRecords(async()=>{
  const target=store,identity=await target.identity();if(identity.owner.startsWith('uid:'))throw new Error('学習記録の置き換えはログアウトしてから行ってください。');
  if(file.size>64*1024*1024)throw new Error('ファイルが大きすぎます。64MB以下の学習記録を選んでください。');
  const candidate=validateState(JSON.parse(await file.text())),workspaceBackup=candidate.workspaceBackup;planner?.validateBackup(workspaceBackup);learning?.validateBackup(candidate.learningBackup,candidate.attempts);
  if((state.attempts.length||corruptRaw!==null)&&!confirm('通常演習の記録と教材編集を、ファイルの内容で置き換えます。計画・診断は追加し、既存のものは残します。先に書き出して保管してください。読み込みますか？'))return;
  await saves;if(store!==target)throw new Error('保存先が変わりました。記録は変更していません。');
  const learningOperations=learning?.restoreOperations(candidate.learningBackup)||[];delete candidate.workspaceBackup;delete candidate.learningBackup;if(candidate.view==='flashcards')candidate.view='home';
  $('#save-state').textContent='保存中…';
  try{await target.write(candidate,{replace:true,learningOperations});await learning?.bind();}catch(error){$('#save-state').textContent=storageOK?'この端末に保存済み':'保存できていません';throw new Error('学習記録を取り込めませんでした。現在の記録と計画は変更していません。 '+error.message);}
  state=candidate;learning?.apply();corruptRaw=null;storageOK=true;saveVersion++;rebuildProgress();$('#save-state').textContent='この端末に保存済み';notice('');
  let result;
  try{result=await planner?.restoreBackup(workspaceBackup);}catch(error){render();$('#settings-status').textContent='通常演習の記録は読み込み済みです。受験日・計画・診断は取り込めませんでした。同じファイルを選んで再試行できます。 '+error.message;return;}
  if(qualification.studyContext)await content.loadStudyContext().then(value=>studyContext=value).catch(error=>notice(error.message));render();
  const details=[];if(result?.plan==='restored')details.push('受験日・計画を追加しました。');if(result?.plan==='retained')details.push('既存の受験日・計画は保持しました。');if(workspaceBackup?.runs.length)details.push(`診断${result.diagnosticsAdded}件を追加、${result.diagnosticsRetained}件は登録済みです。`);
  $('#settings-status').textContent='学習記録を読み込みました。'+(details.length?' '+details.join(' '):'');
 });}catch(error){$('#settings-status').textContent=error instanceof SyntaxError?'JSONを読み取れませんでした。現在の記録は変更していません。':error.message;}
 finally{e.target.value='';}
});
$('#clear-state').addEventListener('click',async()=>{if(!confirm('このブラウザの通常演習・診断の記録を削除します。単語帳・受験日・計画・教材の編集は残します。よろしいですか？'))return;await saves;const {settings,overrides}=state;corruptRaw=null;state={...makeState(),settings,overrides};notice('');await save({replace:true});await learning?.bind();await planner?.clearDiagnostics();render();$('#settings-status').textContent=storageOK?'通常演習・診断の学習記録を削除しました。受験日と計画は残しています。':'記録を初期化しましたが、保存に失敗しました。ブラウザの保存設定を確認してください。';});
$('#close-editor').addEventListener('click',()=>$('#editor-dialog').close());
$('#editor-form').addEventListener('submit',e=>{e.preventDefault();const f=new FormData(e.target);const q=question(editId);const changes={enrichment:'personal',hintStatus:'individual',hints:q.hints.map((h,i)=>({...h,text:String(f.get(`hint${i}`)).trim(),revealsAnswer:f.has(`reveal${i}`)})),revision:now()};for(const k of ['summary','explanation','takeaway'])changes[k]=String(f.get(k)).trim();if(changes.hints.some(h=>!h.text)||['summary','explanation','takeaway'].some(k=>!changes[k])){alert('空欄を埋めてから保存してください。');return;}state.overrides[editId]=changes;save();$('#editor-dialog').close();render(false);});
$('#reset-material').addEventListener('click',()=>{if(!confirm('この問題のヒントと解説を、初期教材に戻しますか？'))return;delete state.overrides[editId];save();$('#editor-dialog').close();render(false);});
let scrollTimer;
window.addEventListener('scroll',()=>{if(state.view!=='study')return;clearTimeout(scrollTimer);const attemptId=state.currentId;scrollTimer=setTimeout(()=>{if(state.view!=='study'||state.currentId!==attemptId)return;const a=current();if(a){a.scrollY=window.scrollY;save();}},200);},{passive:true});
function saveScroll(){if(state.view==='study'&&current()){current().scrollY=window.scrollY;save();}}
window.addEventListener('pagehide',saveScroll);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveScroll();});
async function switchOwner(owner,{restore=false}={}){
 if(recordMaintenance)await recordMaintenance;
 const identity=await store.identity();if(identity.owner===(owner||`guest:${identity.deviceId}`))return;
 main.inert=true;document.querySelector('.sidebar').inert=true;
 const controls=['import-state','export-state','clear-state','large-text'];controls.forEach(id=>$("#"+id).disabled=true);
 clearTimeout(scrollTimer);navigation++;$('#editor-dialog').close();
 try{
  if(!await save())throw new Error('現在の記録を保存できません。');await saves;
  const next=createLocalStore({qualificationId:qualification.id,rootPath:appRoot.pathname,key:qualification.storageKey,validate:validateState,owner});
  let raw=await next.read(),candidate=raw?validateState(JSON.parse(raw)):makeState();
  if(!raw){candidate.settings={largeText:state.settings.largeText,paperMode:state.settings.paperMode,lastEntry:state.settings.lastEntry,deskQuestionIds:[]};await next.write(candidate);raw=await next.read();}
  await store.close();store=next;state=validateState(JSON.parse(raw));displayedNextAction=null;fieldMode='learning';fieldPartId=null;topicPartId=null;reviewTopicId=null;reviewPartId=null;await cards?.bind();await learning?.bind();await planner?.bind();corruptRaw=null;storageOK=true;editId=null;
  // Explicit account changes open home; restoring the same browser's saved
  // login preserves its own current question and scroll position.
  if(!restore){state.currentId=null;state.view='home';state.session={attemptIds:[],topic:null};}
  if(restore&&state.view==='study'&&current()&&questionIndex.has(current().questionId))await content.ensure(current().questionId).catch(()=>{});
  if(qualification.studyContext)await content.loadStudyContext().then(value=>studyContext=value).catch(error=>notice(error.message));
  if(state.view==='flashcards')await cards.load().catch(error=>{state.view='home';notice(error.message);});
  await save();render(true,state.view==='study'?current()?.scrollY:0);notice('');
  $('#clear-state').closest('details').hidden=!!owner;$('#import-state').closest('label').hidden=!!owner;
 }finally{main.inert=false;document.querySelector('.sidebar').inert=false;controls.forEach(id=>$("#"+id).disabled=false);}
}
function validateSyncAttempt(a){const probe={...makeState(),attempts:[a]};validateState(probe);if(a.qualificationId!==qualification.id||!a.questionSnapshot)throw new Error('同期対象の問題情報がありません。');}
function remoteRecords(records){
 const byId=new Map(state.attempts.map(a=>[a.id,a]));for(const a of records)if(a.id!==state.currentId)byId.set(a.id,a);
 state.attempts=[...byId.values()].sort((a,b)=>a.startedAt.localeCompare(b.startedAt)||a.id.localeCompare(b.id));learning?.apply();rebuildProgress();
 if(records.length&&state.view!=='study'&&state.view!=='planning')render(false);
}
function remoteFork({before,after,data}){
 const a=state.attempts.find(x=>x.id===before);if(a)Object.assign(a,data);else state.attempts.push(data);
 if(state.currentId===before)state.currentId=after;state.session.attemptIds=state.session.attemptIds.map(id=>id===before?after:id);learning?.refresh();account?.learningChanged();rebuildProgress();
}
async function importGuest(uid){
 if((await store.identity()).owner!==`uid:${uid}`)throw new Error('アカウントが変わりました。');
 const guest=createLocalStore({qualificationId:qualification.id,rootPath:appRoot.pathname,key:qualification.storageKey,validate:validateState});
 try{
  const raw=await guest.read();if(!raw){await planner?.importGuest(uid,(await guest.identity()).deviceId);return;}
  const source=validateState(JSON.parse(raw));
  if(!confirm(`ログイン前の${source.attempts.length}件の学習記録と紙ペン・先送り設定を、このGoogleアカウントへ追加します。元の記録は残します。取り込みますか？`))return;
  const identity=await guest.identity(),prefix=`${identity.deviceId}:`,already=new Set(state.attempts.map(a=>a.importedFrom).filter(Boolean));
  const mapping=new Map(await Promise.all(source.attempts.filter(a=>!already.has(prefix+a.id)).map(async a=>[a.id,await guestAttemptId(uid,prefix+a.id)])));
  for(const original of source.attempts){if(!mapping.has(original.id))continue;const a=structuredClone(original);
   if(!a.questionSnapshot){await content.ensure(a.questionId);a.questionSnapshot=createAttempt(question(a.questionId)).questionSnapshot;}
   a.id=mapping.get(original.id);a.qualificationId=qualification.id;a.selectedChoiceId=a.selected===null?null:a.questionSnapshot.choices[a.selected].id;a.importedFrom=prefix+original.id;
   if(a.continuationOf)a.continuationOf=mapping.get(a.continuationOf)||a.continuationOf;
   validateSyncAttempt(a);state.attempts.push(a);
  }
  const guestRows=await guest.learningStore().read(),operations=[];
  for(const row of guestRows){if(row.kind==='context'){const p=structuredClone(row.payload);if(!mapping.has(p.attemptId))continue;p.attemptId=mapping.get(p.attemptId);operations.push(learning?.operation('context',p));}else if(!learning?.hasQuestionSetting(row.kind,row.payload.questionId))operations.push(learning?.operation(row.kind,row.payload));}
  for(const questionId of source.settings.deskQuestionIds)if(!learning?.hasQuestionSetting('desk',questionId))operations.push(learning?.operation('desk',{questionId,value:true}));
  for(const a of source.attempts)if(a.deferred&&!learning?.hasQuestionSetting('deferred',a.questionId))operations.push(learning?.operation('deferred',{questionId:a.questionId,value:true}));
  if(!await save({learningOperations:[...new Map(operations.filter(Boolean).map(op=>[op.id,op])).values()]}))throw new Error('取り込んだ記録を保存できませんでした。');if(learning?.apply()&&!await save())throw new Error('取り込んだ学習設定を保存できませんでした。');await planner?.importGuest(uid,identity.deviceId);render(false);
 }finally{await guest.close();}
}
async function initialize(){
main.inert=true;document.querySelector('.sidebar').inert=true;main.setAttribute('aria-busy','true');$('#settings-button').disabled=true;
try {
  content=await loadCatalog(document.documentElement.dataset.qualification);
  if(content.choose){
    main.innerHTML='<section class="panel"><h1>資格を選ぶ</h1>'+content.qualifications.map(q=>`<p><a class="button secondary" href="${new URL(q.id+'/',appRoot).href}">${esc(q.name)} · ${q.count}問</a></p>`).join('')+'</section>';
    document.querySelector('.sidebar').hidden=true;$('#settings-button').hidden=true;document.querySelector('.app-footer').hidden=true;document.title='ひと問｜資格を選ぶ';return;
  }
  qualification=content.manifest;store=createLocalStore({qualificationId:qualification.id,rootPath:appRoot.pathname,key:qualification.storageKey,validate:validateState});
  document.title=`ひと問｜${qualification.shortName}の学習`;
  document.querySelector('.app-footer span').textContent=`問題出典：${qualification.sourceLabel} · ヒントと解説は独自作成`;
  document.querySelector('.app-footer a').href=new URL(qualification.sourceDoc,appRoot).href;
  online=content.online;base=content.questions;questionIndex=new Map(base.map(q=>[q.id,q]));
  try { const raw=await store.read();if(raw){try{state=validateState(JSON.parse(raw));if(state.session.topicId)state.session.topic=qualification.topics.find(t=>t.id===state.session.topicId)?.name||state.session.topic;}catch{corruptRaw=raw;}} } catch {storageOK=false;notice('このブラウザでは記録を保存できません。学習後に記録を書き出してください。');}
  if(state.view==='study'&&current()&&questionIndex.has(current().questionId))await content.ensure(current().questionId);
  if(qualification.studyContext)await content.loadStudyContext().then(value=>studyContext=value).catch(error=>notice(error.message));
  cards=createCardFeature({qualification,content,getStore:()=>store,getNavigation:()=>navigation,onNavigate:go,onUpdate:()=>{if(state.view==='flashcards')render(false);},onNotice:notice,download,rootPath:appRoot.pathname});await cards.bind().catch(()=>{cards=null;if(state.view==='flashcards')state.view='home';notice('単語帳の記録を保存できません。通常演習は続けられます。');});if(state.view==='flashcards')await cards.load().catch(error=>{state.view='home';notice(error.message);});
  planner=createPlanningFeature({qualification,rootPath:appRoot.pathname,getStore:()=>store,getState:()=>state,getNavigation:()=>navigation,content,base,validateAttempt:validateDiagnosticAttempt,onUpdate:(options={})=>{rebuildProgress();if(state.view!=='study'&&!options.preserveForm)render(false);},onNavigate:(view,runId)=>{if(view==='diagnostic'){const a=current();if(a&&!complete(a))a.status='postponed';state.currentId=null;state.currentRunId=runId;}go(view);},onNotice:notice,onChanged:()=>account?.workspaceChanged(),getReviewCount:()=>reviewQuestions().length,download,getTargetPart:()=>displayedNextAction?.scope?.examPartId||null});
  learning=createLearningFeature({qualification,getStore:()=>store,getState:()=>state,onNotice:notice,onUpdate:()=>{save();if(!['study','planning','flashcards'].includes(state.view))render(false);}});await learning.bind();
  await refreshOfflineQuestions();
  if(state.view==='study'&&!current())state.view='home'; rebuildProgress();render(true,state.view==='study'?current()?.scrollY:0);
  if(corruptRaw!==null)save();else if(!storageOK)$('#save-state').textContent='保存できていません';
  await planner.bind().catch(()=>notice('計画・診断の記録を保存できません。通常演習は続けられます。'));
  initAccountControls({getLearningStore:()=>learning.store(),onLearningRows:learning.onRows,onLearningStatus:learning.onStatus,getWorkspaceStore:()=>planner.store(),onDocuments:planner.onDocuments,onWorkspaceStatus:planner.onStatus,qualificationId:qualification.id,getStore:()=>store,switchOwner,importGuest,validateAttempt:validateSyncAttempt,onRecords:remoteRecords,onFork:remoteFork}).then(value=>{account=value;});
  if(navigator.modelContext?.registerTool) {
    navigator.modelContext.registerTool({name:'get_study_summary',description:'Read counts of local study attempts and review candidates. Does not modify study records.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:async()=>({content:[{type:'text',text:JSON.stringify(planner.summary())}]})});
  }
} catch(error) { main.innerHTML='<div class="empty"><h1>問題を読み込めませんでした。</h1><p>接続を確認し、このページを再読み込みしてください。</p><button class="button primary" id="reload">再読み込み</button></div>';$('#reload').addEventListener('click',()=>location.reload());console.error(error); }finally{main.inert=false;document.querySelector('.sidebar').inert=false;main.setAttribute('aria-busy','false');$('#settings-button').disabled=false;}
}
await initialize();
