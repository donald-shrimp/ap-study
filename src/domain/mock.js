import {createAssessment,validateAssessment,diagnosticResult} from './diagnostic.js';
const id=v=>typeof v==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(v);
export const mockLabel=label=>label.replace(/^派生模試\s*/, '模試 ');
export function mockQuestions(set,questions){
 const byId=new Map(questions.map(q=>[q.id,q]));
 if(!set||set.status!=='ready'||set.size!==80||!Array.isArray(set.slots)||set.slots.length!==80||new Set(set.slots.map(s=>s.questionId)).size!==80||new Set(set.slots.map(s=>s.parentQuestionId)).size!==80)throw new Error('この模試の80問を確認できません。');
 return set.slots.map((slot,i)=>{
  const q=byId.get(slot.questionId);
  if(slot.number!==i+1||!q?.diagnosticOnly||q.enrichment!=='reviewed'||q.parentQuestionId!==slot.parentQuestionId||q.topicId!==slot.topicId)throw new Error('模試の固定問題と教材が一致しません。');
  return q;
 });
}
export function createMock(set,questions,qualification,attempts=[],catalogRevision=''){
 const ordered=mockQuestions(set,questions),run=createAssessment(ordered,qualification,attempts,catalogRevision);
 return {...run,mode:'mock',blueprintVersion:1,selectionPolicy:null,mockSet:{id:set.id,label:mockLabel(set.label),version:set.version||1,questionIds:ordered.map(q=>q.id)}};
}
export function validateMock(run,qualification,validateAttempt){
 const fail=()=>{throw new Error('模試データの形式を確認できません。記録は変更していません。');};
 const set=run?.mockSet;
 if(run?.mode!=='mock'||run.selectionPolicy!==null||!set||Object.keys(set).some(k=>!['id','label','version','questionIds'].includes(k))||!id(set.id)||typeof set.label!=='string'||!set.label.length||set.label.length>200||!Number.isInteger(set.version)||set.version<1||!Array.isArray(set.questionIds)||set.questionIds.length!==80||new Set(set.questionIds).size!==80)fail();
 const value=validateAssessment(run,qualification,validateAttempt,{size:80});
 if(value.slots.some((s,i)=>!s.attempt.questionSnapshot.diagnosticOnly||s.attempt.questionId!==set.questionIds[i]))fail();
 return value;
}
export function mockResult(run,qualification){
 const result=diagnosticResult(run,qualification);
 return {...result,mode:'mock',mockSet:structuredClone(run.mockSet),scoreRate:result.correct/run.size};
}
