import {createAttempt,selectAnswer,finalizeAttempt} from './study.js';
import {examPartsFor} from './planning.js';
export const DIAGNOSTIC_SIZE=30;
export const DIAGNOSTIC_BLUEPRINT_VERSION=2;
export const diagnosticFamily=q=>q.diagnosticOnly?q.parentQuestionId:q.id;
const shuffle=(items,random)=>{const a=[...items];for(let i=a.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
const policyFor=qualification=>({sampling:'topic-round-robin',defaultVariantLimit:1,variantLimits:structuredClone(qualification.diagnosticBlueprint?.variantLimits||{}),preference:['unseen-derived','unseen-original','seen-derived','seen-original']});
export function selectDiagnostic(questions,qualification,attempts=[],random=Math.random,variants=[]){
 const supported=new Set(examPartsFor(qualification).filter(p=>p.practiceAvailable).map(p=>p.id));
 const originals=questions.filter(q=>!q.diagnosticOnly&&supported.has(q.examPartId||qualification.defaultExamPartId||'objective'));
 const byId=new Map(originals.map(q=>[q.id,q])),validTopics=new Set(qualification.topics.map(t=>t.id));
 if(new Set(variants.map(q=>q.id)).size!==variants.length||variants.some(q=>!q.diagnosticOnly||!byId.has(q.parentQuestionId)||byId.has(q.id)||q.topicId!==byId.get(q.parentQuestionId).topicId||(q.examPartId||qualification.defaultExamPartId||'objective')!==(byId.get(q.parentQuestionId).examPartId||qualification.defaultExamPartId||'objective')))throw new Error('診断専用教材の元問題・分野・パートを確認できません。');
 const eligible=[...originals,...variants];
 if(eligible.length<DIAGNOSTIC_SIZE)throw new Error('診断には対象パートの問題が30問以上必要です。通常学習は利用できます。');
 if(eligible.some(q=>!validTopics.has(q.topicId))||new Set(eligible.map(diagnosticFamily)).size<DIAGNOSTIC_SIZE)throw new Error('診断には元問題が異なる30問以上必要です。通常学習は利用できます。');
 const seen=new Set(attempts.map(a=>a.questionId));
 const priority=q=>(seen.has(q.id)?2:0)+(q.diagnosticOnly?0:1);
 const topics=shuffle(qualification.topics.map(t=>t.id),random),groups=new Map(topics.map(id=>[id,shuffle(eligible.filter(q=>q.topicId===id),random).sort((a,b)=>priority(a)-priority(b))]));
 const result=[],families=new Set(),variantCounts=new Map(),limits=qualification.diagnosticBlueprint?.variantLimits||{};
 for(const [topic,limit] of Object.entries(limits))if(!validTopics.has(topic)||!Number.isInteger(limit)||limit<0||limit>DIAGNOSTIC_SIZE)throw new Error('診断の派生問題配分を確認できません。');
 while(result.length<DIAGNOSTIC_SIZE){let added=false;for(const topic of topics){const group=groups.get(topic),limit=limits[topic]??1,index=group.findIndex(q=>!families.has(diagnosticFamily(q))&&(!q.diagnosticOnly||(variantCounts.get(topic)||0)<limit));if(index!==-1){const [q]=group.splice(index,1);families.add(diagnosticFamily(q));if(q.diagnosticOnly)variantCounts.set(topic,(variantCounts.get(topic)||0)+1);result.push(q);added=true;if(result.length===DIAGNOSTIC_SIZE)break;}}if(!added)throw new Error('診断の30問を分野別に用意できません。通常学習は利用できます。');}
 return shuffle(result,random);
}
export function createDiagnostic(questions,qualification,attempts=[],catalogRevision=''){
 if(questions.length!==DIAGNOSTIC_SIZE||new Set(questions.map(q=>q.id)).size!==DIAGNOSTIC_SIZE||new Set(questions.map(diagnosticFamily)).size!==DIAGNOSTIC_SIZE)throw new Error('診断は元問題が異なる30問で開始してください。');
 const startedAt=new Date().toISOString(),seen=new Set(attempts.map(a=>a.questionId));
 return {id:crypto.randomUUID(),qualificationId:qualification.id,version:1,blueprintVersion:Math.max(DIAGNOSTIC_BLUEPRINT_VERSION,qualification.diagnosticBlueprint?.version||DIAGNOSTIC_BLUEPRINT_VERSION),selectionPolicy:policyFor(qualification),catalogRevision,assistance:'none',feedback:'after-finish',size:DIAGNOSTIC_SIZE,status:'in_progress',startedAt,completedAt:null,currentIndex:0,currentChoiceId:null,responses:{},slots:questions.map(q=>({id:crypto.randomUUID(),attempt:createAttempt(q,{at:startedAt,diagnostic:true}),previouslySeen:seen.has(q.id),kind:q.diagnosticOnly?'derived':'original',parentQuestionId:q.diagnosticOnly?q.parentQuestionId:null,parentPreviouslySeen:q.diagnosticOnly?seen.has(q.parentQuestionId):null}))};
}
export function submitDiagnostic(run,choiceId){
 if(run.status!=='in_progress')throw new Error('終了した診断には回答できません。');
 const slot=run.slots[run.currentIndex];if(Object.hasOwn(run.responses,slot.id))throw new Error('この回答は確定しています。');
 if(choiceId!==null&&!slot.attempt.questionSnapshot.choices.some(c=>c.id===choiceId))throw new Error('有効な選択肢を選んでください。');
 run.responses[slot.id]=choiceId;run.currentChoiceId=null;
 if(run.currentIndex<run.size-1)run.currentIndex++;else finishDiagnostic(run);
 return run;
}
export function finishDiagnostic(run){
 if(run.status!=='in_progress')return run;
 run.status=Object.keys(run.responses).length===run.size?'completed':'ended_early';run.completedAt=new Date().toISOString();run.currentChoiceId=null;return run;
}
// Results are derived from the finalized run, rather than duplicated in the
// attempt outbox. A run has one canonical slot per question across devices.
const resultsCache=new WeakMap();
export function diagnosticAttempts(run){
 if(run.status==='in_progress')return [];
 if(resultsCache.has(run))return resultsCache.get(run);
 const result=run.slots.filter(s=>Object.hasOwn(run.responses,s.id)&&run.responses[s.id]!==null).map(s=>{const a=structuredClone(s.attempt);a.id=s.id;selectAnswer(a,a.questionSnapshot.choices.findIndex(c=>c.id===run.responses[s.id]));finalizeAttempt(a,run.responses[s.id]===a.questionSnapshot.correctChoiceId?'correct':'incorrect',run.completedAt);a.diagnosticRunId=run.id;return a;});
 resultsCache.set(run,result);return result;
}
export function diagnosticResult(run,qualification){
 const attempts=diagnosticAttempts(run),correct=attempts.filter(a=>a.status==='correct').length;
 const sourceCounts=slots=>['original','derived'].map(kind=>{const selected=slots.filter(s=>(s.kind||(s.attempt.questionSnapshot.diagnosticOnly?'derived':'original'))===kind),ids=new Set(selected.map(s=>s.id)),answered=attempts.filter(a=>ids.has(a.id));return {kind,selected:selected.length,answered:answered.length,correct:answered.filter(a=>a.status==='correct').length,previouslySeen:selected.filter(s=>s.previouslySeen).length,parentPreviouslySeen:selected.filter(s=>s.parentPreviouslySeen).length};});
 const byId=new Map(attempts.map(a=>[a.id,a]));
 const items=run.slots.map(s=>{const q=s.attempt.questionSnapshot;return {questionId:q.id,questionVersion:q.version,topicId:q.topicId,kind:s.kind||'original',parentQuestionId:s.parentQuestionId||null,previouslySeen:s.previouslySeen,parentPreviouslySeen:s.parentPreviouslySeen??null,outcome:byId.get(s.id)?.status||'unanswered'};});
 return {id:run.id,status:run.status,completedAt:run.completedAt,size:run.size,answered:attempts.length,correct,incorrect:attempts.length-correct,unanswered:run.size-attempts.length,correctRate:attempts.length?correct/attempts.length:null,previouslySeen:run.slots.filter(s=>s.previouslySeen).length,assistance:'none',blueprintVersion:run.blueprintVersion,selectionPolicy:run.selectionPolicy?structuredClone(run.selectionPolicy):null,catalogRevision:run.catalogRevision,composition:sourceCounts(run.slots),items,topics:qualification.topics.map(t=>{const rows=attempts.filter(a=>a.questionSnapshot.topicId===t.id);return {topicId:t.id,label:t.name,answered:rows.length,correct:rows.filter(a=>a.status==='correct').length,composition:sourceCounts(run.slots.filter(s=>s.attempt.questionSnapshot.topicId===t.id))};})};
}
export function diagnosticSlots(run){
 return run.slots.map((s,i)=>{const answered=Object.hasOwn(run.responses,s.id),choice=answered?run.responses[s.id]:i===run.currentIndex&&run.status==='in_progress'?run.currentChoiceId:null;return {...s,selectedChoiceId:choice,submitted:answered&&choice!==null,skipped:answered&&choice===null};});
}
export function validateDiagnostic(run,qualification,validateAttempt){
 const fail=()=>{throw new Error('診断データの形式を確認できません。記録は変更していません。');};
 const ids=new Set(),questions=new Set(),families=new Set();
 if(!run||run.version!==1||run.qualificationId!==qualification.id||typeof run.id!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(run.id)||run.size!==30||!Array.isArray(run.slots)||run.slots.length!==30||run.assistance!=='none'||run.feedback!=='after-finish'||!['in_progress','completed','ended_early'].includes(run.status)||!Number.isInteger(run.currentIndex)||run.currentIndex<0||run.currentIndex>=30||typeof run.startedAt!=='string'||Number.isNaN(Date.parse(run.startedAt))||run.status==='in_progress'&&run.completedAt!==null||run.status!=='in_progress'&&Number.isNaN(Date.parse(run.completedAt))||!run.responses||typeof run.responses!=='object'||Array.isArray(run.responses))fail();
 if(!Number.isInteger(run.blueprintVersion)||run.blueprintVersion<1||run.blueprintVersion>10000||typeof run.catalogRevision!=='string'||run.catalogRevision.length>200)fail();
 if(run.blueprintVersion>=DIAGNOSTIC_BLUEPRINT_VERSION){const p=run.selectionPolicy;if(!p||Object.keys(p).some(k=>!['sampling','defaultVariantLimit','variantLimits','preference'].includes(k))||p.sampling!=='topic-round-robin'||p.defaultVariantLimit!==1||JSON.stringify(p.preference)!==JSON.stringify(policyFor(qualification).preference)||!p.variantLimits||typeof p.variantLimits!=='object'||Array.isArray(p.variantLimits)||Object.entries(p.variantLimits).some(([id,n])=>!qualification.topics.some(t=>t.id===id)||!Number.isInteger(n)||n<0||n>30))fail();}
 for(const slot of run.slots){
  if(!slot||typeof slot.previouslySeen!=='boolean'||typeof slot.id!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(slot.id)||ids.has(slot.id))fail();ids.add(slot.id);
  const a=slot.attempt;validateAttempt(a);
  const q=a.questionSnapshot,family=diagnosticFamily(q);
  if(!qualification.topics.some(t=>t.id===q.topicId)||!examPartsFor(qualification).some(p=>p.practiceAvailable&&p.id===(q.examPartId||qualification.defaultExamPartId||'objective')))fail();
  if(run.blueprintVersion>=DIAGNOSTIC_BLUEPRINT_VERSION){if(slot.kind!==(q.diagnosticOnly?'derived':'original')||slot.parentQuestionId!==(q.diagnosticOnly?q.parentQuestionId:null)||(q.diagnosticOnly?typeof slot.parentPreviouslySeen!=='boolean':slot.parentPreviouslySeen!==null)||families.has(family))fail();families.add(family);}else if(q.diagnosticOnly)fail();
  if(a.status!=='in_progress'||a.hintCount!==0||a.hintEvents.length||a.answerViewedBefore||a.selected!==null||questions.has(a.questionId)||a.qualificationId!==qualification.id)fail();questions.add(a.questionId);
  if(Object.hasOwn(run.responses,slot.id)&&run.responses[slot.id]!==null&&!a.questionSnapshot.choices.some(c=>c.id===run.responses[slot.id]))fail();
 }
 if(run.selectionPolicy&&qualification.topics.some(t=>run.slots.filter(s=>s.kind==='derived'&&s.attempt.questionSnapshot.topicId===t.id).length>(run.selectionPolicy.variantLimits[t.id]??1)))fail();
 if(Object.keys(run.responses).some(id=>!ids.has(id)))fail();
 if(run.currentChoiceId!==null&&!run.slots[run.currentIndex].attempt.questionSnapshot.choices.some(c=>c.id===run.currentChoiceId))fail();
 for(let i=0;i<run.currentIndex;i++)if(!Object.hasOwn(run.responses,run.slots[i].id))fail();
 if(run.status==='in_progress'&&run.slots.slice(run.currentIndex).some(s=>Object.hasOwn(run.responses,s.id)))fail();
 if(run.status==='completed'&&Object.keys(run.responses).length!==30)fail();
 return structuredClone(run);
}
