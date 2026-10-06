import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createAttempt,finalizeAttempt,selectAnswer,openHint} from '../src/domain/study.js';
import {createStateValidator} from '../src/storage/validate.js';
import {makeState} from '../src/domain/study.js';
import {blankPlan,validatePlan,parsePlan,validDate,dateInZone,daysBetween,summarize,phaseProgress,studySummary} from '../src/domain/planning.js';
import {selectDiagnostic,createDiagnostic,submitDiagnostic,finishDiagnostic,diagnosticAttempts,diagnosticResult,validateDiagnostic} from '../src/domain/diagnostic.js';

const q={id:'sample',name:'検証資格',defaultExamPartId:'objective',examParts:[{id:'objective',label:'選択式',practiceAvailable:true},{id:'written',label:'記述式',practiceAvailable:false}],topics:[{id:'one',name:'分野1'},{id:'two',name:'分野2'},{id:'three',name:'分野3'}]};
const questions=Array.from({length:60},(_,i)=>({id:`q${i}`,qualificationId:q.id,examPartId:'objective',version:1,type:'singleChoice',packId:'first',packLabel:'検証',number:i+1,title:'足し算',topic:q.topics[i%3].name,topicId:q.topics[i%3].id,source:'検証用',stem:'1＋1は？',sourceImages:[],imageSizes:[],related:[],adaptation:'',choices:[{id:'a',label:'ア',text:'1'},{id:'b',label:'イ',text:'2'}],correctChoiceId:'b',answer:1,enrichment:'reviewed',hintStatus:'individual',hints:[{title:'考える',text:'1に1を足す。',revealsAnswer:false},{title:'答え',text:'2になる。',revealsAnswer:true}],summary:'2',explanation:'1＋1＝2',takeaway:'足す',choiceReasons:['1は加算前','1に1を加算した結果']}));
const validateState=createStateValidator({getQuestions:()=>questions,getTopics:()=>q.topics.map(t=>t.name),getQualification:()=>q});
const validateAttempt=a=>validateState({...makeState(),attempts:[a]});
const plan=()=>({...blankPlan(q),phases:[{id:'phase',name:'確認',start:'2026-10-07',end:'2026-10-18',examPartIds:['objective'],targets:{completedAttempts:10},focusTopicIds:['one']}]});

test('暦日・閏日・JSTの境界で、残日数と日付がずれない',()=>{
 assert.ok(validDate('2028-02-29'));assert.equal(validDate('2026-02-29'),false);assert.equal(validDate('2026-02-30'),false);assert.equal(validDate('2026-2-3'),false);
 assert.equal(dateInZone('2026-10-06T15:00:00Z','Asia/Tokyo'),'2026-10-07');assert.equal(daysBetween('2026-10-07','2026-11-04'),28);
});
test('資格・参照・版・未知項目・重複期間を、登録前に拒否する',()=>{
 validatePlan(plan(),q);
 for(const modify of [p=>p.version=2,p=>p.qualificationId='other',p=>p.extra=true,p=>p.phases[0].focusTopicIds=['unknown'],p=>p.phases[0].end='2026-10-06',p=>p.examDates=[{examPartId:'objective',date:'2026-02-30'}],p=>p.phases.push({...p.phases[0],id:'other'}),p=>p.phases[0].targets.completedAttempts=1.5,p=>p.phases[0].examPartIds=['written']]){const p=plan();modify(p);assert.throws(()=>validatePlan(p,q));}
 assert.deepEqual(parsePlan('```json\n'+JSON.stringify(plan())+'\n```',q),plan());assert.throws(()=>parsePlan('{bad}',q));
});
test('計画実績は完了回数で、解き直し・解答閲覧を含み、重点分野に限定しない',()=>{
 const attempts=['correct','assisted','incorrect','revealed'].map((status,i)=>{const a=createAttempt(questions[i<2?0:1],{at:'2026-10-07T00:00:00Z'});selectAnswer(a,status==='incorrect'?0:1);if(status==='assisted')openHint(a);if(status==='revealed')a.answerViewedBefore=true;finalizeAttempt(a,status,'2026-10-07T01:00:00Z');return a;});
 const out=summarize(attempts,q,'Asia/Tokyo','2026-10-07T03:00:00Z');assert.equal(out.all.completedAttempts,4);assert.equal(out.all.distinctQuestions,2);assert.equal(out.all.selfCorrectRate,.25);assert.equal(out.topics[0].completedAttempts,2);
 assert.equal(phaseProgress(plan(),attempts,q)[0].actual,4);assert.equal(phaseProgress({...plan(),phases:plan().phases.map(p=>({...p,examPartIds:['written']}))},attempts,q)[0].actual,0);
 const exportData=studySummary({qualification:q,plan:plan(),attempts,at:'2026-10-07T03:00:00Z'});assert.equal(exportData.learning.last7Days.completedAttempts,4);assert.equal(JSON.stringify(exportData).includes('questionSnapshot'),false);
});
test('診断は30問の重複なし・分野分散・各分野の初見優先',()=>{
 const seen=questions.slice(0,30).map(question=>({questionId:question.id}));const selected=selectDiagnostic(questions,q,seen,()=>.42);assert.equal(selected.length,30);assert.equal(new Set(selected.map(x=>x.id)).size,30);assert.equal(new Set(selected.map(x=>x.topicId)).size,3);assert.ok(selected.every(x=>Number(x.id.slice(1))>=30));assert.throws(()=>selectDiagnostic(questions.slice(0,29),q));
});
test('途中回答は採点せず、最後に一括で結果を作る。結果は支援なし',()=>{
 const run=createDiagnostic(questions.slice(0,30),q);run.currentChoiceId='b';validateDiagnostic(run,q,validateAttempt);assert.equal(diagnosticAttempts(run).length,0);
 for(let i=0;i<30;i++)submitDiagnostic(run,i<18?'b':'a');validateDiagnostic(run,q,validateAttempt);assert.equal(run.status,'completed');const result=diagnosticResult(run,q);assert.equal(result.answered,30);assert.equal(result.correct,18);assert.equal(result.incorrect,12);assert.equal(result.unanswered,0);
 assert.ok(diagnosticAttempts(run).every(a=>a.hintsBeforeAnswer===0&&!a.answerViewedBefore));assert.throws(()=>submitDiagnostic(run,'b'));
});
test('スキップ・途中終了・診断後の復習は、結果を混同しない',()=>{
 const run=createDiagnostic(questions.slice(0,30),q);submitDiagnostic(run,'b');submitDiagnostic(run,null);finishDiagnostic(run);const result=diagnosticResult(run,q);assert.equal(result.answered,1);assert.equal(result.unanswered,29);assert.equal(result.correctRate,1);assert.equal(run.status,'ended_early');
 const serialized=JSON.stringify(run);const retry=createAttempt(questions[0]);openHint(retry);selectAnswer(retry,0);finalizeAttempt(retry,'incorrect');assert.equal(JSON.stringify(run),serialized);
});
test('診断へ支援付き記録・重複問題・異なる資格を混入できない',()=>{
 for(const modify of [r=>openHint(r.slots[0].attempt),r=>r.slots[1].attempt=structuredClone(r.slots[0].attempt),r=>r.qualificationId='other',r=>r.slots[0].attempt.answerViewedBefore=true,r=>r.size=10]){const run=createDiagnostic(questions.slice(0,30),q);modify(run);assert.throws(()=>validateDiagnostic(run,q,validateAttempt));}
});
test('公開サンプルを現行資格定義で検証できる',()=>{
 const qualification=JSON.parse(readFileSync(new URL('../content/ap/qualification.json',import.meta.url))),example=JSON.parse(readFileSync(new URL('../schemas/study-plan.example.json',import.meta.url)));validatePlan(example,qualification);
});

const detailedPlan=()=>{const p=plan();p.phases[0].weeklyTargets=[{id:'first',start:'2026-10-07',end:'2026-10-13',completedAttempts:4},{id:'last',start:'2026-10-14',end:'2026-10-18',completedAttempts:6}];p.phases[0].milestones=[{id:'mock',name:'記述式の模試',date:'2026-10-18',examPartId:'written',completed:false}];return p;};
test('週別目標と予定は任意。未知項目・期間・件数・ID・合計の矛盾を拒否する',()=>{
 assert.deepEqual(validatePlan(plan(),q),plan());validatePlan(detailedPlan(),q);
 for(const modify of [p=>p.phases[0].weeklyTargets=null,p=>p.phases[0].weeklyTargets[0].end='2026-10-14',p=>p.phases[0].weeklyTargets[1].start='2026-10-13',p=>p.phases[0].weeklyTargets[0].completedAttempts=5,p=>p.phases[0].weeklyTargets[0].start='2026-10-06',p=>p.phases[0].weeklyTargets[0].id='last',p=>p.phases[0].weeklyTargets[0].completedAttempts=1.2,p=>p.phases[0].milestones=null,p=>p.phases[0].milestones[0].date='2026-10-19',p=>p.phases[0].milestones[0].examPartId='unknown',p=>p.phases[0].milestones[0].completed='true',p=>p.phases[0].milestones[0].extra='unknown',p=>p.phases[0].milestones.push({...p.phases[0].milestones[0]})]){const p=detailedPlan();modify(p);assert.throws(()=>validatePlan(p,q));}
});
test('週の両端とJST境界で実績を数え、休んだ週の未達を繰り越さない',()=>{
 const p=detailedPlan(),attempts=['2026-10-06T15:00:00Z','2026-10-13T14:59:59Z','2026-10-13T15:00:00Z','2026-10-18T14:59:59Z','2026-10-18T15:00:00Z'].map(at=>{const a=createAttempt(questions[0],{at});selectAnswer(a,1);finalizeAttempt(a,'correct',at);return a;});
 const before=JSON.stringify(attempts),first=phaseProgress(p,attempts,q,'2026-10-13T14:59:59Z')[0],second=phaseProgress(p,attempts,q,'2026-10-13T15:00:00Z')[0];
 assert.equal(first.actual,4);assert.deepEqual(first.weeklyProgress.map(w=>[w.actual,w.remaining,w.active]),[[2,2,true],[2,4,false]]);assert.deepEqual(second.weeklyProgress.map(w=>[w.actual,w.remaining,w.active]),[[2,2,false],[2,4,true]]);
 p.phases[0].milestones[0].completed=true;assert.equal(phaseProgress(p,attempts,q)[0].actual,4);assert.equal(JSON.stringify(attempts),before);
 const summary=studySummary({qualification:q,plan:p,attempts,at:'2026-10-14T00:00:00Z'});assert.equal(summary.phaseProgress[0].weeklyProgress[1].remaining,4);assert.equal(summary.currentPlan.phases[0].milestones[0].completed,true);
});
