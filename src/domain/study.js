import {now} from '../utils.js';
export const makeState = () => ({version:1, attempts:[], currentId:null, currentRunId:null, view:'home', settings:{largeText:false,paperMode:'all',lastEntry:'all',deskQuestionIds:[]}, session:{attemptIds:[], topic:null}, readingNotes:{}, overrides:{}});
export const complete = a => ['correct','assisted','incorrect','revealed'].includes(a.status);
export const labels = {correct:'自力で正解',assisted:'ヒントで正解',incorrect:'不正解',revealed:'解答を確認',in_progress:'途中',postponed:'あとで解く'};
export function hintTotal(a) { return a.materialSnapshot.hints.length; }
export function enriched(q) { return ['reviewed','personal'].includes(q.enrichment); }
export function hintKind(q) { return q.hintStatus || (enriched(q)?'individual':'topic-guide'); }
export function createAttempt(q, {topic=null, readingNote='', contentRevision='original', at=now(), id=crypto.randomUUID(),diagnostic=false}={}) {
 if(q.diagnosticOnly&&!diagnostic)throw new Error('この問題は診断専用です。通常学習には追加できません。');
 const {hints,summary,explanation,takeaway,choiceReasons,searchText,hintSource,lessonSource,revision,...questionSnapshot}=q;
 return {id,qualificationId:q.qualificationId,questionId:q.id,questionVersion:q.version,contentRevision,topic,topicId:topic?q.topicId:null,readingNote,status:'in_progress',startedAt:at,updatedAt:at,completedAt:null,selected:null,selectedChoiceId:null,hintCount:0,hintsBeforeAnswer:null,hintEvents:[],answerViewedBefore:false,confidence:false,scrollY:0,questionSnapshot:structuredClone(questionSnapshot),materialSnapshot:structuredClone({enrichment:q.enrichment,hintStatus:hintKind(q),hints,summary,explanation,takeaway,choiceReasons})};
}
export function selectAnswer(a, index, question) {
 const choices=a.questionSnapshot?.choices||question?.choices;
 if(complete(a) || !Number.isInteger(index) || !choices?.[index])return false;
 a.selected=index;a.selectedChoiceId=choices[index].id;return true;
}
export function openHint(a, at=now()) {
 if(a.hintCount>=a.materialSnapshot.hints.length)return false;
 const phase=complete(a)?'after':'before';a.hintCount++;a.hintEvents.push({step:a.hintCount,at,phase});a.updatedAt=at;
 if(phase==='before'&&a.materialSnapshot.hints[a.hintCount-1].revealsAnswer)a.answerViewedBefore=true;
 return true;
}
export function gradeAttempt(a, answer) {
 if(complete(a))return a.status;
 const correctAnswer=a.questionSnapshot?.answer??answer;
 return a.answerViewedBefore?'revealed':a.selected===correctAnswer?(a.hintCount?'assisted':'correct'):'incorrect';
}
export function finalizeAttempt(a,status,at=now()) {
 if(complete(a))return false;
 a.status=status;a.completedAt=at;a.updatedAt=at;a.hintsBeforeAnswer=a.hintCount;return true;
}
