// Scope and ordering are shared; answering and grading stay format-specific.
export function studyQueue(items,{scope={},visited=[],available=()=>true,allowed=()=>true,compareRecommended=()=>0}={}){
 const topics=scope.topicIds?.length?scope.topicIds:scope.topicId?[scope.topicId]:[],seen=new Set(visited);
 const pool=items.filter(c=>(!scope.examPartId||c.examPartId===scope.examPartId)&&(!topics.length||topics.includes(c.topicId))&&(!scope.packId||c.packId===scope.packId)&&!seen.has(c.id)&&allowed(c)&&available(c));
 return pool.sort(scope.order==='number'?(a,b)=>(a.number??Infinity)-(b.number??Infinity)||a.id.localeCompare(b.id):compareRecommended);
}
export function caseRecommendation(runs,{seed='cases'}={}){
 const latest=new Map();for(const r of runs)if(!latest.has(r.caseId)||latest.get(r.caseId).updatedAt<r.updatedAt)latest.set(r.caseId,r);
 const rank=c=>{const r=latest.get(c.id);if(!r)return 0;const es=Object.values(r.evaluations);return es.some(e=>e.outcome==='incorrect'||['partial','notYet','unsure'].includes(e.outcome))?1:2;};
 const hash=s=>{let h=2166136261;for(const c of s)h=Math.imul(h^c.charCodeAt(0),16777619);return h>>>0;};
 return (a,b)=>rank(a)-rank(b)||String(latest.get(a.id)?.updatedAt||'').localeCompare(String(latest.get(b.id)?.updatedAt||''))||hash(seed+':'+a.id)-hash(seed+':'+b.id)||a.id.localeCompare(b.id);
}
export function validCaseScope(s,qualification,index=[]){
 return !!s&&typeof s==='object'&&!Array.isArray(s)&&Object.keys(s).every(k=>['examPartId','topicId','topicIds','packId','order','sessionId'].includes(k))&&qualification.examParts.some(p=>p.id===s.examPartId&&p.unit==='cases')&&['recommended','number'].includes(s.order)&&typeof s.sessionId==='string'&&/^[\w-]{1,100}$/.test(s.sessionId)&&(s.topicId===null||qualification.topics.some(t=>t.id===s.topicId))&&Array.isArray(s.topicIds)&&s.topicIds.length<=100&&new Set(s.topicIds).size===s.topicIds.length&&s.topicIds.every(id=>qualification.topics.some(t=>t.id===id))&&(s.packId===null||index.some(e=>e.packId===s.packId))&&(s.order!=='number'||!!s.packId);
}
