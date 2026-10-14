import {isMultiple,validResponse,canonicalIds,canSubmitIds,correctIds,sameChoices} from './question-format.js';
import {createAttempt,selectAnswer,finalizeAttempt,toggleChoice} from './study.js';
import {questionFamily,questionKind,canUseQuestion} from './content-policy.js';
import {validAssessmentSize,validSelectionPolicy,diagnosticPolicy} from './assessment-policy.js';
import {weightedQuotas} from './assessment-sampling.js';
export function createAssessment(questions,qualification,attempts=[],catalogRevision='',{mode='diagnostic'}={}){
 if(!validAssessmentSize(questions.length)||new Set(questions.map(q=>q.id)).size!==questions.length||questions.some(q=>q.qualificationId!==qualification.id||!canUseQuestion(q,mode)))throw new Error('受験する問題の用途・件数を確認できません。');
 const startedAt=new Date().toISOString(),seen=new Set(attempts.map(a=>a.questionId));
 return {id:crypto.randomUUID(),qualificationId:qualification.id,version:1,blueprintVersion:Math.max(4,qualification.diagnosticBlueprint?.version||4),selectionPolicy:diagnosticPolicy(qualification),catalogRevision,assistance:'none',feedback:'after-finish',size:questions.length,status:'in_progress',startedAt,completedAt:null,currentIndex:0,currentChoiceId:null,responses:{},slots:questions.map(q=>({id:crypto.randomUUID(),attempt:createAttempt(q,{at:startedAt,diagnostic:true}),previouslySeen:seen.has(q.id),kind:questionKind(q),parentQuestionId:q.parentQuestionId||null,parentPreviouslySeen:q.parentQuestionId?seen.has(q.parentQuestionId):null}))};
}
export function submitAssessment(run,choiceId){
 if(run.status!=='in_progress')throw new Error('終了した診断には回答できません。');
 const slot=run.slots[run.currentIndex];if(Object.hasOwn(run.responses,slot.id))throw new Error('この回答は確定しています。');
 if(choiceId!==null&&(!validResponse(slot.attempt.questionSnapshot,choiceId)||!canSubmitIds(slot.attempt.questionSnapshot,Array.isArray(choiceId)?choiceId:[choiceId])))throw new Error('有効な選択肢を選んでください。');
 run.responses[slot.id]=Array.isArray(choiceId)?[...choiceId]:choiceId;run.currentChoiceId=null;
 if(run.currentIndex<run.size-1)run.currentIndex++;else finishAssessment(run);
 return run;
}
export function finishAssessment(run){
 if(run.status!=='in_progress')return run;
 run.status=Object.keys(run.responses).length===run.size?'completed':'ended_early';run.completedAt=new Date().toISOString();run.currentChoiceId=null;return run;
}
// Results are derived from the finalized run, rather than duplicated in the
// attempt outbox. A run has one canonical slot per question across devices.
const resultsCache=new WeakMap();
export function assessmentAttempts(run){
 if(run.status==='in_progress')return [];
 if(resultsCache.has(run))return resultsCache.get(run);
 const result=run.slots.filter(s=>Object.hasOwn(run.responses,s.id)&&run.responses[s.id]!==null).map(s=>{const a=structuredClone(s.attempt);a.id=s.id;const q=a.questionSnapshot,response=run.responses[s.id];if(isMultiple(q)){for(const id of response)toggleChoice(a,id,true);}else selectAnswer(a,q.choices.findIndex(c=>c.id===response));finalizeAttempt(a,sameChoices(Array.isArray(response)?response:[response],correctIds(q))?'correct':'incorrect',run.completedAt);a.diagnosticRunId=run.id;return a;});
 resultsCache.set(run,result);return result;
}
export function assessmentExposure(run){
 return run.slots.filter((slot,i)=>i<=run.currentIndex||Object.hasOwn(run.responses,slot.id)).map(slot=>({questionId:slot.attempt.questionId,qualificationId:run.qualificationId,exposedAt:run.completedAt||run.startedAt}));
}
export function assessmentResult(run,qualification){
 const attempts=assessmentAttempts(run),correct=attempts.filter(a=>a.status==='correct').length;
 const sourceCounts=slots=>['original','authored','derived'].map(kind=>{const selected=slots.filter(s=>(s.kind||(questionKind(s.attempt.questionSnapshot)))===kind),ids=new Set(selected.map(s=>s.id)),answered=attempts.filter(a=>ids.has(a.id));return {kind,selected:selected.length,answered:answered.length,correct:answered.filter(a=>a.status==='correct').length,previouslySeen:selected.filter(s=>s.previouslySeen).length,parentPreviouslySeen:selected.filter(s=>s.parentPreviouslySeen).length};});
 const byId=new Map(attempts.map(a=>[a.id,a]));
 const topics=new Map();
 for(const s of run.slots){const q=s.attempt.questionSnapshot;topics.set(q.topicId,{id:q.topicId,name:q.topic||topics.get(q.topicId)?.name||q.topicId});}
 const items=run.slots.map((s,i)=>{const q=s.attempt.questionSnapshot;return {questionId:q.id,questionVersion:q.version,...(isMultiple(q)?{type:q.type,selection:structuredClone(q.selection),grading:structuredClone(q.grading||{method:'exactChoiceSet'}),selectedChoiceIds:byId.get(s.id)?.selectedChoiceIds||[]}:{}),...Object.fromEntries(['syllabusId','syllabus','language','objectiveIds','objectivesSnapshot','sourceRefs'].filter(k=>q[k]!==undefined).map(k=>[k,structuredClone(q[k])])),topicId:q.topicId,kind:s.kind||questionKind(q),parentQuestionId:s.parentQuestionId||null,previouslySeen:s.previouslySeen,parentPreviouslySeen:s.parentPreviouslySeen??null,exposed:i<=run.currentIndex||Object.hasOwn(run.responses,s.id),skipped:Object.hasOwn(run.responses,s.id)&&run.responses[s.id]===null,outcome:byId.get(s.id)?.status||'unanswered'};});
 return {id:run.id,status:run.status,completedAt:run.completedAt,size:run.size,answered:attempts.length,correct,incorrect:attempts.length-correct,unanswered:run.size-attempts.length,exposed:assessmentExposure(run).length,skipped:Object.values(run.responses).filter(value=>value===null).length,correctRate:attempts.length?correct/attempts.length:null,previouslySeen:run.slots.filter(s=>s.previouslySeen).length,assistance:'none',blueprintVersion:run.blueprintVersion,selectionPolicy:run.selectionPolicy?structuredClone(run.selectionPolicy):null,catalogRevision:run.catalogRevision,composition:sourceCounts(run.slots),items,topics:[...topics.values()].map(t=>{const rows=attempts.filter(a=>a.questionSnapshot.topicId===t.id);return {topicId:t.id,label:t.name,answered:rows.length,correct:rows.filter(a=>a.status==='correct').length,composition:sourceCounts(run.slots.filter(s=>s.attempt.questionSnapshot.topicId===t.id))};})};
}
export function assessmentSlots(run){
 return run.slots.map((s,i)=>{const answered=Object.hasOwn(run.responses,s.id),choice=answered?run.responses[s.id]:i===run.currentIndex&&run.status==='in_progress'?run.currentChoiceId:null;return {...s,selectedChoiceId:choice,submitted:answered&&choice!==null,skipped:answered&&choice===null};});
}
export function validateAssessment(run,qualification,validateAttempt,{size,diagnostic=false}){
 const fail=()=>{throw new Error('診断データの形式を確認できません。記録は変更していません。');};
 const ids=new Set(),questions=new Set(),families=new Set();
 if(!validAssessmentSize(size)||!run||run.version!==1||run.qualificationId!==qualification.id||typeof run.id!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(run.id)||run.size!==size||!Array.isArray(run.slots)||run.slots.length!==size||run.assistance!=='none'||run.feedback!=='after-finish'||!['in_progress','completed','ended_early'].includes(run.status)||!Number.isInteger(run.currentIndex)||run.currentIndex<0||run.currentIndex>=size||typeof run.startedAt!=='string'||Number.isNaN(Date.parse(run.startedAt))||run.status==='in_progress'&&run.completedAt!==null||run.status!=='in_progress'&&Number.isNaN(Date.parse(run.completedAt))||!run.responses||typeof run.responses!=='object'||Array.isArray(run.responses))fail();
 if(!Number.isInteger(run.blueprintVersion)||run.blueprintVersion<1||run.blueprintVersion>10000||typeof run.catalogRevision!=='string'||run.catalogRevision.length>200)fail();
 if(diagnostic&&run.blueprintVersion>=2&&!validSelectionPolicy(run.selectionPolicy,size))fail();
 for(const slot of run.slots){
  if(!slot||typeof slot.previouslySeen!=='boolean'||typeof slot.id!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(slot.id)||ids.has(slot.id))fail();ids.add(slot.id);
  const a=slot.attempt;validateAttempt(a);
  const q=a.questionSnapshot,family=questionFamily(q);
  // A saved question and policy retain their scope even if the catalog changes.
  if(typeof q.topicId!=='string'||!q.topicId||typeof q.examPartId!=='string'||!q.examPartId||!canUseQuestion(q,diagnostic?'diagnostic':'mock'))fail();
  if(!diagnostic||run.blueprintVersion>=2){if(slot.kind!==questionKind(q)||slot.parentQuestionId!==(q.parentQuestionId||null)||(q.parentQuestionId?typeof slot.parentPreviouslySeen!=='boolean':slot.parentPreviouslySeen!==null)||families.has(family))fail();families.add(family);}else if(!canUseQuestion(q,'practice'))fail();
  if(a.status!=='in_progress'||a.hintCount!==0||a.hintEvents.length||a.answerViewedBefore||a.selected!==null||(a.selectedChoiceIds?.length||0)>0||questions.has(a.questionId)||a.qualificationId!==qualification.id)fail();questions.add(a.questionId);
  if(Object.hasOwn(run.responses,slot.id)&&run.responses[slot.id]!==null&&(!validResponse(q,run.responses[slot.id])||!canSubmitIds(q,Array.isArray(run.responses[slot.id])?run.responses[slot.id]:[run.responses[slot.id]])))fail();
 }
 if(diagnostic&&run.selectionPolicy){
  const p=run.selectionPolicy,topics=new Set(run.slots.map(s=>s.attempt.questionSnapshot.topicId));
  for(const id of topics){const limit=Object.hasOwn(p.variantLimits,id)?p.variantLimits[id]:p.defaultVariantLimit;
   if(run.slots.filter(s=>s.kind==='derived'&&s.attempt.questionSnapshot.topicId===id).length>limit)fail();}
  if(p.sampling==='topic-weighted'){
   const quotas=weightedQuotas(p.weights,size);
   if([...topics].some(id=>!quotas.has(id))||[...quotas].some(([id,n])=>run.slots.filter(s=>s.attempt.questionSnapshot.topicId===id).length!==n))fail();
  }
 }
 if(Object.keys(run.responses).some(id=>!ids.has(id)))fail();
 if(run.status!=='in_progress'&&run.currentChoiceId!==null)fail();
 if(run.currentChoiceId!==null&&!validResponse(run.slots[run.currentIndex].attempt.questionSnapshot,run.currentChoiceId,{empty:true}))fail();
 for(let i=0;i<run.currentIndex;i++)if(!Object.hasOwn(run.responses,run.slots[i].id))fail();
 if(run.status==='in_progress'&&run.slots.slice(run.currentIndex).some(s=>Object.hasOwn(run.responses,s.id)))fail();
 if(run.status==='completed'&&Object.keys(run.responses).length!==size)fail();
 return structuredClone(run);
}

export function chooseAssessment(run,id,checked=true){
 if(run.status!=='in_progress'||Object.hasOwn(run.responses,run.slots[run.currentIndex].id))throw Error('この回答は確定しています。');
 const q=run.slots[run.currentIndex].attempt.questionSnapshot;if(!q.choices.some(c=>c.id===id))throw Error('選択肢を確認できません。');
 if(!isMultiple(q)){run.currentChoiceId=id;return;}
 const ids=new Set(run.currentChoiceId||[]);if(checked)ids.add(id);else ids.delete(id);run.currentChoiceId=canonicalIds(q,[...ids]);
}
