import {initPWA, savedAssetURLs} from '../pwa.js';
import {$,esc,now,day,dateText,timeText} from './utils.js';
import {makeState,complete,labels,hintTotal,enriched,hintKind,createAttempt,openHint,gradeAttempt,finalizeAttempt,selectAnswer} from './domain/study.js';
import {createProgress} from './domain/review.js';
import {createViews} from './ui/views.js';
import {createStateValidator} from './storage/validate.js';
import {createLocalStore} from './storage/local.js';
import {loadCatalog,appRoot} from './content/catalog.js';
import {initAccountControls,guestAttemptId} from './sync/account.js';
import {createPlanningFeature} from './features/planning.js';

let store, content, qualification, account, planner;
let questionIndex = new Map(), progress = createProgress([]);
let catalog = {year:'', season:'', topic:'', query:'', enriched:false, page:1};
const PAGE_SIZE=20;
const examLabel=q=>esc(q.packLabel || `${q.year}年 ${qualification.seasonLabels?.[q.season] || q.season}`);
let base = [], state = makeState(), storageOK = true, corruptRaw = null, editId = null;
const main = $('#main');

const validateState=createStateValidator({getQuestions:()=>base,getTopics:topics,getQualification:()=>qualification});
function rebuildProgress(){progress=createProgress(planner?.allAttempts()||state.attempts);}
const latest=id=>progress.latest(id);
const previousAttempt=a=>progress.previousAttempt(a);
const improvement=a=>progress.improvement(a);
const reviewInfo=q=>progress.reviewInfo(q);
function views(){return createViews({state:{...state,attempts:planner?.allAttempts()||state.attempts},workspaceViews:planner?.store()?planner.views():null,base,catalog,PAGE_SIZE,examLabel,question,current,reviewInfo,reviewQuestions,topics,topicPool,latest,previousAttempt,improvement,sessionCount,hasFreshTopicQuestion,materialUpdateAvailable,qualification,readNote});}
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
let saves=Promise.resolve(),saveVersion=0;
function save(options={}) {
  rebuildProgress();const version=++saveVersion;
  if (corruptRaw !== null) { notice('保存データを読み取れませんでした。表示・データから書き出すか、読み込み・初期化で復旧できます。元の記録は上書きしていません。'); return Promise.resolve(false); }
  $('#save-state').textContent='保存中…';
  const operation=store.write(state,options).then(result=>{
    for(const [before,after] of Object.entries(result.remap)){
      const local=state.attempts.find(a=>a.id===before);if(local){local.id=after;local.continuationOf=before;local.continuedAt=result.attempts.find(a=>a.id===after)?.continuedAt||now();}
      if(state.currentId===before)state.currentId=after;state.session.attemptIds=state.session.attemptIds.map(id=>id===before?after:id);
    }
    const ids=new Set(state.attempts.map(a=>a.id));for(const a of result.attempts)if(!ids.has(a.id)){state.attempts.push(a);ids.add(a.id);}
    state.attempts.sort((a,b)=>a.startedAt.localeCompare(b.startedAt)||a.id.localeCompare(b.id));rebuildProgress();
    if(version===saveVersion){storageOK=true;$('#save-state').textContent='この端末に保存済み';}
    account?.changed();
    return true;
  }).catch(error=>{
    if(version===saveVersion){storageOK=false;$('#save-state').textContent='保存できていません';notice(`${error.message || 'ブラウザに保存できません。'} いまの学習は続けられます。「表示・データ」から記録を書き出してください。`);}
    return false;
  });saves=operation;return operation;
}

function reviewQuestions() { return base.map(q=>({q, info:reviewInfo(q)})).filter(x=>x.info && (x.info.needs || x.info.isDue)).sort((a,b)=>Number(b.info.isDue)-Number(a.info.isDue)||a.info.due-b.info.due); }
function topics() { return [...new Set(base.map(q => q.topic))]; }
function readNote(topic){const id=qualification.topics.find(t=>t.name===topic)?.id;return Object.hasOwn(state.readingNotes,id)?state.readingNotes[id]:Object.hasOwn(state.readingNotes,topic)?state.readingNotes[topic]:'';}
function topicPool(topic,topicId=null) {const id=topicId||qualification.topics.find(t=>t.name===topic)?.id||(state.session.topic===topic?state.session.topicId:null);return base.filter(q=>(!topic||(id?q.topicId===id:q.topic===topic))&&usableOffline(q));}
function sessionCount() { return state.session.attemptIds.filter(id => complete(state.attempts.find(a => a.id === id) || {})).length; }
function hasFreshTopicQuestion() { return topicPool(state.session.topic).some(q => !state.session.attemptIds.some(id => state.attempts.find(a => a.id === id)?.questionId === q.id)); }
function pickQuestion(session = state.session) {
  const scoped = topicPool(session.topic,session.topicId);
  const done = new Set();
  for(const id of session.attemptIds) {const qid=state.attempts.find(a=>a.id===id)?.questionId;if(scoped.some(q=>q.id===qid))done.add(qid);if(done.size===scoped.length)done.clear();}
  const candidates = scoped.filter(q=>!done.has(q.id));
  const pool = candidates.length ? candidates : scoped;
  return pool.find(q=>reviewInfo(q)?.isDue) || pool.find(q=>!latest(q.id)) || pool.find(q=>reviewInfo(q)?.needs) || pool[0];
}
function render(focus = true, preserveY = null) {
  document.documentElement.classList.toggle('large-text', state.settings.largeText);
  $('#large-text').checked = state.settings.largeText;
  document.querySelectorAll('.nav-item').forEach(b=>{ const active = b.dataset.view === (state.view==='study'?(state.session.topic?'topics':'home'):state.view); b.classList.toggle('active',active); active ? b.setAttribute('aria-current','page') : b.removeAttribute('aria-current'); });
  $('#review-count').textContent = reviewQuestions().length;
  main.innerHTML = state.view==='planning'&&planner ? planner.views().planningHTML() : state.view==='diagnostics'&&planner ? planner.views().diagnosticsHTML() : state.view==='diagnostic'&&planner ? planner.views().diagnosticHTML() : state.view==='study' && current() ? views().studyHTML() : state.view==='topics' ? views().topicsHTML() : state.view==='review' ? views().reviewHTML() : state.view==='history' ? views().historyHTML() : state.view==='materials' ? views().materialsHTML() : views().homeHTML();
  if (focus) { main.focus({preventScroll:true}); window.scrollTo(0, preserveY ?? 0); }
}
let navigation=0;
function go(view) { if(!store)return;navigation++;main.setAttribute('aria-busy','false');state.view=view; save(); render(); }
let opening=false;
async function start(id, newSession = false, options = {}) {
  if(opening)return;opening=true;const token=++navigation;main.setAttribute('aria-busy','true');notice('教材を読み込んでいます。');
  try {
  let session=newSession?{attemptIds:[],topic:options.topic || null,topicId:qualification.topics.find(t=>t.name===options.topic)?.id||null}:state.session;
  if(id && session.topic && (session.topicId?question(id)?.topicId!==session.topicId:question(id)?.topic!==session.topic)) session={attemptIds:[],topic:null,topicId:null};
  if(session.topicId)session={...session,topic:qualification.topics.find(t=>t.id===session.topicId)?.name||session.topic};
  const picked = id ? question(id) : pickQuestion(session); const q=picked?question(picked.id):null;
  if(!q){notice('この範囲には現在利用できる問題がありません。分野の一覧から選び直してください。');return;}
  if(!usableOffline(q)) {notice('この問題はまだオフライン用に保存されていません。接続後に開いてください。');return;}
  await content.ensure(q.id);if(token!==navigation)return;
  const full=question(q.id);
  state.session=session;
  const old = current(); if(old && !complete(old)) { old.status='postponed'; old.updatedAt=now(); }
  const a=createAttempt(full,{topic:state.session.topic,readingNote:state.session.topic?readNote(state.session.topic):'',contentRevision:state.overrides[q.id]?.revision||'original'});
  state.attempts.push(a); state.currentId=a.id; state.session.attemptIds.push(a.id); state.view='study'; save(); render();return a;
  }catch(error){notice(error.message);}finally{opening=false;if(token===navigation)main.setAttribute('aria-busy','false');if(token===navigation&&$('#notice').textContent==='教材を読み込んでいます。')notice('');}
}
async function resume(id) {
 const runId=planner?.derivedRun(id);if(runId){await planner.action({dataset:{action:'resume-diagnostic',id:runId}});const detail=document.querySelector(`[data-diagnostic-slot="${id}"]`);if(detail){detail.open=true;detail.scrollIntoView({block:'start'});}return;}
 const target=state.attempts.find(a=>a.id===id);if(!target)return;const token=++navigation;main.setAttribute('aria-busy','true');
 try {
  if(questionIndex.has(target.questionId))await content.ensure(target.questionId);if(token!==navigation)return;
  const old=current();if(old&&old.id!==id&&!complete(old))old.status='postponed';
  let a=state.attempts.find(a=>a.id===id);if(!a)return;
  // A synchronized checkpoint belongs to its creating device. Continue under
  // a fresh UUID so two devices can both answer without overwriting each other.
  const identity=await store.identity(),remote=(await store.remoteDevice?.(id));
  if(!complete(a)&&remote&&remote!==identity.deviceId){a={...structuredClone(a),id:crypto.randomUUID(),continuationOf:id,continuedAt:now(),scrollY:0};state.attempts.push(a);id=a.id;}
  state.currentId=id;
  if(!state.session.attemptIds.includes(id)||(state.session.topicId!==undefined?state.session.topicId!==(a.topicId||null):state.session.topic!==(a.topic||null)))state.session={attemptIds:[id],topic:qualification.topics.find(t=>t.id===a.topicId)?.name||a.topic||null,topicId:a.topicId||null};
  if(!complete(a))a.status='in_progress';state.view='study';await save();if(token===navigation)render(true,a.scrollY||0);
 }catch(error){notice(error.message);}finally{if(token===navigation)main.setAttribute('aria-busy','false');}
}

function finish(status) {
  const a=current(); if(!a || complete(a)) return;
  finalizeAttempt(a,status); save(); render(false);
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
  if(el.dataset.view) { go(el.dataset.view); return; }
  const action=el.dataset.action; const a=current();
  try {
  if(await planner?.action(el))return;
  if(action==='start-session') start(null,true);
  else if(action==='topic-session') { if(!topics().includes(el.dataset.topic))return;start(null,true,{topic:el.dataset.topic}); }
  else if(action==='zoom') openImage(el.dataset.id,Number(el.dataset.image));
  else if(action==='catalog-page'){catalog.page=Number(el.dataset.page);render();}
  else if(action==='reset-filters'){catalog={year:'',season:'',topic:'',query:'',enriched:false,page:1};render();}
  else if(action==='start') start(el.dataset.id);
  else if(action==='resume') await resume(el.dataset.id);
  else if(action==='latest-hints') await useLatestHints();
  else if(action==='next') start();
  else if(['pause','postpone','end'].includes(action)) { if(a&&!complete(a)) {a.status='postponed';a.updatedAt=now();} state.currentId=null;go('home'); }
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
main.addEventListener('input',e=>{if(planner?.input(e.target))return;if(e.target.closest('#catalog-form')){const f=new FormData($('#catalog-form'));catalog={year:String(f.get('year')),season:String(f.get('season')),topic:String(f.get('topic')),query:String(f.get('query')),enriched:f.has('enriched'),page:1};$('#catalog-results').innerHTML=views().catalogRowsHTML();return;}if(e.target.dataset.readingTopic){const topic=qualification.topics.find(t=>t.name===e.target.dataset.readingTopic);state.readingNotes[topic?.id||e.target.dataset.readingTopic]=e.target.value.trim().slice(0,200);save();}});
main.addEventListener('change',async e=>{
  if(await planner?.change(e.target))return;
  if(e.target.closest('#catalog-form'))return;
  const a=current();if(!a||complete(a))return;
  if(e.target.name==='answer') {selectAnswer(a,Number(e.target.value),question(a.questionId));document.querySelectorAll('.choice').forEach(l=>l.classList.toggle('selected',$('input',l).checked)); $('[data-action="submit"]').disabled=false;}
  else if(e.target.id==='confidence') a.confidence=e.target.checked;
  a.updatedAt=now();save();
});
$('#catalog-form')?.addEventListener('submit',e=>e.preventDefault());
main.addEventListener('submit',async e=>{if(['catalog-form','exam-form','phase-form'].includes(e.target.id))e.preventDefault();await planner?.submit(e.target);});
$('#close-image').addEventListener('click',()=>$('#image-dialog').close());
$('#image-zoom-in').addEventListener('click',()=>{const img=$('#image-scroll img');img.style.width=`${Math.min(4000,img.clientWidth*1.25)}px`;});
$('#image-zoom-out').addEventListener('click',()=>{const img=$('#image-scroll img');img.style.width=`${Math.max(600,img.clientWidth/1.25)}px`;});
$('#settings-button').addEventListener('click',()=>$('#settings-dialog').showModal());
$('#large-text').addEventListener('change',e=>{state.settings.largeText=e.target.checked;save();render(false);});
$('#export-state').addEventListener('click',async()=>{await saves;download(corruptRaw??{...state,workspaceBackup:planner?.backup()},`${qualification.id}-study-record-${day(now())}.json`,corruptRaw!==null);});
$('#import-state').addEventListener('change',async e=>{
  const file=e.target.files[0];if(!file)return;
  try { if(file.size>64*1024*1024) throw new Error('ファイルが大きすぎます。64MB以下の学習記録を選んでください。'); const candidate=validateState(JSON.parse(await file.text()));planner?.validateBackup(candidate.workspaceBackup);
    if((state.attempts.length||corruptRaw!==null)&&!confirm('通常演習の記録と教材編集を、ファイルの内容で置き換えます。計画・診断は追加し、既存のものは残します。先に書き出して保管してください。読み込みますか？'))return;
    await saves;await planner?.restoreBackup(candidate.workspaceBackup);delete candidate.workspaceBackup;corruptRaw=null;state=candidate;notice('');await save({replace:true});render();$('#settings-status').textContent=storageOK?'学習記録を読み込みました。':'読み込みましたが、ブラウザに保存できていません。書き出して保管してください。';
  } catch(error) { $('#settings-status').textContent=error instanceof SyntaxError?'JSONを読み取れませんでした。現在の記録は変更していません。':error.message; }
  finally {e.target.value='';}
});
$('#clear-state').addEventListener('click',async()=>{if(!confirm('このブラウザの学習記録を削除します。問題と教材の編集は残します。よろしいですか？'))return;await saves;const {settings,overrides}=state;corruptRaw=null;state={...makeState(),settings,overrides};notice('');await save({replace:true});await planner?.clearDiagnostics();render();$('#settings-status').textContent=storageOK?'通常演習・診断の学習記録を削除しました。受験日と計画は残しています。':'記録を初期化しましたが、保存に失敗しました。ブラウザの保存設定を確認してください。';});
$('#close-editor').addEventListener('click',()=>$('#editor-dialog').close());
$('#editor-form').addEventListener('submit',e=>{e.preventDefault();const f=new FormData(e.target);const q=question(editId);const changes={enrichment:'personal',hintStatus:'individual',hints:q.hints.map((h,i)=>({...h,text:String(f.get(`hint${i}`)).trim(),revealsAnswer:f.has(`reveal${i}`)})),revision:now()};for(const k of ['summary','explanation','takeaway'])changes[k]=String(f.get(k)).trim();if(changes.hints.some(h=>!h.text)||['summary','explanation','takeaway'].some(k=>!changes[k])){alert('空欄を埋めてから保存してください。');return;}state.overrides[editId]=changes;save();$('#editor-dialog').close();render(false);});
$('#reset-material').addEventListener('click',()=>{if(!confirm('この問題のヒントと解説を、初期教材に戻しますか？'))return;delete state.overrides[editId];save();$('#editor-dialog').close();render(false);});
let scrollTimer;
window.addEventListener('scroll',()=>{if(state.view!=='study')return;clearTimeout(scrollTimer);const attemptId=state.currentId;scrollTimer=setTimeout(()=>{if(state.view!=='study'||state.currentId!==attemptId)return;const a=current();if(a){a.scrollY=window.scrollY;save();}},200);},{passive:true});
function saveScroll(){if(state.view==='study'&&current()){current().scrollY=window.scrollY;save();}}
window.addEventListener('pagehide',saveScroll);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveScroll();});
async function switchOwner(owner,{restore=false}={}){
 const identity=await store.identity();if(identity.owner===(owner||`guest:${identity.deviceId}`))return;
 main.inert=true;document.querySelector('.sidebar').inert=true;
 const controls=['import-state','export-state','clear-state','large-text'];controls.forEach(id=>$("#"+id).disabled=true);
 clearTimeout(scrollTimer);navigation++;$('#editor-dialog').close();
 try{
  if(!await save())throw new Error('現在の記録を保存できません。');await saves;
  const next=createLocalStore({qualificationId:qualification.id,rootPath:appRoot.pathname,key:qualification.storageKey,validate:validateState,owner});
  let raw=await next.read(),candidate=raw?validateState(JSON.parse(raw)):makeState();
  if(!raw){candidate.settings={...state.settings};await next.write(candidate);raw=await next.read();}
  await store.close();store=next;state=validateState(JSON.parse(raw));await planner?.bind();corruptRaw=null;storageOK=true;editId=null;
  // Explicit account changes open home; restoring the same browser's saved
  // login preserves its own current question and scroll position.
  if(!restore){state.currentId=null;state.view='home';state.session={attemptIds:[],topic:null};}
  if(restore&&state.view==='study'&&current()&&questionIndex.has(current().questionId))await content.ensure(current().questionId).catch(()=>{});
  await save();render(true,state.view==='study'?current()?.scrollY:0);notice('');
  $('#clear-state').closest('details').hidden=!!owner;$('#import-state').closest('label').hidden=!!owner;
 }finally{main.inert=false;document.querySelector('.sidebar').inert=false;controls.forEach(id=>$("#"+id).disabled=false);}
}
function validateSyncAttempt(a){const probe={...makeState(),attempts:[a]};validateState(probe);if(a.qualificationId!==qualification.id||!a.questionSnapshot)throw new Error('同期対象の問題情報がありません。');}
function remoteRecords(records){
 const byId=new Map(state.attempts.map(a=>[a.id,a]));for(const a of records)if(a.id!==state.currentId)byId.set(a.id,a);
 state.attempts=[...byId.values()].sort((a,b)=>a.startedAt.localeCompare(b.startedAt)||a.id.localeCompare(b.id));rebuildProgress();
 if(records.length&&state.view!=='study'&&state.view!=='planning')render(false);
}
function remoteFork({before,after,data}){
 const a=state.attempts.find(x=>x.id===before);if(a)Object.assign(a,data);else state.attempts.push(data);
 if(state.currentId===before)state.currentId=after;state.session.attemptIds=state.session.attemptIds.map(id=>id===before?after:id);rebuildProgress();
}
async function importGuest(uid){
 if((await store.identity()).owner!==`uid:${uid}`)throw new Error('アカウントが変わりました。');
 const guest=createLocalStore({qualificationId:qualification.id,rootPath:appRoot.pathname,key:qualification.storageKey,validate:validateState});
 try{
  const raw=await guest.read();if(!raw){await planner?.importGuest(uid,(await guest.identity()).deviceId);return;}
  const source=validateState(JSON.parse(raw));if(!source.attempts.length){await planner?.importGuest(uid,(await guest.identity()).deviceId);return;}
  if(!confirm(`ログイン前の${source.attempts.length}件の学習記録を、このGoogleアカウントへ追加します。元の記録は残します。取り込みますか？`))return;
  const identity=await guest.identity(),prefix=`${identity.deviceId}:`,already=new Set(state.attempts.map(a=>a.importedFrom).filter(Boolean));
  const mapping=new Map(await Promise.all(source.attempts.filter(a=>!already.has(prefix+a.id)).map(async a=>[a.id,await guestAttemptId(uid,prefix+a.id)])));
  for(const original of source.attempts){if(!mapping.has(original.id))continue;const a=structuredClone(original);
   if(!a.questionSnapshot){await content.ensure(a.questionId);a.questionSnapshot=createAttempt(question(a.questionId)).questionSnapshot;}
   a.id=mapping.get(original.id);a.qualificationId=qualification.id;a.selectedChoiceId=a.selected===null?null:a.questionSnapshot.choices[a.selected].id;a.importedFrom=prefix+original.id;
   if(a.continuationOf)a.continuationOf=mapping.get(a.continuationOf)||a.continuationOf;
   validateSyncAttempt(a);state.attempts.push(a);
  }
  if(!await save())throw new Error('取り込んだ記録を保存できませんでした。');await planner?.importGuest(uid,identity.deviceId);render(false);
 }finally{await guest.close();}
}
async function initialize(){
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
  planner=createPlanningFeature({qualification,rootPath:appRoot.pathname,getStore:()=>store,getState:()=>state,getNavigation:()=>navigation,content,base,validateAttempt:validateSyncAttempt,onUpdate:(options={})=>{rebuildProgress();if(state.view!=='study'&&!options.preserveForm)render(false);},onNavigate:(view,runId)=>{if(view==='diagnostic'){const a=current();if(a&&!complete(a))a.status='postponed';state.currentId=null;state.currentRunId=runId;}go(view);},onNotice:notice,onChanged:()=>account?.workspaceChanged(),getReviewCount:()=>reviewQuestions().length,download});
  await refreshOfflineQuestions();
  if(state.view==='study'&&!current())state.view='home'; rebuildProgress();render(true,state.view==='study'?current()?.scrollY:0);
  if(corruptRaw!==null)save();else if(!storageOK)$('#save-state').textContent='保存できていません';
  await planner.bind();
  initAccountControls({getWorkspaceStore:()=>planner.store(),onDocuments:planner.onDocuments,onWorkspaceStatus:planner.onStatus,qualificationId:qualification.id,getStore:()=>store,switchOwner,importGuest,validateAttempt:validateSyncAttempt,onRecords:remoteRecords,onFork:remoteFork}).then(value=>{account=value;});
  if(navigator.modelContext?.registerTool) {
    navigator.modelContext.registerTool({name:'get_study_summary',description:'Read counts of local study attempts and review candidates. Does not modify study records.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:async()=>({content:[{type:'text',text:JSON.stringify(planner.summary())}]})});
  }
} catch(error) { main.innerHTML='<div class="empty"><h1>問題を読み込めませんでした。</h1><p>接続を確認し、このページを再読み込みしてください。</p><button class="button primary" id="reload">再読み込み</button></div>';$('#reload').addEventListener('click',()=>location.reload());console.error(error); }
}
await initialize();
