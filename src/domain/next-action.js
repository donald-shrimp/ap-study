import {complete} from './study.js';
import {practicePool,selectPractice} from './practice.js';
export function chooseNextAction({qualification,questions,attempts,reviewInfo,available=()=>true,practiceAllowed=()=>true,paperless=false,ignorePaused=false,online=true,resumeAllowed=()=>true,scope={},intent='normal',excludedQuestionIds=[]}){
 const pool=practicePool({qualification,questions,scope,available,practiceAllowed}),byId=new Map(pool.map(q=>[q.id,q]));
 const continued=new Set(attempts.map(a=>a.continuationOf).filter(Boolean));
 const paused=attempts.filter(a=>!complete(a)&&!a.deferred&&a.practiceScope?.intent!=='direct'&&!a.diagnosticRunId&&!a.questionSnapshot?.diagnosticOnly&&!continued.has(a.id)&&(!a.qualificationId||a.qualificationId===qualification.id)&&byId.has(a.questionId)&&resumeAllowed(a)).sort((a,b)=>(a.updatedAt||a.startedAt).localeCompare(b.updatedAt||b.startedAt)||a.id.localeCompare(b.id)).at(-1);
 if(!ignorePaused&&paused)return {kind:'resume',attemptId:paused.id,questionId:paused.questionId,topicId:byId.get(paused.questionId).topicId,reasonCode:'paused',reason:`ヒント ${paused.hintCount}まで · ${paused.selected===null?'回答未確定':'回答候補を保存済み'}`,scope:paused.practiceScope||{topicId:paused.topicId||null,examPartId:byId.get(paused.questionId).examPartId||qualification.defaultExamPartId}};
 const result=selectPractice({qualification,questions,attempts,reviewInfo,scope,available,practiceAllowed,intent,excludedQuestionIds});
 if(!pool.length)return {...result,reasonCode:'no_content',reason:paperless?(online?'紙・ペンなしで選べる問題がありません。すべてに切り替えるか、単語帳を使えます。':'紙・ペンなしで選べる保存済みの問題がありません。すべてに切り替えるか、保存済みの単語帳を使えます。'):online?'この資格には利用できる問題がありません。':'保存済みの問題がありません。'};
 return result;
}
