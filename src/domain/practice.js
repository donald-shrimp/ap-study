import {complete} from './study.js';
import {examPartsFor} from './planning.js';
export function practicePool({qualification,questions,scope={},available=()=>true,practiceAllowed=()=>true}){
 const parts=new Set(examPartsFor(qualification).filter(p=>p.practiceAvailable).map(p=>p.id));
 const topics=scope.topicIds?.length?scope.topicIds:scope.topicId?[scope.topicId]:[];
 const requestedParts=scope.examPartIds?.length?scope.examPartIds:scope.examPartId?[scope.examPartId]:[];
 return questions.filter(q=>!q.diagnosticOnly&&(!q.qualificationId||q.qualificationId===qualification.id)&&parts.has(q.examPartId||qualification.defaultExamPartId||'objective')&&(!topics.length||topics.includes(q.topicId))&&(!requestedParts.length||requestedParts.includes(q.examPartId||qualification.defaultExamPartId||'objective'))&&available(q)&&practiceAllowed(q));
}
const hash=text=>{let n=2166136261;for(const c of text)n=Math.imul(n^c.charCodeAt(0),16777619);return n>>>0;};
// Recommendations are separate from explicit restrictions. Identical inputs
// select the same candidate, both at entry and at the next question.
export function selectPractice({qualification,questions,attempts=[],reviewInfo,scope={},available=()=>true,practiceAllowed=()=>true,excludedQuestionIds=[],visitedQuestionIds=[],intent='normal'}){
 const pool=practicePool({qualification,questions,scope,available,practiceAllowed});
 const rows=attempts.filter(a=>(!a.qualificationId||a.qualificationId===qualification.id)&&!a.diagnosticRunId&&!a.questionSnapshot?.diagnosticOnly);
 const continued=new Set(rows.map(a=>a.continuationOf).filter(Boolean));
 const latestCompleted=new Map();for(const a of rows.filter(complete))if(!latestCompleted.has(a.questionId)||a.completedAt>latestCompleted.get(a.questionId))latestCompleted.set(a.questionId,a.completedAt);
 const deferred=new Set(rows.filter(a=>!complete(a)&&!continued.has(a.id)&&a.deferred&&(!latestCompleted.has(a.questionId)||latestCompleted.get(a.questionId)<a.updatedAt)).map(a=>a.questionId));
 const excluded=new Set([...excludedQuestionIds,...deferred]);
 const cached=new Map(pool.map(q=>[q.id,reviewInfo(q)])),info=q=>cached.get(q.id);
 let candidates=pool.filter(q=>!excluded.has(q.id)&&!visitedQuestionIds.includes(q.id)&&(intent!=='review'||info(q)?.needs||info(q)?.isDue));
 const pending=new Set(rows.filter(a=>!complete(a)&&!continued.has(a.id)).map(a=>a.questionId));
 const free=candidates.filter(q=>!pending.has(q.id));if(free.length)candidates=free;
 if(!candidates.length)return {kind:'unavailable',reasonCode:'no_candidates',reason:intent==='review'?'この範囲の復習はここまでです。':'この範囲には次に解ける問題がありません。先送りした問題は「解き直し」から再開できます。',pool};
 const byId=new Map(questions.map(q=>[q.id,q]));
 const recent=rows.slice().sort((a,b)=>String(b.startedAt).localeCompare(String(a.startedAt))||b.id.localeCompare(a.id)).slice(0,20);
 const topicCount=new Map(),packCount=new Map(),lastSeen=new Map();
 for(const a of recent){const q=byId.get(a.questionId)||a.questionSnapshot;if(!q)continue;topicCount.set(q.topicId,(topicCount.get(q.topicId)||0)+1);packCount.set(q.packId,(packCount.get(q.packId)||0)+1);if(!lastSeen.has(q.id))lastSeen.set(q.id,a.startedAt);}
 const rank=q=>{const i=info(q);return i?.isDue?0:!i?1:i.needs?2:3;};
 const seed=recent[0]?.id||qualification.id;
 candidates.sort((a,b)=>{
  const ra=rank(a),rb=rank(b),ia=info(a),ib=info(b);
  return ra-rb||(ra===0?ia.due-ib.due:ra===3?Date.parse(ia.a.completedAt)-Date.parse(ib.a.completedAt):0)||(topicCount.get(a.topicId)||0)-(topicCount.get(b.topicId)||0)||(packCount.get(a.packId)||0)-(packCount.get(b.packId)||0)||String(lastSeen.get(a.id)||'').localeCompare(String(lastSeen.get(b.id)||''))||hash(seed+':'+a.id)-hash(seed+':'+b.id)||a.id.localeCompare(b.id);
 });
 const q=candidates[0],reasonCode=['due','new','needs','recheck'][rank(q)];
 const reasons={due:'復習日が来た問題です。',new:'まだ回答していない問題です。',needs:'前に解いた問題をもう一度確認します。',recheck:'前に解いた問題を再確認します。'};
 return {kind:'question',questionId:q.id,topicId:q.topicId,scope:{topicId:scope.topicId||null,topicIds:scope.topicIds||[],examPartId:scope.examPartId||null,examPartIds:scope.examPartIds||[]},reasonCode,reason:reasons[reasonCode],pool};
}
