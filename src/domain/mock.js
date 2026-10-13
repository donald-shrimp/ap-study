import {createAssessment,validateAssessment,assessmentResult} from './assessment.js';
import {validAssessmentSize} from './assessment-policy.js';
import {canUseQuestion,questionFamily} from './content-policy.js';
const id=v=>typeof v==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(v);
export const mockLabel=label=>label.replace(/^派生模試\s*/, '模試 ');
export function mockQuestions(set,questions){
 const byId=new Map(questions.map(q=>[q.id,q]));
 if(!set||set.status!=='ready'||!validAssessmentSize(set.size)||!Array.isArray(set.slots)||set.slots.length!==set.size||new Set(set.slots.map(s=>s.questionId)).size!==set.size)throw new Error('この模試の問題数を確認できません。');
 const ordered=set.slots.map((slot,i)=>{
  const q=byId.get(slot.questionId);
  if(slot.number!==i+1||!q||!canUseQuestion(q,'mock')||q.enrichment!=='reviewed'||(slot.parentQuestionId!==undefined&&q.parentQuestionId!==slot.parentQuestionId)||q.topicId!==slot.topicId)throw new Error('模試の固定問題と教材が一致しません。');
  return q;
 });
 if(new Set(ordered.map(questionFamily)).size!==ordered.length)throw new Error('模試で同じ内容の問題が重複しています。');
 return ordered;
}
export function createMock(set,questions,qualification,attempts=[],catalogRevision=''){
 const ordered=mockQuestions(set,questions),run=createAssessment(ordered,qualification,attempts,catalogRevision,{mode:'mock'});
 return {...run,mode:'mock',blueprintVersion:1,selectionPolicy:null,mockSet:{id:set.id,label:mockLabel(set.label),version:set.version||1,questionIds:ordered.map(q=>q.id)}};
}
export function validateMock(run,qualification,validateAttempt){
 const fail=()=>{throw new Error('模試データの形式を確認できません。記録は変更していません。');};
 const set=run?.mockSet;
 if(run?.mode!=='mock'||run.selectionPolicy!==null||!set||Object.keys(set).some(k=>!['id','label','version','questionIds'].includes(k))||!id(set.id)||typeof set.label!=='string'||!set.label.length||set.label.length>200||!Number.isInteger(set.version)||set.version<1||!Array.isArray(set.questionIds)||set.questionIds.length!==run.size||new Set(set.questionIds).size!==run.size)fail();
 const value=validateAssessment(run,qualification,validateAttempt,{size:run.size});
 if(value.slots.some((s,i)=>!canUseQuestion(s.attempt.questionSnapshot,'mock')||s.attempt.questionId!==set.questionIds[i]))fail();
 return value;
}
export function mockResult(run,qualification){
 const result=assessmentResult(run,qualification);
 return {...result,mode:'mock',mockSet:structuredClone(run.mockSet),scoreRate:result.correct/run.size};
}
