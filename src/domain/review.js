import {complete} from './study.js';
import {day,now} from '../utils.js';
export function createProgress(attempts) {
 const latestIndex=new Map(),successIndex=new Map(),prior=new Map(),previous=new Map();
 for(const a of attempts.filter(complete).slice().sort((a,b)=>new Date(a.completedAt)-new Date(b.completedAt))) {
  prior.set(a.id,previous.get(a.questionId));previous.set(a.questionId,a);latestIndex.set(a.questionId,a);
  if(a.status==='correct'&&!a.confidence){if(!successIndex.has(a.questionId))successIndex.set(a.questionId,new Set());successIndex.get(a.questionId).add(day(a.completedAt));}
 }
 const latest=id=>latestIndex.get(id)||null;
 const previousAttempt=a=>prior.get(a.id);
 function reviewInfo(q, today=now()) {
  const a=latest(q.id);if(!a)return null;
  const successes=successIndex.get(q.id)?.size||0, needs=a.status!=='correct'||a.confidence;
  const days=needs?1:[3,7,14][Math.min(Math.max(successes-1,0),2)];
  const due=new Date(a.completedAt);due.setHours(0,0,0,0);due.setDate(due.getDate()+days);
  return {a,successes,needs,due,isDue:day(today)>=day(due)};
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
