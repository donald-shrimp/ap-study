import {complete} from './study.js';
import {canUseQuestion} from './content-policy.js';
import {now} from '../utils.js';
import {dateInZone,addDays} from './planning.js';
const intervals=[3,7,21,45,90,180],spread=[1,2,4,9,18,30];
export function createProgress(attempts,{timeZone='Asia/Tokyo'}={}) {
 const latestIndex=new Map(),successIndex=new Map(),streakIndex=new Map(),prior=new Map(),previous=new Map();
 for(const a of attempts.filter(a=>complete(a)&&!a.diagnosticRunId&&canUseQuestion(a.questionSnapshot,'practice')).slice().sort((a,b)=>new Date(a.completedAt)-new Date(b.completedAt)||a.id.localeCompare(b.id))) {
  prior.set(a.id,previous.get(a.questionId));previous.set(a.questionId,a);latestIndex.set(a.questionId,a);
  const day=dateInZone(a.completedAt,timeZone),stable=a.status==='correct'&&!a.confidence;
  const streak=streakIndex.get(a.questionId)||{days:0,lastDay:null,blockedDay:null};
  if(!stable){streak.days=0;streak.blockedDay=day;}
  else if(streak.lastDay!==day&&streak.blockedDay!==day)streak.days++;
  streak.lastDay=day;streakIndex.set(a.questionId,streak);
  if(a.status==='correct'&&!a.confidence){if(!successIndex.has(a.questionId))successIndex.set(a.questionId,new Set());successIndex.get(a.questionId).add(day);}
 }
 const latest=id=>latestIndex.get(id)||null;
 const previousAttempt=a=>prior.get(a.id);
 function reviewInfo(q, today=now()) {
  const a=latest(q.id);if(!a)return null;
  const successes=successIndex.get(q.id)?.size||0, needs=a.status!=='correct'||a.confidence;
  const {days:streak,lastDay:completedDay}=streakIndex.get(q.id);
  // Distinct successful days since the last lapse. Same-day retries cannot
  // advance spacing; the hash spreads cohorts without changing on reload/sync.
  const stage=Math.min(Math.max(streak-1,0),intervals.length-1);
  let hash=2166136261;for(const c of `${q.id}:${completedDay}:${stage}`)hash=Math.imul(hash^c.charCodeAt(0),16777619);
  const days=needs||!streak?1:intervals[stage]+(hash>>>0)%(2*spread[stage]+1)-spread[stage];
  const dueDate=addDays(completedDay,days),due=new Date(dueDate+'T00:00:00Z');
  return {a,successes,streak,intervalDays:days,needs,due,dueDate,timeZone,isDue:dateInZone(today,timeZone)>=dueDate};
 }
 function improvement(a) {
  const previous=previousAttempt(a);if(!previous)return null;
  if(a.status==='correct'&&!a.confidence&&previous.status!=='correct') {
    return previous.status==='incorrect'?'不正解 → 自力で正解':previous.status==='revealed'?'解答確認 → 自力で正解':`ヒント${previous.hintsBeforeAnswer}つ → ヒントなしで正解`;
  }
  if(['correct','assisted'].includes(a.status)&&['correct','assisted'].includes(previous.status)&&a.hintsBeforeAnswer<previous.hintsBeforeAnswer) return `ヒント${previous.hintsBeforeAnswer}つ → ${a.hintsBeforeAnswer}つで正解`;
  return null;
}
 return {latest,previousAttempt,reviewInfo,improvement};
}
