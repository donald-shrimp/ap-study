import {complete} from './study.js';
import {dateInZone,daysBetween,examPartsFor,partOfAttempt} from './planning.js';

export function activePhase(plan,at=new Date()){
 if(!plan)return null;const today=dateInZone(at,plan.timeZone);
 return plan.phases.find(p=>p.start<=today&&today<=p.end)||null;
}
export function learningFields({qualification,attempts,questions=[],plan=null,at=new Date(),days=28,examPartId=null}){
 const zone=plan?.timeZone||'Asia/Tokyo',today=dateInZone(at,zone),latest=new Map(),byQuestion=new Map(questions.map(q=>[q.id,q]));
 for(const a of attempts){
  if(!complete(a)||a.diagnosticRunId||a.questionSnapshot?.diagnosticOnly||a.qualificationId&&a.qualificationId!==qualification.id||!a.completedAt)continue;
  if(examPartId&&partOfAttempt(a.questionSnapshot?a:{...a,questionSnapshot:byQuestion.get(a.questionId)},qualification)!==examPartId)continue;
  const distance=daysBetween(dateInZone(a.completedAt,zone),today);
  if(distance<0||distance>=days||new Date(a.completedAt)>new Date(at))continue;
  const old=latest.get(a.questionId);
  if(!old||a.completedAt>old.completedAt||a.completedAt===old.completedAt&&a.id>old.id)latest.set(a.questionId,a);
 }
 const focus=new Set(activePhase(plan,at)?.focusTopicIds||[]);
 const rows=qualification.topics.map(t=>({topicId:t.id,label:t.name,total:0,correct:0,assisted:0,incorrect:0,revealed:0,focus:focus.has(t.id)})),byTopic=new Map(rows.map(r=>[r.topicId,r]));
 for(const a of latest.values()){
  const q=a.questionSnapshot||byQuestion.get(a.questionId),topicId=q?.topicId||qualification.topics.find(t=>t.name===q?.topic)?.id,row=byTopic.get(topicId);
  if(row){row.total++;row[a.status]++;}
 }
 for(const row of rows){row.rate=row.total?row.correct/row.total:null;row.smallSample=row.total>0&&row.total<10;}
 rows.sort((a,b)=>Number(b.focus)-Number(a.focus)||category(a)-category(b)||(category(a)===0&&a.rate!==b.rate?a.rate-b.rate:0));
 return {mode:'learning',days,timeZone:zone,asOf:today,examPartId,definition:'latestCompletedPerQuestion',rows};
}
const category=r=>!r.total?2:r.smallSample?1:0;
export function summarizeFields(data){
 const counts=data.rows.reduce((sum,row)=>({total:sum.total+row.total,correct:sum.correct+row.correct}),{total:0,correct:0});
 return {...counts,rate:counts.total?counts.correct/counts.total:null};
}
export function diagnosticFields(result,qualification){
 return {mode:'diagnostic',result,rows:qualification.topics.map(t=>{
  const r=result?.topics.find(r=>r.topicId===t.id),total=r?.answered||0,correct=r?.correct||0;
  return {topicId:t.id,label:t.name,total,correct,assisted:0,incorrect:total-correct,revealed:0,rate:total?correct/total:null,smallSample:total>0&&total<10,focus:false};
 })};
}
export function upcomingExam(plan,qualification,at=new Date(),preferredPartId=null){
 if(!plan?.examDates.length)return null;
 const today=dateInZone(at,plan.timeZone),dates=[...plan.examDates].sort((a,b)=>a.date.localeCompare(b.date));
 const chosen=dates.find(d=>d.examPartId===preferredPartId&&d.date>=today)||dates.find(d=>d.date>=today)||dates.at(-1);
 return {...chosen,label:examPartsFor(qualification).find(p=>p.id===chosen.examPartId)?.label||chosen.examPartId,days:daysBetween(today,chosen.date)};
}
