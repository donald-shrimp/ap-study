import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createAttempt,toggleChoice,selectAnswer,openHint,gradeAttempt,finalizeAttempt,makeState} from '../src/domain/study.js';
import {createStateValidator} from '../src/storage/validate.js';
import {canSubmit,validChoiceFormat} from '../src/domain/question-format.js';
import {createAssessment,chooseAssessment,submitAssessment,finishAssessment,assessmentAttempts,assessmentResult,validateAssessment} from '../src/domain/assessment.js';
import {buildAIPrompt} from '../src/features/ai-handoff.js';
const manifest=JSON.parse(readFileSync(new URL('../data/qualifications/ap/manifest.json',import.meta.url)));
const original=JSON.parse(readFileSync(new URL('../data/qualifications/ap/'+manifest.packs[0].url,import.meta.url)))[0];
const qualification={id:'fixture',topics:[{id:'a',name:'非公開テスト'}]};
function question(extra={}){const q={...structuredClone(original),id:'multi',qualificationId:'fixture',topicId:'a',topic:'非公開テスト',type:'multipleChoice',sourceKind:'authored',uses:['practice','diagnostic','mock'],answer:null,correctChoiceIds:['choice-0','choice-2'],selection:{mode:'exact',count:2},grading:{method:'exactChoiceSet'},...extra};delete q.correctChoiceId;return q;}
const validate=(q,a)=>createStateValidator({getQuestions:()=>[q],getTopics:()=>[q.topic],getQualification:()=>qualification})({...makeState(),attempts:[a],currentId:a.id});
test('複数選択は順不同の集合一致で採点し、未選択・選び過ぎ・選び忘れを判別',()=>{
 const q=question(),a=createAttempt(q);assert(!canSubmit(a));assert(!selectAnswer(a,0));toggleChoice(a,'choice-2',true);assert(!canSubmit(a));toggleChoice(a,'choice-0',true);assert.deepEqual(a.selectedChoiceIds,['choice-0','choice-2']);assert(canSubmit(a));assert.equal(gradeAttempt(a),'correct');validate(q,a);
 toggleChoice(a,'choice-1',true);assert(!canSubmit(a));assert.equal(gradeAttempt(a),'incorrect');toggleChoice(a,'choice-0',false);assert(canSubmit(a));finalizeAttempt(a,gradeAttempt(a));validate(q,a);assert.equal(a.status,'incorrect');assert(!toggleChoice(a,'choice-0',true));
 const all=createAttempt(question({selection:{mode:'all'}}));toggleChoice(all,'choice-0',true);assert(canSubmit(all));assert.equal(gradeAttempt(all),'incorrect');
});
test('複数のヒント付き正解・解答閲覧・確定回答・バックアップの型を維持',()=>{
 const q=question(),a=createAttempt(q);openHint(a);toggleChoice(a,'choice-2',true);toggleChoice(a,'choice-0',true);assert.equal(gradeAttempt(a),'assisted');finalizeAttempt(a,'assisted');validate(q,JSON.parse(JSON.stringify(a)));
 const reveal=createAttempt(q);reveal.answerViewedBefore=true;finalizeAttempt(reveal,'revealed');validate(q,reveal);
 for(const patch of [{selectedChoiceIds:['choice-0','unknown']},{selectedChoiceIds:['choice-0','choice-0']},{selectedChoiceIds:['choice-2','choice-0']},{selected:0},{selectedChoiceIds:'choice-0'},{status:'incorrect',selectedChoiceIds:['choice-0','choice-1'],answerViewedBefore:true}])assert.throws(()=>validate(q,{...structuredClone(a),...patch}));
 for(const patch of [{grading:{method:'deferred'}},{correctChoiceId:'choice-0'},{selection:{mode:'exact',count:3}},{correctChoiceIds:[]},{type:'freeText'}])assert(!validChoiceFormat({...q,...patch}));
 assert.throws(()=>createAttempt({...q,type:'freeText'}));
 const prompt=buildAIPrompt({question:q,attempt:a,qualification,baseURL:'https://example.com/'});assert(prompt.includes('答えを2つ選'));assert(prompt.includes(q.choices[0].text)&&prompt.includes(q.choices[2].text));
});
test('診断・模試は部分選択を保存し、終了後だけ集合で採点・結果とExportに反映',()=>{
 const questions=Array.from({length:30},(_,i)=>question({id:'multi-'+i}));const run=createAssessment(questions,qualification),q=run.slots[0].attempt.questionSnapshot;
 chooseAssessment(run,'choice-2');assert.deepEqual(run.currentChoiceId,['choice-2']);assert.throws(()=>submitAssessment(run,run.currentChoiceId));assert.deepEqual(assessmentAttempts(run),[]);
 const check=a=>validate(questions.find(q=>q.id===a.questionId),a);validateAssessment(run,qualification,check,{size:30,diagnostic:true});chooseAssessment(run,'choice-0');const external=run.currentChoiceId;submitAssessment(run,external);external.push('choice-3');assert.deepEqual(run.responses[run.slots[0].id],['choice-0','choice-2']);chooseAssessment(run,'choice-1');chooseAssessment(run,'choice-2');submitAssessment(run,run.currentChoiceId);finishAssessment(run);
 const saved=validateAssessment(JSON.parse(JSON.stringify(run)),qualification,check,{size:30,diagnostic:true}),result=assessmentResult(saved,qualification);assert.equal(result.answered,2);assert.equal(result.correct,1);assert.equal(result.incorrect,1);assert.deepEqual(result.items[0].selectedChoiceIds,q.correctChoiceIds);assert.equal(result.items[0].type,'multipleChoice');assert(assessmentAttempts(saved).every(a=>a.hintCount===0&&!a.answerViewedBefore));
 const bad=structuredClone(run);bad.responses[run.slots[0].id]=['choice-0'];assert.throws(()=>validateAssessment(bad,qualification,check,{size:30,diagnostic:true}));
});
