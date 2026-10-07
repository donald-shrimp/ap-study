import {complete} from './study.js';
import {examPartsFor,partOfAttempt,dateInZone,daysBetween} from './planning.js';
import {activePhase} from './analytics.js';

// The returned question ID and scope are used by both the card and its button.
export function chooseNextAction({qualification,questions,attempts,plan=null,reviewInfo,available=()=>true,at=new Date(),ignorePaused=false,online=true}){
 const ordinary=questions.filter(q=>!q.diagnosticOnly&&(!q.qualificationId||q.qualificationId===qualification.id)),byId=new Map(ordinary.map(q=>[q.id,q]));
 const continued=new Set(attempts.map(a=>a.continuationOf).filter(Boolean));
 const paused=attempts.filter(a=>!complete(a)&&!a.diagnosticRunId&&!a.questionSnapshot?.diagnosticOnly&&!continued.has(a.id)&&(!a.qualificationId||a.qualificationId===qualification.id)&&byId.has(a.questionId)).sort((a,b)=>(a.updatedAt||a.startedAt).localeCompare(b.updatedAt||b.startedAt)||a.id.localeCompare(b.id)).at(-1);
 if(!ignorePaused&&paused&&available(byId.get(paused.questionId)))return {kind:'resume',attemptId:paused.id,questionId:paused.questionId,topicId:byId.get(paused.questionId).topicId,reasonCode:'paused',reason:`ヒント ${paused.hintCount}まで · ${paused.selected===null?'回答未確定':'回答候補を保存済み'}`,scope:{topicId:paused.topicId||null,examPartId:partOfAttempt(paused,qualification)}};
 const allowedParts=new Set(examPartsFor(qualification).filter(p=>p.practiceAvailable).map(p=>p.id));
 const pool=ordinary.filter(q=>allowedParts.has(q.examPartId||qualification.defaultExamPartId)&&available(q));
 if(!pool.length)return {kind:'unavailable',reasonCode:'no_content',reason:online?'この資格には利用できる問題がありません。':'保存済みの問題がありません。オンラインで問題を開いてください。'};
 const phase=activePhase(plan,at),phasePool=phase?pool.filter(q=>phase.examPartIds.includes(q.examPartId||qualification.defaultExamPartId)&&(!phase.focusTopicIds.length||phase.focusTopicIds.includes(q.topicId))):[];
 const info=q=>reviewInfo(q),byDue=(a,b)=>info(a).due-info(b).due||a.id.localeCompare(b.id);
 let q,reasonCode,scope={topicId:null,examPartId:null};
 if(phasePool.length){
  q=phasePool.filter(q=>info(q)?.isDue).sort(byDue)[0];reasonCode='phase_due';
  if(!q){
   const seen=new Map(qualification.topics.map(t=>[t.id,new Set()]));
   for(const a of attempts){if(!complete(a)||a.diagnosticRunId||a.questionSnapshot?.diagnosticOnly||a.qualificationId&&a.qualificationId!==qualification.id||!a.completedAt)continue;const date=new Date(a.completedAt);if(date>new Date(at)||daysBetween(dateInZone(date,plan.timeZone),dateInZone(at,plan.timeZone))>=28)continue;seen.get(a.questionSnapshot?.topicId||byId.get(a.questionId)?.topicId)?.add(a.questionId);}
   const focusOrder=qualification.topics.map(t=>t.id);
   const ordered=[...phasePool].sort((a,b)=>(seen.get(a.topicId)?.size||0)-(seen.get(b.topicId)?.size||0)||focusOrder.indexOf(a.topicId)-focusOrder.indexOf(b.topicId));
   q=ordered.find(q=>!info(q));reasonCode='phase_new';
   if(!q){q=[...ordered].sort((a,b)=>new Date(info(a)?.a.completedAt||0)-new Date(info(b)?.a.completedAt||0))[0];reasonCode='phase_recheck';}
  }
  scope={topicId:phase.focusTopicIds.length?q.topicId:null,examPartId:q.examPartId||qualification.defaultExamPartId};
  if(!phase.focusTopicIds.length)reasonCode=reasonCode.replace('phase_','part_');
 }else{
  q=pool.filter(q=>info(q)?.isDue).sort(byDue)[0];reasonCode='due';
  if(!q){q=pool.find(q=>!info(q));reasonCode='new';}
  if(!q){q=pool.filter(q=>info(q)?.needs)[0]||[...pool].sort((a,b)=>new Date(info(a)?.a.completedAt||0)-new Date(info(b)?.a.completedAt||0))[0];reasonCode='recheck';}
  if(phase?.focusTopicIds.length&&!online)reasonCode='offline_fallback';
  else if(phase&&!phasePool.length)reasonCode='phase_unavailable';
 }
 const reasons={part_due:'計画の対象パート。復習日が来た問題です。',part_new:'計画の対象パート。まだ取り組んでいない問題です。',part_recheck:'計画の対象パート。前に解いた問題を再確認します。',phase_due:'計画の重点分野。復習日が来た問題です。',phase_new:'計画の重点分野。まだ取り組んでいない問題です。',phase_recheck:'計画の重点分野。前に解いた問題を再確認します。',due:'復習日が来た問題を、もう一度確認します。',new:'まだ取り組んでいない問題です。',recheck:'前に解いた問題を、もう一度確認します。',offline_fallback:'重点分野は未保存。いま開ける問題を選びました。',phase_unavailable:'重点分野に利用できる教材がないため、通常の問題を選びました。'};
 return {kind:'question',questionId:q.id,topicId:q.topicId,scope,reasonCode,reason:reasons[reasonCode],phaseId:phase?.id||null};
}
