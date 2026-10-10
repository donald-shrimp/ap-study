// Mutable preferences and resumption metadata stay outside immutable answers.
const identifier=v=>typeof v==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(v);
const only=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).every(k=>keys.includes(k));
export const learningModes=['all','paperless','desk'];
export function validateLearning(kind,p){
 const fail=()=>{throw new Error('学習設定の同期データを確認できません。');};
 if(['desk','deferred'].includes(kind)){
  if(!only(p,['questionId','value'])||!identifier(p.questionId)||typeof p.value!=='boolean')fail();
 }else if(kind==='context'){
  if(!only(p,['attemptId','questionId','entryMode','scope'])||!identifier(p.attemptId)||!identifier(p.questionId)||!learningModes.includes(p.entryMode))fail();
  const s=p.scope;
  if(!only(s,['intent','topicId','topicIds','examPartId','examPartIds','paperMode','returnView','returnRunId'])||!['normal','topic','review','direct'].includes(s.intent)||s.paperMode!==p.entryMode)fail();
  for(const k of ['topicId','examPartId','returnRunId'])if(s[k]!==null&&!identifier(s[k]))fail();
  for(const k of ['topicIds','examPartIds'])if(!Array.isArray(s[k])||s[k].length>100||new Set(s[k]).size!==s[k].length||!s[k].every(identifier))fail();
  if(!['home','topics','review','history','materials','flashcards','study','diagnostic','diagnostics','planning'].includes(s.returnView))fail();
 }else fail();
 return structuredClone(p);
}
export function learningId(kind,p){validateLearning(kind,p);return `${kind}--${kind==='context'?p.attemptId:p.questionId}`;}
export function contextPayload(a){
 const s=a.practiceScope;if(!s||a.diagnosticRunId||a.questionSnapshot?.diagnosticOnly)return null;
 const entryMode=a.entryMode||s.paperMode||'all';
 return validateLearning('context',{attemptId:a.id,questionId:a.questionId,entryMode,scope:{intent:s.intent||'normal',topicId:s.topicId||null,topicIds:s.topicIds||[],examPartId:s.examPartId||null,examPartIds:s.examPartIds||[],paperMode:entryMode,returnView:s.returnView||'home',returnRunId:s.returnRunId||null}});
}
export function scopeBelongsToQualification(p,qualification){
 if(!qualification)return true;
 const topics=new Set(qualification.topics.map(t=>t.id)),parts=new Set((qualification.examParts||[{id:qualification.defaultExamPartId||'objective'}]).map(p=>p.id)),s=p.scope;
 return (!s.topicId||topics.has(s.topicId))&&s.topicIds.every(id=>topics.has(id))&&(!s.examPartId||parts.has(s.examPartId))&&s.examPartIds.every(id=>parts.has(id));
}
export function contextMatchesQuestion(p,q,qualification){
 if(!q)return !qualification;
 const s=p.scope,part=q.examPartId||qualification?.defaultExamPartId||'objective';
 return (!s.topicId||s.topicId===q.topicId)&&(!s.topicIds.length||s.topicIds.includes(q.topicId))&&(!s.examPartId||s.examPartId===part)&&(!s.examPartIds.length||s.examPartIds.includes(part));
}
export function applyLearning(state,documents,qualification=null){
 let changed=false;const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 for(const doc of documents){
  const p=doc.payload;try{validateLearning(doc.kind,p);}catch{continue;}if(doc.kind==='context'&&!scopeBelongsToQualification(p,qualification))continue;
  if(doc.kind==='desk'){
   const before=state.settings.deskQuestionIds,after=p.value?[...new Set([...before,p.questionId])]:before.filter(id=>id!==p.questionId);
   if(!same(before,after)){state.settings.deskQuestionIds=after;changed=true;}
  }else if(doc.kind==='deferred'){
   for(const a of state.attempts)if(a.questionId===p.questionId&&a.deferred!==p.value){a.deferred=p.value;changed=true;}
   const before=state.session.excludedQuestionIds||[],after=p.value?[...new Set([...before,p.questionId])]:before.filter(id=>id!==p.questionId);
   if(!same(before,after)){state.session.excludedQuestionIds=after;changed=true;}
  }else if(doc.kind==='context'){
   const a=state.attempts.find(a=>a.id===p.attemptId&&a.questionId===p.questionId);
   if(a&&contextMatchesQuestion(p,a.questionSnapshot,qualification)&&!(state.view==='study'&&state.currentId===a.id)){
    if(a.entryMode!==p.entryMode||!same(a.practiceScope,p.scope)){a.entryMode=p.entryMode;a.practiceScope=structuredClone(p.scope);changed=true;}
   }
  }
 }
 return changed;
}
