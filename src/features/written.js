import {studyEntryButton,studyBackButton,aiQuestionButton} from '../ui/study-controls.js';
import {caseBodyHTML} from '../ui/case-body.js';
import {numericInstruction} from '../domain/decimal-answer.js';
import {legalContextHTML} from '../ui/legal-context.js';
import {requiredCaseAssets} from '../domain/offline-assets.js';
import {canonical} from '../domain/plan-history.js';
import {createWorkspaceStore} from '../storage/workspace.js';
import {createCaseRun,caseResponse,validateCaseRun,caseFields,canSubmitCaseField,setCaseResponse,submitCaseField,viewCaseAnswer,checkCaseItem,rateCaseField,mayViewAnswer,mayViewCaseExplanation,updateCaseStatus,caseResult,SELF_OUTCOMES} from '../domain/case-study.js';
import {questionInlineHTML,questionTextHTML} from '../ui/question-text.js';
import {MAX_ANSWER_SET_INPUTS,withAnswerSets} from '../domain/case-answer-set.js';
import {caseCorrectChoiceIds} from '../domain/case-field.js';
import {caseFeedback} from '../domain/case-feedback.js';
import {writtenAnswerSetHTML} from '../ui/written-answer-set.js';
import {writtenTextGrid} from '../ui/written-text-grid.js';
import {writtenReflectionHTML} from '../ui/written-reflection.js';
import {esc,timeText} from '../utils.js';
import {studyQueue,caseRecommendation,validCaseScope} from '../domain/study-queue.js';

export function createWrittenFeature({qualification,rootPath,content,getStore,onUpdate,onChanged,onNotice,getPlanViews,studyAllowed=()=>true,getTargetPart=()=>qualification.examParts.find(p=>p.unit==='cases')?.id,getOnline=()=>navigator.onLine,getSavedAssets=async()=>new Set()}){
 const pendingDrafts=new Map();let lastError='';
 let workspace,rows=[],cases=[],currentId=null,view='home',queue=Promise.resolve(),busy=false,aiKey=null,generation=0,draftDOM=false;
 let activeIdentity=null,originalCases=new Map(),feedbackCases={};
 let available=null,contexts={},browsePackId=null,studyMode='learning';
 const explanationIndex=new Map((qualification.caseExplanations||[]).flatMap(pack=>pack.cases.map(entry=>[entry.caseId,{pack,entry}])));
 const emptyReflection=()=>({scroll:0,open:[]});
 let reflectionReturnRunId=null,reflection=emptyReflection(),explanation=null,reflectionLoading=false,reflectionFailed=false;
 let individualActionsKey=null;
 const catalog=()=>qualification.cases?.index||[];
 const caseMetadata=new Map(catalog().map(e=>[e.caseId,e]));
 const metadata=id=>caseMetadata.get(id)||{};
 const caseTopics=qualification.cases?.topics||qualification.topics;
 const caseTopicId=c=>metadata(c.id).caseTopicId||c.topicId;
 const caseTopicName=c=>caseTopics.find(t=>t.id===caseTopicId(c))?.name||qualification.topics.find(t=>t.id===c.topicId)?.name||'';
 const scopedCases=()=>cases.map(c=>({...c,...metadata(c.id)}));
 const scopeFor=run=>contexts[run?.id]||null;
 const scopeLabel=scope=>[scope?.topicId?'この分野':scope?.topicIds?.length?'計画の重点':scope?.packId?'この試験回':null,scope?.order==='number'?'番号順':'おすすめ'].filter(Boolean).join(' · ');
 function candidates(scope,excludeCurrent=false){const visited=scope?runs().filter(r=>contexts[r.id]?.sessionId===scope.sessionId).map(r=>r.caseId):[];if(excludeCurrent&&current())visited.push(current().caseId);const source=scopedCases().filter(c=>!excludeCurrent||scope?.order!=='number'||!current()||c.number>(metadata(current().caseId).number||0));return studyQueue(source,{scope:scope||{examPartId:partId()},visited:excludeCurrent?visited:[],allowed:studyAllowed,available:usable,compareRecommended:caseRecommendation(runs(),{seed:scope?.sessionId||qualification.id})});}
 function newScope(options={}){return {examPartId:partId(),topicId:null,topicIds:[],packId:null,order:'recommended',sessionId:crypto.randomUUID(),...options};}
 async function refreshAvailability(){available=getOnline()?null:await getSavedAssets();}
 const usable=c=>available===null||requiredCaseAssets(c).every(src=>available.has(new URL(src,content.rootURL||document.baseURI).href));
 const eligibleCases=()=>cases.filter(studyAllowed);
 const partId=()=>getTargetPart(),part=()=>qualification.examParts.find(p=>p.id===partId());
 const partLabel=part()?.label||'記述',caseLabel=part()?.caseLabel||'大問',countLabel=part()?.countLabel||'題';
 const row=id=>rows.find(r=>r.id===id),allRuns=()=>rows.filter(r=>r.kind==='case').map(r=>r.payload),runs=()=>allRuns().filter(r=>r.examPartId===partId());
 const current=()=>{const r=pendingDrafts.get(currentId)||row(currentId)?.payload;return r?.examPartId===partId()?r:null;};
 const validate=(kind,value)=>{if(kind!=='case')throw Error('大問の保存形式を確認できません。');return validateCaseRun(value,qualification);};
 const checkpointKey=(identity,examPartId=partId())=>`hitomon-v2:${rootPath}:${identity.owner}:${qualification.id}:written-view${qualification.examParts.filter(p=>p.unit==='cases').length>1?':'+examPartId:''}`;
 let cpKey;
 function checkpoint(){try{localStorage.setItem(cpKey,JSON.stringify({currentId,view,contexts,browsePackId,studyMode,reflectionReturnRunId,reflection:reflection.revision?reflection:undefined,cursor:current()?Object.fromEntries(['currentItemId','bodyScroll','questionScroll','pane'].map(k=>[k,current().progress[k]])):null}));}catch{}}
 async function bind({loadMaterial=true}={}){const token=++generation;await flush();await workspace?.close();const identity=await getStore().identity();if(token!==generation)return;workspace=createWorkspaceStore({...identity,rootPath,namespaceName:'written',validate});rows=await workspace.read();if(workspace.error())throw workspace.error();const [materials,revisions,feedback]=loadMaterial?await Promise.all([content.loadCases(),content.loadCaseAnswerSets(),content.loadCaseFeedback()]):[[],{},{}];
  feedbackCases=feedback;
  originalCases=new Map(materials.filter(c=>c.examPartId===partId()).map(c=>[c.id,c]));
  cases=[...originalCases.values()].map(c=>withAnswerSets(c,revisions[c.id]));await refreshAvailability();activeIdentity=identity;cpKey=checkpointKey(identity);let cp;try{cp=JSON.parse(localStorage.getItem(cpKey));}catch{}currentId=runs().some(r=>r.id===cp?.currentId)?cp.currentId:null;contexts=Object.fromEntries(Object.entries(cp?.contexts||{}).filter(([id,scope])=>runs().some(r=>r.id===id)&&validCaseScope(scope,qualification,catalog())));browsePackId=catalog().some(e=>e.packId===cp?.browsePackId)?cp.browsePackId:null;studyMode=cp?.studyMode==='exam'?'exam':'learning';view=['home','history','topics','study','planning','review','packs','pack','reflection'].includes(cp?.view)?cp.view:'home';if(['study','reflection'].includes(view)&&!current())view='home';if(current()&&cp?.cursor){const candidate=structuredClone(current());candidate.progress={...candidate.progress,...cp.cursor};try{validate('case',candidate);Object.assign(current().progress,cp.cursor);}catch{}}
  resetReflection();
  if(current()&&cp?.reflectionReturnRunId===currentId)reflectionReturnRunId=currentId;
  if(current()&&cp?.reflection?.runId===currentId)reflection=restoreReflection(cp.reflection);
  if(view==='reflection'){
   const selected=availableExplanation(current());
   if(selected)await loadReflection(selected);
   else view='study';
  }
 }
 async function persist(run,expected){const next=structuredClone(run),target=workspace,token=generation;const saved=await target.write('case',next.id,next,expected);if(token!==generation||target!==workspace)return;rows=rows.filter(r=>r.id!==saved.id).concat(saved);onChanged();return saved;}
 function edit(change,{render=true,remember=true}={}){const token=generation,id=currentId;const op=queue.catch(()=>{}).then(async()=>{if(token!==generation)return false;const r=row(id);if(!r)throw Error('大問の記録が見つかりません。');const previous=pendingDrafts.get(id),next=structuredClone(previous||r.payload);change(next);validate('case',next);if(canonical(next)===canonical(r.payload)){if(pendingDrafts.get(id)===previous)pendingDrafts.delete(id);draftDOM=pendingDrafts.size>0;if(render&&id===currentId)onUpdate();return true;}if(remember)pendingDrafts.set(id,next);await persist(next,r.localRevision);if(pendingDrafts.get(id)===(remember?next:previous))pendingDrafts.delete(id);lastError='';draftDOM=pendingDrafts.size>0;checkpoint();const retry=document.querySelector('.written-save-actions');if(retry&&!draftDOM)retry.hidden=true;if(render&&id===currentId)onUpdate();return true;});queue=op;op.catch(error=>{lastError=error.message;draftDOM=pendingDrafts.size>0;const retry=document.querySelector('.written-save-actions');if(retry&&id===currentId)retry.hidden=false;const conflict=document.querySelector('.written-conflict-controls');if(conflict&&row(id)?.conflict)conflict.innerHTML=conflictControls(row(id));if(remember)onNotice(error.message+' 入力を残しています。「保存を再試行」か、設定から書き出して保管してください。');});return op;}
 async function flush({allowUncommitted=false}={}){if(allowUncommitted){await queue.catch(()=>{});await workspace?.flush().catch(()=>{});return;}await queue;await workspace?.flush();if(pendingDrafts.size)throw Error(lastError||'大問の入力がまだ保存できていません。');}
 const conflictControls=r=>r?.conflict?`<section class="notice"><p>別端末の変更と重なっています。使う内容を選んでください。</p><div class="button-row"><button class="button secondary" data-action="written-remote" data-id="${esc(r.id)}">クラウドの内容を使う</button><button class="button secondary" data-action="written-fork" data-id="${esc(r.id)}">この端末の内容を別の取り組みとして保存</button></div></section>`:'';
 async function begin(id,mode,scope=null){await flush();const c=id?cases.find(c=>c.id===id)||current()?.material:cases.find(c=>c.id===candidates(scope)[0]?.id);if(!c)throw Error('大問教材が見つかりません。');if(!studyAllowed(c))throw Error('法令改正のある問題は除外中です。');await refreshAvailability();if(!usable(c))throw Error('この大問の図がまだ保存されていません。接続中に教材を保存してください。');const run=createCaseRun(c,{mode:mode||'learning'});await persist(run,0);currentId=run.id;resetReflection();contexts[run.id]=scope||newScope();view='study';aiKey=null;checkpoint();onUpdate();}
 function answerFormUpdate(run,itemId){
  const original=originalCases.get(run.caseId),latest=cases.find(c=>c.id===run.caseId);
  if(run.progress.status==='completed'||!latest||!original||latest.version<=run.caseVersion||
     !studyAllowed(latest)||!usable(latest))return null;
  const fields=latest.items.find(item=>item.id===itemId)?.fields;
  if(!fields?.some(field=>field.type==='answerSet')||canonical(run.material)!==canonical(original))return null;
  const before=new Map(caseFields(run.material).map(({key,field})=>[key,field]));
  const unchanged=new Set(caseFields(latest).filter(({key,field})=>canonical(field)===canonical(before.get(key))).map(({key})=>key));
  const keep=Object.entries(run.responses).every(([key,response])=>unchanged.has(key)||!response.submittedAt&&!response.value.trim());
  return {latest,keep,unchanged};
 }
 async function switchAnswerForm(){
  await flush();
  const previous=current();
  await refreshAvailability();
  const change=previous&&answerFormUpdate(previous,previous.progress.currentItemId);
  if(!change)return;
  const at=change.keep?previous.startedAt:undefined;
  const run=createCaseRun(change.latest,{mode:previous.mode,at});
  if(change.keep){
   const snapshot=structuredClone(previous);
   run.responses=Object.fromEntries(Object.entries(snapshot.responses).filter(([key])=>change.unchanged.has(key)));
   run.evaluations=snapshot.evaluations;
   run.assistance=snapshot.assistance;
   run.progress.submittedFieldKeys=snapshot.progress.submittedFieldKeys;
   run.progress.status=snapshot.progress.status;
  }
  run.progress.bodyScroll=previous.progress.bodyScroll;
  showItem(run,previous.progress.currentItemId);
  updateCaseStatus(run,run.updatedAt);
  validate('case',run);
  if(!await persist(run,0))return;
  contexts[run.id]=scopeFor(previous)||newScope();
  currentId=run.id;resetReflection();aiKey=null;checkpoint();onUpdate();
  const first=document.querySelector('.written-items [data-answer-set-entry]:not(:disabled), .written-items [data-answer-set-choice]:not(:disabled)');
  if(first)first.focus();
 }
 async function resumeRun(run,scope=null){await flush();if(currentId!==run.id)resetReflection();currentId=run.id;if(scope)contexts[run.id]=scope;else contexts[run.id]??=newScope();view='study';checkpoint();onUpdate();}
 async function beginQueue(options={}){await flush();await refreshAvailability();const scope=newScope(options),pool=candidates(scope),pending=runs().filter(r=>r.progress.status!=='completed').sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt)),selected=scope.order==='number'?pool[0]:pool.find(c=>!pending.some(r=>r.caseId===c.id))||pool[0];if(!selected)throw Error('この範囲には今解ける問題がありません。');const existing=pending.find(r=>r.caseId===selected.id);if(existing)await resumeRun(existing,scope);else await begin(selected.id,studyMode,scope);}
 async function nextCase(){await flush();const run=current();if(!run||run.progress.status!=='completed')throw Error('回答と評価を終えてから次へ進んでください。');await refreshAvailability();const scope=scopeFor(run)||newScope();contexts[run.id]=scope;const next=candidates(scope,true)[0];if(!next)throw Error('この範囲はここまでです。');const existing=runs().filter(r=>r.caseId===next.id&&r.progress.status!=='completed').sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt))[0];if(existing)await resumeRun(existing,scope);else await begin(next.id,run.mode,scope);}
 async function setView(next){await flush();view=next;checkpoint();onUpdate();}
 function showItem(run,itemId){
  run.progress.currentItemId=itemId;
  run.progress.pane='questions';
  run.progress.questionScroll=0;
  run.updatedAt=new Date().toISOString();
 }
 function revealItem(run,itemId){
  for(const {item,key} of caseFields(run.material)){
   if(item.id===itemId&&mayViewAnswer(run,key))viewCaseAnswer(run,key);
  }
 }
 function focusFeedback(key){
  const target=key?document.getElementById('written-answer-'+key):document.querySelector('.written-answer h4');
  focusStudyTarget(target);
 }
 function focusStudyTarget(target){
  if(!target)return;
  target.tabIndex=-1;
  target.focus({preventScroll:true});
  target.scrollIntoView({block:'nearest'});
 }
 async function submitAndCheck(key,skip){
  if(await edit(run=>{
   const reviewNow=run.mode==='learning'||run.progress.status==='partially_completed';
   submitCaseField(run,key,undefined,{skip});
   if(reviewNow)viewCaseAnswer(run,key);
  }))focusFeedback(key);
 }
 async function startExamReview({partial}){
  if(await edit(run=>{
   const {submitted,total}=caseResult(run);
   if(run.mode!=='exam'||!submitted||(submitted<total&&!partial))return;
   if(submitted<total){run.progress.status='partially_completed';updateCaseStatus(run);}
   const first=caseFields(run.material).find(({key})=>run.responses[key]?.submittedAt&&!run.assistance.viewedFields.includes(key));
   if(first){showItem(run,first.item.id);revealItem(run,first.item.id);}
  }))focusFeedback();
 }
 async function advanceItem(itemId){
  if(await edit(run=>{
   if(!run.material.items.some(item=>item.id===itemId))throw Error('小問が見つかりません。');
   showItem(run,itemId);
   if(run.mode==='exam'&&run.assistance.firstAnswerViewedAt)revealItem(run,itemId);
  })){
   focusStudyTarget(document.querySelector('.case-prompt'));
  }
 }
 function availableExplanation(run){
  if(!mayViewCaseExplanation(run))return null;
  const selected=explanationIndex.get(run.caseId);
  const original=originalCases.get(run.caseId);
  if(!selected||selected.entry.caseVersion!==original?.version)return null;
  const published=run.caseVersion===original.version?original:cases.find(c=>c.id===run.caseId);
  return published?.version===run.caseVersion&&canonical(published)===canonical(run.material)?selected:null;
 }
 function resetReflection(){
  reflectionReturnRunId=null;reflection=emptyReflection();explanation=null;reflectionLoading=false;reflectionFailed=false;
 }
 function restoreReflection(saved){
  return {runId:saved.runId,revision:saved.revision,
   scroll:Number.isFinite(saved.scroll)?Math.max(0,saved.scroll):0,
   open:Array.isArray(saved.open)?saved.open.filter(id=>typeof id==='string'):[]};
 }
 async function loadReflection(selected){
  const {pack,entry}=selected,id=currentId,token=generation;
  if(reflection.revision!==entry.revision)reflection={...emptyReflection(),runId:id,revision:entry.revision};
  if(explanation?.revision===entry.revision)return;
  reflectionLoading=true;reflectionFailed=false;
  try{
   const loaded=await content.loadCaseExplanation(pack,entry);
   if(token===generation&&id===currentId)explanation=loaded;
  }catch{
   if(token===generation&&id===currentId)reflectionFailed=true;
  }finally{
   if(token===generation&&id===currentId)reflectionLoading=false;
  }
 }
 async function openReflection(key,runId=currentId){
  await flush();
  const run=runs().find(r=>r.id===runId),selected=availableExplanation(run);
  if(!selected)return;
  if(currentId!==runId){resetReflection();currentId=runId;contexts[runId]??=newScope();}
  rememberReflection();
  view='reflection';
  const id=currentId,token=generation,loading=loadReflection(selected);
  checkpoint();onUpdate();
  await loading;
  if(token!==generation||id!==currentId||view!=='reflection')return;
  checkpoint();onUpdate();
  const target=key&&explanation?.sections.find(section=>section.links.some(link=>link.fieldIds.some(f=>link.itemId+'--'+f===key)));
  if(target)jumpToExplanation(target.id);
  else {
   const opened=[...document.querySelectorAll('details[data-reflection-section][open] summary')];
   const near=reflection.scroll&&opened.reverse().find(heading=>heading.getBoundingClientRect().top<=24);
   (near||document.getElementById('written-reflection-title'))?.focus({preventScroll:true});
  }
 }
 function rememberReflection(){
  if(view!=='reflection'||!explanation||!document.querySelector('.written-reflection'))return;
  reflection.scroll=window.scrollY;
  const sections=[...document.querySelectorAll('details[data-reflection-section]')];
  reflection.open=sections.filter(el=>el.open).map(el=>el.dataset.reflectionSection);
  const toggle=document.querySelector('[data-action="written-reflection-expand"]');
  const toc=document.querySelector('.written-reflection-toc'),back=document.querySelector('[data-action="written-reflection-toc"]');
  if(toc&&back)back.hidden=toc.getBoundingClientRect().bottom>0;
  if(toggle)toggle.textContent=sections.every(section=>section.open)?'すべて閉じる':'すべて開く';
  checkpoint();
 }
 function restoreReflectionDOM(){
  if(explanation){window.scrollTo(0,reflection.scroll);rememberReflection();}
  for(const section of document.querySelectorAll('details[data-reflection-section]')){
   section.addEventListener('toggle',()=>{if(section.isConnected)rememberReflection();});
  }
 }
 function jumpToExplanation(id){
  if(view!=='reflection'||!availableExplanation(current()))return;
  const section=document.querySelector(`details[data-reflection-section="${CSS.escape(id)}"]`);
  if(!section)return;
  section.open=true;
  const heading=section.querySelector('summary');
  heading.focus({preventScroll:true});heading.scrollIntoView({block:'start'});
  rememberReflection();
 }
 function expandReflection(){
  if(view!=='reflection'||!availableExplanation(current()))return;
  const sections=[...document.querySelectorAll('details[data-reflection-section]')];
  const open=!sections.every(s=>s.open);
  for(const section of sections)section.open=open;
  rememberReflection();
 }
 async function returnToStudy(key,pane='questions',ref){
  if(view!=='reflection'||!current())return;
  const slot=key&&caseFields(current().material).find(field=>field.key===key);
  if(key&&!slot)return;
  rememberReflection();
  await edit(run=>{
   run.progress.pane=pane==='body'?'body':'questions';
   if(slot){
    run.progress.currentItemId=slot.item.id;
    viewCaseAnswer(run,key);
   }
  },{render:false});
  reflectionReturnRunId=currentId;
  await setView('study');
  const source=pane==='body'&&ref&&document.getElementById('written-ref-'+ref);
  const target=slot?document.getElementById('written-answer-'+key):source||document.querySelector(pane==='body'?'.written-body':'.case-prompt');
  if(target){target.tabIndex=-1;target.focus({preventScroll:true});if(slot||pane==='body')target.scrollIntoView({block:'start'});}
 }
 function completedActions({withReflection=false}={}){
  const next=candidates(scopeFor(current()),true).length?`<button class="button ${withReflection?'secondary':'primary'}" data-action="written-next">次の${esc(caseLabel)} →</button>`:'';
  return `<div class="finish-actions"><button class="button secondary" data-view="home">今日はここまで</button>${next}</div>`;
 }
 function reflectionHTML(){
  return writtenReflectionHTML({run:current(),explanation,state:reflection,loading:reflectionLoading,failed:reflectionFailed,finish:completedActions()});
 }
 const data=key=>`data-written-key="${esc(key)}"`;
 const resultLabel=r=>r?.evaluation?(r.evaluation.source==='automatic'?(r.evaluation.outcome==='correct'?'自動判定：正解':'自動判定：不正解'):'自己評価：'+SELF_OUTCOMES[r.evaluation.outcome]):r?.submittedAt?'評価待ち':'回答途中';
 function feedbackForRun(run){
  const revision=feedbackCases[run.caseId];
  if(!revision?.versions.includes(run.caseVersion))return null;
  const original=originalCases.get(run.caseId),latest=cases.find(c=>c.id===run.caseId);
  const published=run.caseVersion===original?.version?original:latest;
  if(!published||canonical(published)!==canonical(run.material))return null;
  return {fields:revision.fields,latestFields:new Map(caseFields(latest).map(({key,field})=>[key,field]))};
 }
 function feedbackForSlot({field,key},feedback){
  const latest=feedback?.latestFields.get(key);
  const sameSlot=latest?.answerSet?.sourceFieldIds?.length===1&&latest.answerSet.sourceFieldIds[0]===field.id;
  return caseFeedback(field,feedback?.fields[key],!field.choices&&sameSlot&&latest.choices?latest:field);
 }
 function commonBody(c,feedback){
  const anchors=Object.entries(feedback?.fields||{}).filter(([,value])=>value.source)
   .map(([key,value])=>['answer-'+key,{text:value.source.anchor}]);
  const material=anchors.length?{...c,bodyRefs:{...c.bodyRefs,...Object.fromEntries(anchors)}}:c;
  return caseBodyHTML(material,content.rootURL||document.baseURI,metadata(c.id).referenceTargets);
 }
 function originals(c){const url=c.sourceRecord?.questionUrl;if(!c.sourceImages.length&&!url&&!c.source)return '';return `<details class="written-originals"><summary>原本・出典</summary><p class="small muted">${esc(c.source)}</p>${!getOnline()?'原本はオンラインで参照できます。':c.sourceImages.map((p,i)=>`<a href="${esc(new URL(p,document.baseURI))}" target="_blank" rel="noopener">原本 ${i+1}ページ ↗</a>`).join(' · ')+(url?`<p><a href="${esc(url)}" target="_blank" rel="noopener">公式問題PDF ↗</a></p>`:'')}</details>`;}
 function modeHTML(){return `<details class="case-options"><summary>学習の設定</summary><label class="case-mode">解答の確認<select name="written-study-mode"><option value="learning" ${studyMode==='learning'?'selected':''}>小問ごと</option><option value="exam" ${studyMode==='exam'?'selected':''}>最後にまとめて</option></select></label></details>`;}
 function caseRows(list,scope={}){return list.map(c=>{const m=metadata(c.id),topic=scope.packId&&m.caseTopicId?caseTopicName(c):'';return `<article class="written-case-option"><h3>${m.number?'問'+m.number+' · ':''}${esc(c.title)}</h3><p class="small muted">${esc(m.packLabel||'')}${topic?' · '+esc(topic):''} · ${c.items.length}小問${usable(c)?'':' · 図が未保存'}</p><button class="button secondary" data-action="written-start" ${usable(c)?'':'disabled'} data-id="${esc(c.id)}" data-topic="${esc(scope.topicId||'')}" data-pack="${esc(scope.packId||'')}" data-order="${esc(scope.order||'recommended')}">この${esc(caseLabel)}を解く</button></article>`;}).join('');}
 function homeHTML(){
  const pending=(current()?.progress.status!=='completed'&&current()&&studyAllowed(cases.find(c=>c.id===current().caseId)||current().material)?current():null)||runs().filter(r=>r.progress.status!=='completed'&&studyAllowed(cases.find(c=>c.id===r.caseId)||r.material)).sort((a,b)=>b.updatedAt.localeCompare(a.updatedAt))[0],available=candidates(newScope()).length;
  const entrances=[pending?studyEntryButton({label:'続きから',primary:true,attributes:{'data-action':'written-resume','data-id':pending.id}}):'',studyEntryButton({label:'おすすめで1'+countLabel,primary:!pending,disabled:!available,attributes:{'data-action':'written-start'}}),studyEntryButton({label:'分野から選ぶ',field:true,attributes:{'data-view':'topics'}}),studyEntryButton({label:'試験回から選ぶ',field:true,attributes:{'data-action':'written-packs'}})].join('');
  return `<div class="home-core"><section class="panel quick-start-panel hero-start study-entry"><h1 class="entry-heading">とりあえずはじめる</h1><div class="quick-start entry-list">${entrances}</div></section>${modeHTML()}${getPlanViews()?.homeSupportHTML()||''}</div>`;
 }
 function packsHTML(){const packs=[...new Map(eligibleCases().map(c=>metadata(c.id)).filter(m=>m.packId).map(m=>[m.packId,m])).values()].sort((a,b)=>b.packId.localeCompare(a.packId));return `<div class="page-heading"><h1>試験回から選ぶ</h1></div><div class="case-pack-grid">${packs.map(p=>`<button class="button secondary case-pack-card" data-action="written-pack" data-pack="${esc(p.packId)}"><strong>${esc(p.packLabel)}</strong><span>${eligibleCases().filter(c=>metadata(c.id).packId===p.packId).length}${esc(countLabel)}</span></button>`).join('')}</div>${!packs.length?'<p class="empty">試験回の情報を読み込めませんでした。接続後に開き直してください。</p>':''}`;}
 function packHTML(){const m=catalog().find(e=>e.packId===browsePackId),list=scopedCases().filter(c=>studyAllowed(c)&&c.packId===browsePackId).sort((a,b)=>a.number-b.number),usableAny=list.some(usable);return `<div class="page-heading"><h1>${esc(m?.packLabel||'試験回')}</h1>${studyBackButton({action:'written-packs',label:'試験回の一覧',home:true})}</div><section class="panel"><div class="button-row"><button class="button primary" data-action="written-sequence" data-pack="${esc(browsePackId)}" ${usableAny?'':'disabled'}>番号順で解く</button><button class="button secondary" data-action="written-recommend" data-pack="${esc(browsePackId)}" ${usableAny?'':'disabled'}>おすすめで解く</button></div>${modeHTML()}<button class="button quiet" data-action="offline-open" data-pack="${esc(browsePackId)}">この試験回を端末に保存</button></section><section class="panel"><h2>${list.length}${esc(countLabel)}</h2>${caseRows(list,{packId:browsePackId,order:'number'})}</section>`;}
 function historyHTML(){const ordered=runs().sort((a,b)=>Number(a.progress.status==='completed')-Number(b.progress.status==='completed')||b.updatedAt.localeCompare(a.updatedAt));
  const completed=ordered.filter(run=>run.progress.status==='completed'),unfinished=ordered.filter(run=>run.progress.status!=='completed');
  if(!ordered.length)return `<div class="page-heading"><h1>${esc(partLabel)}の記録</h1><button class="button quiet" data-view="planning">学習計画</button></div><section class="panel"><p>まだ学習記録はありません。</p><button class="button primary" data-action="written-start">1${esc(countLabel)}解く</button></section>`;
  const renderRun=r=>{
   const result=caseResult(r),done=r.progress.status==='completed',reflectionAvailable=Boolean(availableExplanation(r));
   return `<section class="panel written-record"><h3>${esc(r.material.title)}</h3><p class="small muted">${timeText(r.startedAt)} · 回答 ${result.submitted} / ${result.total}欄${result.evaluated<result.total?' · 評価 '+result.evaluated+'欄':''}</p><button class="button secondary" data-action="${reflectionAvailable?'written-reflection-open':'written-resume'}" data-id="${esc(r.id)}">${done?reflectionAvailable?'振り返る':'回答・解説を見る':'続きから'}</button>${done?`<details><summary>評価の内訳</summary>${result.automatic.count?`<p>自動判定 ${result.automatic.correct} / ${result.automatic.count}欄正解</p>`:''}${Object.entries(result.self).filter(([,count])=>count).map(([outcome,count])=>`<p>自己評価 · ${SELF_OUTCOMES[outcome]} ${count}欄</p>`).join('')}</details>`:''}${conflictControls(row(r.id))}</section>`;
  };
  return `<div class="page-heading"><h1>${esc(partLabel)}の記録</h1><button class="button quiet" data-view="planning">学習計画</button></div>${unfinished.length?`<h2>途中の学習</h2>${unfinished.map(renderRun).join('')}`:''}${completed.length?`<h2>完了した学習 · ${completed.length}${esc(countLabel)}</h2>${completed.map(renderRun).join('')}`:''}`;
 }
 function answerConstraints(field,limit){
  return (field.constraints||[]).flatMap(text=>text.match(/[^。]+。?/g)||[])
   .map(text=>text.trim())
   .filter(text=>!(/2000字/.test(text)||/^(?:原本|原問).*(?:字数|文字数).*指定(?:なし|はない)。?$/.test(text)))
   .filter(text=>!limit||text!==limit+'字以内。');
 }
 function fieldHTML(slot,run,showLabel,waitingReview,feedback){
  const {field:f,key}=slot,r=caseResponse(run,key),locked=!!r?.submittedAt,shown=run.assistance.viewedFields.includes(key)&&mayViewAnswer(run,key),isAutomatic=r?.evaluation?.source==='automatic';
  const correctIds=shown&&f.type==='singleChoice'?caseCorrectChoiceIds(f):[];
  const choices=f.type==='singleChoice'?`<fieldset class="written-choices choices" ${locked?'disabled':''}><legend class="sr-only">${esc(f.label)}</legend>${f.choices.map(c=>{const selected=r?.value===c.id,correct=correctIds.includes(c.id);return `<label class="choice ${selected?'selected':''} ${shown&&correct?'correct-choice':''} ${shown&&selected&&!correct?'wrong-choice':''}"><input type="radio" name="written-${esc(key)}" value="${esc(c.id)}" ${data(key)} ${selected?'checked':''}><span class="choice-code">${esc(c.label)}</span><div class="choice-text">${esc(c.text)}</div>${shown&&correct?'<span class="sr-only">（正解）</span>':''}${shown&&selected?'<span class="sr-only">（あなたの回答）</span>':''}</label>`;}).join('')}</fieldset>`:'';
  const limit=['shortText','freeText'].includes(f.type)&&f.maxLength<2000?f.maxLength:null;
  const length=[...(r?.value||'')].length;
  const count=limit&&!locked?`<span class="small written-count" id="written-count-${esc(key)}">${length} / ${limit}字</span>`:'';
  const textEditor=limit?writtenTextGrid({value:r?.value||'',limit,locked,attributes:`${data(key)} ${count?`aria-describedby="written-count-${esc(key)}"`:''}`}):
   `<textarea rows="3" ${data(key)} maxlength="${f.maxLength||2000}" ${locked?'readonly':''}>${esc(r?.value||'')}</textarea>`;
  const constraints=answerConstraints(f,limit);
  const input=f.type==='answerSet'?writtenAnswerSetHTML(f,r,key,shown):f.type==='singleChoice'?choices:f.type==='numeric'?`<label class="editor-field numeric-field"><span class="sr-only">${esc(f.label)}</span><span class="numeric-answer"><input type="text" inputmode="decimal" autocomplete="off" ${data(key)} maxlength="${f.maxLength}" value="${esc(r?.value||'')}" ${locked?'readonly':''}><span>${esc(f.numeric.unit)}</span></span>${locked?'':`<span class="small">${esc(numericInstruction(f))}</span>`}</label>`:`<label class="editor-field"><span class="sr-only">${esc(f.label)}</span>${textEditor}${count}</label>`;
  const resultTone=r?.skipped?'result-incorrect':isAutomatic?(r.evaluation.outcome==='correct'?'result-correct':'result-incorrect'):'result-neutral';
  const result=shown?feedbackForSlot(slot,feedback):null;
  const explanationOpen=shown&&(!isAutomatic||r.evaluation.outcome==='incorrect'||result.explanation.length<=180&&!result.explanation.includes('\n'));
  const unit=f.type==='numeric'?' '+f.numeric.unit:'';
  const answer=({text,code})=>`<strong>${code?questionInlineHTML(text):esc(text)}${esc(unit)}</strong>${code?`<span class="written-answer-code">（${esc(code)}）</span>`:''}`;
  const answers=!shown?'':result.answers.length===1?`<p class="reference-answer">${answer(result.answers[0])}</p>`:
   `<ul class="written-answer-list">${result.answers.map(entry=>`<li class="reference-answer">${answer(entry)}</li>`).join('')}</ul>`;
  const rubric=result?.rubric.length?`<ul>${result.rubric.map(p=>`<li>${esc(p)}</li>`).join('')}</ul>`:'';
  const source=result?.source?`<button class="button quiet written-answer-source" data-action="written-reference" data-ref="answer-${esc(key)}">${esc(result.source.label)}を見る</button>`:'';
  const status=resultLabel(r);
  const selfEvaluation=r?.evaluation?`<div class="written-rubric"><p class="written-field-status" id="written-rating-${esc(key)}">${esc(status)}</p>${rubric?`<details><summary>自己評価の基準</summary>${rubric}</details>`:''}</div>`:`<div class="written-rubric"><h4>${rubric?'自己評価の基準':'自己評価'}</h4>${rubric}<div class="written-self" role="group" aria-label="自己評価">${Object.entries(SELF_OUTCOMES).map(([k,label])=>`<button class="button secondary" data-action="written-rate" ${data(key)} data-outcome="${k}">${label}</button>`).join('')}</div></div>`;
  return `<section class="written-field" ${data(key)}>${showLabel?`<h3>${esc(f.label)}</h3>`:''}${!locked&&constraints.length?`<p class="small muted">${esc(constraints.join(' '))}</p>`:''}${input}
   ${!locked?`<div class="answer-actions written-field-actions${slot.item.fields.length>1?' written-individual-actions':''}"><button class="button ${slot.item.fields.length>1?'secondary':'primary'}" data-action="written-submit" ${data(key)} ${canSubmitCaseField(f,r?.value)?'':'disabled'}>回答する</button><button class="button quiet" data-action="written-skip" ${data(key)}>${run.mode==='learning'?'解答を見る':'分からない'}</button></div>`:!shown?`<p class="written-field-status">${r.skipped?'未回答':'回答済み'}</p>${!waitingReview&&mayViewAnswer(run,key)?`<div class="answer-actions written-field-actions"><button class="button secondary" data-action="written-answer" ${data(key)}>解答・解説を見る</button></div>`:''}`:''}
   ${shown?`<section class="written-answer result ${resultTone}" aria-labelledby="written-answer-${esc(key)}"><h4 id="written-answer-${esc(key)}">${isAutomatic?esc(r.skipped?'未回答':status):'公式解答例'}</h4>${isAutomatic?'<p class="written-answer-label">正答</p>':''}${answers}${source}<details class="written-explanation" ${explanationOpen?'open':''}><summary>解説</summary><div class="explanation rich-question">${questionTextHTML(result.explanation)}</div></details>${isAutomatic?(result.reviewPoint?`<details class="written-rubric"><summary>確認ポイント</summary><p>${esc(result.reviewPoint)}</p></details>`:''):selfEvaluation}</section>`:''}
  </section>`;
 }
 function itemReady(run,item){
  return item.fields.every(field=>{
   const key=item.id+'--'+field.id;
   return run.responses[key]?.submittedAt&&(!mayViewAnswer(run,key)||run.evaluations[key]&&run.assistance.viewedFields.includes(key));
  });
 }
 function studyActions(run,item,result,hasReflection,waitingReview){
  if(waitingReview)return '<div class="finish-actions"><button class="button primary" data-action="written-review-start">答え合わせを始める →</button></div>';
  if(run.progress.status==='completed'&&run.assistance.viewedFields.length===result.total)return completedActions({withReflection:hasReflection});
  const items=run.material.items,index=items.indexOf(item);
  const next=[...items.slice(index+1),...items.slice(0,index)].find(candidate=>!itemReady(run,candidate));
  const nextButton=next&&itemReady(run,item)?`<button class="button primary" data-action="written-item" data-id="${esc(next.id)}">${items.indexOf(next)>index?'次の小問':'残りの小問へ'} →</button>`:'';
  return nextButton?`<div class="finish-actions">${nextButton}</div>`:'';
 }
 function studyHTML(){
  const run=current();
  if(!run)return homeHTML();
  const c=run.material,it=c.items.find(i=>i.id===run.progress.currentItemId)||c.items[0],result=caseResult(run);
  const feedback=feedbackForRun(run);
  const done=run.progress.status==='completed'&&result.total===run.assistance.viewedFields.length;
  const m=metadata(c.id),topic=caseTopicName(c);
  const answerUnit=c.items.some(item=>item.fields.some(field=>field.type==='answerSet'))?'':'欄';
  const hasReflection=!!availableExplanation(run);
  const waitingReview=run.mode==='exam'&&result.submitted===result.total&&!run.assistance.firstAnswerViewedAt;
  const returning=hasReflection&&reflectionReturnRunId===run.id;
  const partial=run.mode==='exam'&&result.submitted>0&&result.submitted<result.total&&run.progress.status!=='partially_completed';
  const earlyEnd=partial?'<details class="assessment-menu"><summary>試験の操作</summary><p class="small muted">回答を確定した欄の答え合わせをします。</p><button class="button secondary" data-action="written-review-partial">試験を終了して答え合わせ</button></details>':'';
  const reflectionAction=hasReflection&&!returning?'<div class="written-reflection-entry"><button class="button primary" data-action="written-reflection-open">大問全体の解説を見る <span aria-hidden="true">→</span></button></div>':'';
  const slots=caseFields(c).filter(x=>x.item.id===it.id);
  const update=answerFormUpdate(run,it.id);
  const updateAction=update?`<div class="written-format-update"><button class="button secondary" data-action="written-use-new-fields">${update.keep?'新しい回答欄で続ける':'新しい回答欄で解き直す'} <span aria-hidden="true">→</span></button></div>`:'';
  const shown=slots.filter(({key})=>run.assistance.viewedFields.includes(key)&&mayViewAnswer(run,key));
  const ai=shown.length?`<div class="ai-explain-entry written-ai-entry">${shown.length>1?`<label>解答欄 <select name="written-ai-field">${shown.map(({key,field})=>`<option value="${esc(key)}">${esc(field.label)}</option>`).join('')}</select></label>`:''}${aiQuestionButton({action:'written-ai',attributes:{'data-written-key':shown.length===1?shown[0].key:undefined}})}</div>`:'';
  const drafts=slots.filter(({key})=>!run.responses[key]?.submittedAt);
  const checkable=drafts.some(({key,field})=>canSubmitCaseField(field,run.responses[key]?.value));
  const batchLabel=run.mode==='exam'&&run.progress.status!=='partially_completed'?'まとめて回答する':'まとめて答え合わせ';
  const individualKey=run.id+'--'+it.id;
  const individualActions=slots.length>1&&drafts.length?`<details class="written-individual-toggle" data-item="${esc(individualKey)}" ${individualActionsKey===individualKey?'open':''}><summary>欄ごとの操作</summary></details>`:'';
  const batchAction=slots.length>1&&drafts.length?`<div class="answer-actions written-batch-actions"><button class="button primary" data-action="written-check-item" data-id="${esc(it.id)}" ${checkable?'':'disabled'}>${batchLabel}</button></div>`:'';
  const itemNavigation=c.items.length>1?`<nav class="written-item-nav" aria-label="小問">${c.items.map(i=>`<button class="button secondary" data-action="written-item" data-id="${esc(i.id)}" aria-current="${it.id===i.id?'step':'false'}">${esc(i.label)}</button>`).join('')}</nav>`:'';
  const nextAction=studyActions(run,it,result,hasReflection,waitingReview);
  const fields=slots.map(slot=>{
   const label=slot.field.label;
   const showLabel=slots.length>1||!it.prompt.trim()&&!['回答','解答','記述'].includes(label);
   return fieldHTML(slot,run,showLabel,waitingReview,feedback);
  }).join('');
  return `<div class="study-toolbar written-toolbar">${studyBackButton({view:'home',label:done?'ホーム':'中断',home:done})}${earlyEnd}${returning?`<button class="button secondary written-reflection-return" data-action="written-reflection-open">振り返りに戻る</button>`:''}${result.total>1?`<p class="page-note">回答 ${result.submitted} / ${result.total}${answerUnit}</p>`:''}</div>
   <header class="written-case-header"><div class="page-heading case-heading"><h1>${esc(c.title)}</h1></div><div class="question-meta case-meta"><span class="badge">${esc(topic)}</span><span>${esc(m.packLabel||'')}${m.number?' · 問'+m.number:''}</span><span class="case-study-scope">${esc(scopeLabel(scopeFor(run)))}</span></div></header>${legalContextHTML(c)}
   <div class="written-conflict-controls">${conflictControls(row(run.id))}</div><div class="written-save-actions" ${pendingDrafts.has(run.id)?'':'hidden'}><button class="button secondary" data-action="written-retry">保存を再試行</button></div>
   <div class="written-mobile-tabs" role="group" aria-label="問題の表示"><button class="button secondary" data-action="written-pane" data-pane="questions" aria-pressed="${run.progress.pane==='questions'}">設問・回答</button><button class="button secondary" data-action="written-pane" data-pane="body" aria-pressed="${run.progress.pane==='body'}">問題文</button></div>
   <div class="written-layout" data-pane="${run.progress.pane}"><section class="panel written-body" tabindex="0" aria-label="共通本文"><h2 class="written-panel-title">問題文</h2><div class="question-stem rich-question">${commonBody(c,feedback)}</div>${originals(c)}</section><section class="panel written-items" aria-label="設問と回答">${itemNavigation}<h2 class="written-panel-title${c.items.length>1?' sr-only':''}">${c.items.length>1?esc(it.label):'回答'}</h2>${it.bodyRefs?.length?`<button class="button quiet" data-action="written-reference" data-ref="${esc(it.bodyRefs[0])}">本文の該当箇所を見る</button>`:''}<div class="question-stem rich-question case-prompt">${questionTextHTML(it.prompt)}</div>${updateAction}${individualActions}${fields}${batchAction}${ai}${reflectionAction}${nextAction}</section></div>`;
 }
 function topicsHTML(){return `<div class="page-heading"><h1>分野から選ぶ</h1></div>${modeHTML()}<div class="case-topics">${caseTopics.map(t=>{const list=eligibleCases().filter(c=>caseTopicId(c)===t.id);if(!list.length)return '';return `<section class="panel case-topic"><button class="field-start" data-action="written-recommend" data-topic="${esc(t.id)}" ${list.some(usable)?'':'disabled'}><span><strong class="field-name">${esc(t.name)}</strong><span class="small muted case-topic-count">${list.length}${esc(countLabel)}</span></span><span class="field-direction"><span class="field-arrow" aria-hidden="true">→</span></span></button><details><summary>問題を選ぶ</summary>${caseRows(list,{topicId:t.id})}</details></section>`;}).join('')}</div>`;}
 function html(){return view==='reflection'&&availableExplanation(current())?reflectionHTML():view==='reflection'?studyHTML():view==='planning'?getPlanViews().planningHTML():view==='study'?studyHTML():view==='topics'?topicsHTML():view==='packs'?packsHTML():view==='pack'?packHTML():['history','review'].includes(view)?historyHTML():homeHTML();}
 async function action(el){const action=el.dataset.action;if(!action?.startsWith('written-'))return false;if(busy)return true;try{busy=true;const key=el.dataset.writtenKey;if(action==='written-recommend')await beginQueue({topicId:el.dataset.topic||null,packId:el.dataset.pack||null});else if(action==='written-sequence')await beginQueue({packId:el.dataset.pack,order:'number'});else if(action==='written-next')await nextCase();
 else if(action==='written-use-new-fields')await switchAnswerForm();
 else if(action==='written-set-add'||action==='written-set-remove')await resizeAnswerSet(el,key,action==='written-set-add');
 else if(action==='written-reflection-open')await openReflection(el.dataset.writtenKey,el.dataset.id);
 else if(action==='written-reflection-jump')jumpToExplanation(el.dataset.id);
 else if(action==='written-reflection-toc'){
  const heading=document.getElementById('written-reflection-toc');
  if(heading){heading.focus({preventScroll:true});heading.scrollIntoView({block:'start'});rememberReflection();}
 }
 else if(action==='written-reflection-expand')expandReflection();
 else if(action==='written-reflection-answer'||action==='written-reflection-study')await returnToStudy(key,el.dataset.pane,el.dataset.ref);
 else if(action==='written-packs'){browsePackId=null;await setView('packs');}else if(action==='written-pack'){browsePackId=el.dataset.pack;await setView('pack');}else if(action==='written-retry')await edit(()=>{});else if(action==='written-plan'){const phase=getPlanViews().activePhase;await beginQueue({topicIds:phase?.focusTopicIds||[]});}else if(action==='written-start'){if(el.dataset.id)await begin(el.dataset.id,el.dataset.mode||studyMode,newScope({topicId:el.dataset.topic||null,packId:el.dataset.pack||null,order:el.dataset.order||'recommended'}));else await beginQueue();}else if(action==='written-resume'){await flush();if(!runs().some(r=>r.id===el.dataset.id))throw Error('この科目の記録が見つかりません。');await resumeRun(runs().find(r=>r.id===el.dataset.id));}else if(action==='written-submit'||action==='written-skip')await submitAndCheck(key,action==='written-skip');
 else if(action==='written-answer'){if(await edit(run=>viewCaseAnswer(run,key)))focusFeedback(key);}
 else if(action==='written-check-item'){
  const id=el.dataset.id;
  if(await edit(run=>checkCaseItem(run,id,undefined,{reveal:run.mode==='learning'||run.progress.status==='partially_completed'})))focusFeedback();
 }
 else if(action==='written-rate'){
  if(await edit(run=>rateCaseField(run,key,el.dataset.outcome))){
   const next=document.querySelector('.written-reflection-entry .primary, .finish-actions .primary');
   focusStudyTarget(next||document.getElementById('written-rating-'+key));
  }
 }
 else if(action==='written-item')await advanceItem(el.dataset.id);
 else if(action==='written-review-start'||action==='written-review-partial')await startExamReview({partial:action==='written-review-partial'});
 else if(action==='written-reference'){await edit(run=>{run.progress.pane='body';run.updatedAt=new Date().toISOString();});document.getElementById('written-ref-'+el.dataset.ref)?.scrollIntoView({block:'start'});}
 else if(action==='written-pane')await edit(run=>{run.progress.pane=el.dataset.pane;run.updatedAt=new Date().toISOString();});
 else if(action==='written-remote'){await flush({allowUncommitted:true});await workspace.resolve(el.dataset.id,false);pendingDrafts.delete(el.dataset.id);draftDOM=pendingDrafts.size>0;rows=await workspace.read();onChanged();onUpdate();}else if(action==='written-fork'){await flush({allowUncommitted:true});const r=row(el.dataset.id),copy=structuredClone(pendingDrafts.get(r.id)||r.payload);copy.id='case--'+crypto.randomUUID();await persist(copy,0);if(contexts[r.id])contexts[copy.id]=structuredClone(contexts[r.id]);await workspace.resolve(r.id,false);pendingDrafts.delete(r.id);draftDOM=pendingDrafts.size>0;if(currentId===r.id)currentId=copy.id;checkpoint();rows=await workspace.read();onChanged();onUpdate();}else if(action==='written-ai'){
  const fieldKey=key||document.querySelector('[name="written-ai-field"]')?.value,run=current();
  if(fieldKey&&run?.assistance.viewedFields.includes(fieldKey)&&mayViewAnswer(run,fieldKey)){aiKey=fieldKey;return {ai:true};}
 }}catch(error){onNotice(error.message);}finally{busy=false;}return true;}
 async function resizeAnswerSet(el,key,add){
  const run=current(),slot=run&&caseFields(run.material).find(slot=>slot.key===key);
  if(slot?.field.type!=='answerSet'||slot.field.choices||slot.field.answerSet.slots||run.responses[key]?.submittedAt)return;
  const controls=el.closest('[data-answer-set]').querySelectorAll('[data-answer-set-entry]');
  const values=[...controls].map(input=>input.value);
  const index=add?values.length:Number(el.dataset.index);
  if(add?values.length>=MAX_ANSWER_SET_INPUTS:values.length<=1||!Number.isInteger(index)||index<0||index>=values.length)return;
  if(add)values.push('');else values.splice(index,1);
  el.focus({preventScroll:true});
  if(await edit(r=>setCaseResponse(r,key,JSON.stringify(values)))){
   const entries=document.querySelectorAll(`[data-answer-set-entry][data-written-key="${CSS.escape(key)}"]`);
   entries[Math.min(index,entries.length-1)]?.focus();
  }
 }
 function input(el){
  if(el.matches('[name=written-study-mode]')){studyMode=el.value==='exam'?'exam':'learning';checkpoint();return true;}
  if(!el.matches('textarea[data-written-key],input[data-written-key],select[data-answer-set-entry]'))return false;
  const key=el.dataset.writtenKey;
  const group=el.closest('[data-answer-set]');
  let value=el.value,ready=Boolean(value.trim());
  if(group){
   const entries=[...group.querySelectorAll('[data-answer-set-entry],[data-answer-set-choice]:checked')].map(input=>input.value);
   value=JSON.stringify(entries);
   const slot=caseFields(current().material).find(slot=>slot.key===key);
   ready=canSubmitCaseField(slot.field,value);
   if(el.type==='checkbox')el.closest('.choice').classList.toggle('selected',el.checked);
  }
  const submit=el.closest('.written-field')?.querySelector('[data-action=written-submit]');
  if(submit)submit.disabled=!ready;
  const batch=document.querySelector('[data-action=written-check-item]');
  if(batch)batch.disabled=!document.querySelector('.written-items [data-action=written-submit]:not(:disabled)');
  const count=el.closest('label')?.querySelector('.written-count');if(count)count.textContent=`${[...value].length} / ${el.maxLength}字`;
  draftDOM=true;edit(r=>setCaseResponse(r,key,value),{render:false});return true;
 }
 function trackPageScroll(){if(view==='reflection'){rememberReflection();return;}if(view!=='study'||!current())return;const offset=window.scrollY,key=matchMedia('(max-width:1000px)').matches&&current().progress.pane==='body'?'bodyScroll':'questionScroll';edit(r=>{r.progress[key]=offset;},{render:false,remember:false});}
 function restoreDOM(){
  if(view==='reflection'&&availableExplanation(current())){restoreReflectionDOM();return;}
  const run=current();
  if(!run||!['study','reflection'].includes(view))return;
  const key=matchMedia('(max-width:1000px)').matches&&run.progress.pane==='body'?'bodyScroll':'questionScroll';
  window.scrollTo(0,run.progress[key]);
  const toggle=document.querySelector('.written-individual-toggle');
  toggle?.addEventListener('toggle',()=>{
   if(toggle.isConnected)individualActionsKey=toggle.open?toggle.dataset.item:null;
  });
  const panel=document.querySelector('.written-body');
  if(panel){
   panel.scrollTop=run.progress.bodyScroll;
   panel.addEventListener('scroll',()=>{
    const offset=panel.scrollTop;
    edit(r=>{r.progress.bodyScroll=offset;},{render:false,remember:false});
   },{passive:true});
  }
 }
 function backupContexts(){const all={};if(activeIdentity)for(const p of qualification.examParts.filter(p=>p.unit==='cases')){try{Object.assign(all,JSON.parse(localStorage.getItem(checkpointKey(activeIdentity,p.id)))?.contexts||{});}catch{}}Object.assign(all,contexts);return Object.fromEntries(Object.entries(all).filter(([id,s])=>allRuns().some(r=>r.id===id&&r.examPartId===s?.examPartId)&&validCaseScope(s,qualification,catalog())));}
 function backup(){return {format:'hitomon-case-backup',version:2,qualificationId:qualification.id,runs:allRuns().map(r=>pendingDrafts.get(r.id)||r),studyContexts:structuredClone(backupContexts()),activeRunId:currentId};}
 function validateBackup(value){if(value===undefined)return;if(value.format!=='hitomon-case-backup'||value.version!==2||value.qualificationId!==qualification.id||!Array.isArray(value.runs)||value.runs.length>10000||new Set(value.runs.map(r=>r.id)).size!==value.runs.length)throw Error('大問のバックアップを確認できません。');if(value.activeRunId!=null&&!value.runs.some(r=>r.id===value.activeRunId))throw Error('再開する記録のバックアップを確認できません。');if(value.studyContexts!==undefined&&(!value.studyContexts||typeof value.studyContexts!=='object'||Array.isArray(value.studyContexts)||Object.keys(value.studyContexts).length>10000||Object.entries(value.studyContexts).some(([id,s])=>!value.runs.some(r=>r.id===id&&r.examPartId===s.examPartId)||!validCaseScope(s,qualification,catalog()))))throw Error('出題範囲のバックアップを確認できません。');for(const r of value.runs){validate('case',r);if(row(r.id)&&canonical(row(r.id).payload)!==canonical(r))throw Error('同じIDの異なる大問記録があります。');}}
 async function guestRuns(){const identity=await getStore().identity(),guest=createWorkspaceStore({...identity,owner:'guest:'+identity.deviceId,rootPath,namespaceName:'written',validate});try{const found=await guest.read();if(guest.error())throw guest.error();return found.map(r=>r.payload);}finally{await guest.close();}}
 async function restoreBackup(value){validateBackup(value);if(!value)return;for(const r of value.runs)if(!row(r.id))await persist(r,0);for(const [id,s] of Object.entries(value.studyContexts||{})){if(s.examPartId===partId())contexts[id]=s;else if(activeIdentity){const key=checkpointKey(activeIdentity,s.examPartId);let cp={};try{cp=JSON.parse(localStorage.getItem(key))||{};}catch{}cp.contexts={...cp.contexts,[id]:s};localStorage.setItem(key,JSON.stringify(cp));}}if(value.activeRunId&&runs().some(r=>r.id===value.activeRunId))currentId=value.activeRunId;checkpoint();}
 return {refreshAvailability,guestRuns,trackPageScroll,bind,flush,html,action,input,restoreDOM,current,runs,allRuns,setView,view:()=>view,isBusy:()=>busy,hasUnsaved:()=>draftDOM,store:()=>workspace,backup,validateBackup,restoreBackup,onRows:async()=>{try{await flush();const before=current()?.progress,latest=await workspace.read();rows=latest;const conflict=document.querySelector('.written-conflict-controls');if(conflict)conflict.innerHTML=conflictControls(row(currentId));if(before&&current())current().progress={...current().progress,currentItemId:before.currentItemId,pane:before.pane,bodyScroll:before.bodyScroll,questionScroll:before.questionScroll};/* remote cursor doesn't change foreground item/view; don't rerender active input */if(!document.activeElement?.matches('[data-written-key]'))onUpdate();}catch(error){onNotice(error.message);}},aiSnapshot:()=>{const run=current(),r=run?.responses[aiKey];if(!run||!r||!mayViewAnswer(run,aiKey))return null;const slot=caseFields(run.material).find(entry=>entry.key===aiKey);return {question:run.material,attempt:{status:'revealed',fieldKey:aiKey,response:structuredClone(r),feedback:feedbackForSlot(slot,feedbackForRun(run)),selfAssessment:run.evaluations[aiKey]?.source!=='automatic'}};}};
}
