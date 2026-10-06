import {createAttempt,selectAnswer,finalizeAttempt} from './study.js';
import {examPartsFor} from './planning.js';
export const DIAGNOSTIC_SIZE=30;
const shuffle=(items,random)=>{const a=[...items];for(let i=a.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;};
export function selectDiagnostic(questions,qualification,attempts=[],random=Math.random){
 const supported=new Set(examPartsFor(qualification).filter(p=>p.practiceAvailable).map(p=>p.id));
 const eligible=questions.filter(q=>supported.has(q.examPartId||qualification.defaultExamPartId||'objective'));
 if(eligible.length<DIAGNOSTIC_SIZE)throw new Error('診断には対象パートの問題が30問以上必要です。通常学習は利用できます。');
 const seen=new Set(attempts.map(a=>a.questionId));
 const topics=shuffle(qualification.topics.map(t=>t.id),random),groups=new Map(topics.map(id=>[id,shuffle(eligible.filter(q=>q.topicId===id),random).sort((a,b)=>Number(seen.has(a.id))-Number(seen.has(b.id)))]));
 const result=[];
 while(result.length<DIAGNOSTIC_SIZE){let added=false;for(const topic of topics){const q=groups.get(topic).shift();if(q){result.push(q);added=true;if(result.length===DIAGNOSTIC_SIZE)break;}}if(!added)throw new Error('診断対象の分野分類を確認できません。');}
 return shuffle(result,random);
}
export function createDiagnostic(questions,qualification,attempts=[],catalogRevision=''){
 if(questions.length!==DIAGNOSTIC_SIZE||new Set(questions.map(q=>q.id)).size!==DIAGNOSTIC_SIZE)throw new Error('診断は異なる30問で開始してください。');
 const startedAt=new Date().toISOString(),seen=new Set(attempts.map(a=>a.questionId));
 return {id:crypto.randomUUID(),qualificationId:qualification.id,version:1,blueprintVersion:1,catalogRevision,assistance:'none',feedback:'after-finish',size:DIAGNOSTIC_SIZE,status:'in_progress',startedAt,completedAt:null,currentIndex:0,currentChoiceId:null,responses:{},slots:questions.map(q=>({id:crypto.randomUUID(),attempt:createAttempt(q,{at:startedAt}),previouslySeen:seen.has(q.id)}))};
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
 return {id:run.id,status:run.status,completedAt:run.completedAt,size:run.size,answered:attempts.length,correct,incorrect:attempts.length-correct,unanswered:run.size-attempts.length,correctRate:attempts.length?correct/attempts.length:null,previouslySeen:run.slots.filter(s=>s.previouslySeen).length,assistance:'none',topics:qualification.topics.map(t=>{const rows=attempts.filter(a=>a.questionSnapshot.topicId===t.id);return {topicId:t.id,label:t.name,answered:rows.length,correct:rows.filter(a=>a.status==='correct').length};})};
}
export function diagnosticSlots(run){
 return run.slots.map((s,i)=>{const answered=Object.hasOwn(run.responses,s.id),choice=answered?run.responses[s.id]:i===run.currentIndex&&run.status==='in_progress'?run.currentChoiceId:null;return {...s,selectedChoiceId:choice,submitted:answered&&choice!==null,skipped:answered&&choice===null};});
}
export function validateDiagnostic(run,qualification,validateAttempt){
 const fail=()=>{throw new Error('診断データの形式を確認できません。記録は変更していません。');};
 const ids=new Set(),questions=new Set();
 if(!run||run.version!==1||run.qualificationId!==qualification.id||typeof run.id!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(run.id)||run.size!==30||!Array.isArray(run.slots)||run.slots.length!==30||run.assistance!=='none'||run.feedback!=='after-finish'||!['in_progress','completed','ended_early'].includes(run.status)||!Number.isInteger(run.currentIndex)||run.currentIndex<0||run.currentIndex>=30||typeof run.startedAt!=='string'||Number.isNaN(Date.parse(run.startedAt))||run.status==='in_progress'&&run.completedAt!==null||run.status!=='in_progress'&&Number.isNaN(Date.parse(run.completedAt))||!run.responses||typeof run.responses!=='object'||Array.isArray(run.responses))fail();
 for(const slot of run.slots){
  if(!slot||typeof slot.previouslySeen!=='boolean'||typeof slot.id!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(slot.id)||ids.has(slot.id))fail();ids.add(slot.id);
  const a=slot.attempt;validateAttempt(a);
  if(a.status!=='in_progress'||a.hintCount!==0||a.hintEvents.length||a.answerViewedBefore||a.selected!==null||questions.has(a.questionId)||a.qualificationId!==qualification.id)fail();questions.add(a.questionId);
  if(Object.hasOwn(run.responses,slot.id)&&run.responses[slot.id]!==null&&!a.questionSnapshot.choices.some(c=>c.id===run.responses[slot.id]))fail();
 }
 if(Object.keys(run.responses).some(id=>!ids.has(id)))fail();
 if(run.currentChoiceId!==null&&!run.slots[run.currentIndex].attempt.questionSnapshot.choices.some(c=>c.id===run.currentChoiceId))fail();
 for(let i=0;i<run.currentIndex;i++)if(!Object.hasOwn(run.responses,run.slots[i].id))fail();
 if(run.status==='in_progress'&&run.slots.slice(run.currentIndex).some(s=>Object.hasOwn(run.responses,s.id)))fail();
 if(run.status==='completed'&&Object.keys(run.responses).length!==30)fail();
 return structuredClone(run);
}
