import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createAttempt,finalizeAttempt,selectAnswer,openHint} from '../src/domain/study.js';
import {createStateValidator} from '../src/storage/validate.js';
import {makeState} from '../src/domain/study.js';
import {blankPlan,validatePlan,parsePlan,validDate,dateInZone,daysBetween,summarize,phaseProgress,studySummary,aiPrompt} from '../src/domain/planning.js';
import {selectDiagnostic,createDiagnostic,submitDiagnostic,finishDiagnostic,diagnosticAttempts,diagnosticResult,validateDiagnostic} from '../src/domain/diagnostic.js';

const q={id:'sample',name:'検証資格',defaultExamPartId:'objective',examParts:[{id:'objective',label:'選択式',practiceAvailable:true},{id:'written',label:'記述式',practiceAvailable:false}],topics:[{id:'one',name:'分野1'},{id:'two',name:'分野2'},{id:'three',name:'分野3'}]};
const questions=Array.from({length:60},(_,i)=>({id:`q${i}`,qualificationId:q.id,examPartId:'objective',version:1,type:'singleChoice',packId:'first',packLabel:'検証',number:i+1,title:'足し算',topic:q.topics[i%3].name,topicId:q.topics[i%3].id,source:'検証用',stem:'1＋1は？',sourceImages:[],imageSizes:[],related:[],adaptation:'',choices:[{id:'a',label:'ア',text:'1'},{id:'b',label:'イ',text:'2'}],correctChoiceId:'b',answer:1,enrichment:'reviewed',hintStatus:'individual',hints:[{title:'考える',text:'1に1を足す。',revealsAnswer:false},{title:'答え',text:'2になる。',revealsAnswer:true}],summary:'2',explanation:'1＋1＝2',takeaway:'足す',choiceReasons:['1は加算前','1に1を加算した結果']}));
const validateState=createStateValidator({getQuestions:()=>questions,getTopics:()=>q.topics.map(t=>t.name),getQualification:()=>q});
const validateAttempt=a=>validateState({...makeState(),attempts:[a]});
const validateAssessment=createStateValidator({getQuestions:()=>questions,getTopics:()=>q.topics.map(t=>t.name),getQualification:()=>q,allowDiagnosticOnly:true});
const validateAssessmentAttempt=a=>validateAssessment({...makeState(),attempts:[a]});
const plan=()=>({...blankPlan(q),phases:[{id:'phase',name:'確認',start:'2026-10-07',end:'2026-10-18',examPartIds:['objective'],targets:{completedAttempts:10},focusTopicIds:['one']}]});

test('暦日・閏日・JSTの境界で、残日数と日付がずれない',()=>{
 assert.ok(validDate('2028-02-29'));assert.equal(validDate('2026-02-29'),false);assert.equal(validDate('2026-02-30'),false);assert.equal(validDate('2026-2-3'),false);
 assert.equal(dateInZone('2026-10-06T15:00:00Z','Asia/Tokyo'),'2026-10-07');assert.equal(daysBetween('2026-10-07','2026-11-04'),28);
});

test('本人の計画の前提は任意・厳密に検証し、残日数と診断を一緒にExportする',()=>{
 const p=plan();p.examDates=[{examPartId:'objective',date:'2026-11-04'}];p.context={studiedScope:'教科書を一周',materials:'手元の教材',weeklyMinutes:180,constraints:'休日中心',rationale:'広く確認する',updatedOn:'2026-10-07'};
 assert.deepEqual(parsePlan(JSON.stringify(p),q),p);
 const result=studySummary({qualification:q,plan:p,attempts:[],diagnostics:[{size:30,answered:0}],at:'2026-10-06T15:00:00Z'});
 assert.equal(result.examDates[0].daysUntil,28);assert.deepEqual(result.context,p.context);assert.equal(result.diagnostics[0].size,30);assert.ok(aiPrompt(q,result).includes('本人の前提を引き継ぎ'));
 result.context.rationale='changed';assert.equal(p.context.rationale,'広く確認する');
 for(const context of [null,[],{unknown:'value'},{weeklyMinutes:-1},{weeklyMinutes:1.5},{weeklyMinutes:10081},{weeklyMinutes:'180'},{studiedScope:3},{materials:'x'.repeat(2001)},{updatedOn:'2026-02-30'}])assert.throws(()=>validatePlan({...p,context},q));
 validatePlan({...p,context:{}},q);validatePlan({...p,context:{weeklyMinutes:0}},q);
});

const variants=questions.slice(0,30).map((original,i)=>({...structuredClone(original),id:`variant-${i}`,diagnosticOnly:true,parentQuestionId:original.id,packId:'variants',packLabel:'検証専用',hints:[]}));
test('派生問題は分野枠内で優先し、通常問題で補い、元問題の重複を避ける',()=>{
 const early=selectDiagnostic(questions,q,[],()=>.42,variants);
 assert.equal(early.length,30);assert.equal(early.filter(x=>x.diagnosticOnly).length,3);assert.deepEqual(q.topics.map(t=>early.filter(x=>x.topicId===t.id).length),[10,10,10]);assert.equal(new Set(early.map(x=>x.parentQuestionId||x.id)).size,30);
 const full=selectDiagnostic(questions,{...q,diagnosticBlueprint:{variantLimits:{one:8,two:8,three:8}}},[],()=>.42,variants);
 assert.equal(full.filter(x=>x.diagnosticOnly).length,24);assert.deepEqual(q.topics.map(t=>full.filter(x=>x.topicId===t.id).length),[10,10,10]);assert.equal(new Set(full.map(x=>x.parentQuestionId||x.id)).size,30);
 const additional={...variants[0],id:'same-parent-other'};const selected=selectDiagnostic(questions,q,[],()=>.42,[...variants,additional]);assert.ok(selected.filter(x=>(x.parentQuestionId||x.id)==='q0').length<=1);
 const unseenOriginal=selectDiagnostic(questions,q,variants.map(x=>({questionId:x.id})),()=>.42,variants);assert.equal(unseenOriginal.filter(x=>x.diagnosticOnly).length,0);
 assert.throws(()=>selectDiagnostic(questions,q,[],()=>.42,[{...variants[0],topicId:'two'}]));assert.throws(()=>selectDiagnostic(questions,q,[],()=>.42,[{...variants[0],parentQuestionId:'missing'}]));assert.throws(()=>selectDiagnostic(questions,q,[],()=>.42,[variants[0],variants[0]]));
 assert.throws(()=>selectDiagnostic(questions.slice(0,20),q,[],()=>.42,variants.slice(0,20)));assert.throws(()=>selectDiagnostic(questions,{...q,diagnosticBlueprint:{variantLimits:{one:-1}}}));
});
test('派生の結果と元問題の経験を分離し、通常学習・計画実績へ混ぜない',()=>{
 const chosen=selectDiagnostic(questions,q,[{questionId:'q0'}],()=>.42,variants),run=createDiagnostic(chosen,q,[{questionId:'q0'}],'catalog:variant-bank');
 validateDiagnostic(run,q,validateAssessmentAttempt);const frozen=JSON.stringify(run.slots);
 for(let i=0;i<30;i++)submitDiagnostic(run,run.slots[run.currentIndex].attempt.questionSnapshot.diagnosticOnly?'a':'b');
 const result=diagnosticResult(run,q),derived=result.composition.find(c=>c.kind==='derived');assert.equal(derived.selected,3);assert.equal(derived.answered,3);assert.equal(derived.correct,0);assert.equal(derived.parentPreviouslySeen,run.slots.filter(s=>s.kind==='derived'&&s.parentQuestionId==='q0').length);
 assert.equal(result.items.length,30);assert.equal(result.blueprintVersion,2);assert.equal(JSON.stringify(run.slots),frozen);
 const attempts=diagnosticAttempts(run);assert.equal(attempts.length,30);assert.equal(summarize(attempts,q).all.completedAttempts,27);assert.equal(summarize(attempts,q).all.incorrect,0);
 assert.throws(()=>createAttempt(variants[0]));assert.throws(()=>validateAttempt(run.slots.find(s=>s.kind==='derived').attempt));
 const clone=structuredClone(run);clone.slots[0].kind=clone.slots[0].kind==='derived'?'original':'derived';assert.throws(()=>validateDiagnostic(clone,q,validateAssessmentAttempt));
 const duplicate=structuredClone(run);const originalSlot=duplicate.slots.find(s=>s.kind==='original'),variantSlot=duplicate.slots.find(s=>s.kind==='derived');variantSlot.parentQuestionId=originalSlot.attempt.questionId;variantSlot.attempt.questionSnapshot.parentQuestionId=originalSlot.attempt.questionId;assert.throws(()=>validateDiagnostic(duplicate,q,validateAssessmentAttempt));
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
test('追加前の診断記録を変更せず、その構成と結果を読める',()=>{
 const run=createDiagnostic(questions.slice(0,30),q);run.blueprintVersion=1;delete run.selectionPolicy;
 for(const slot of run.slots){delete slot.kind;delete slot.parentQuestionId;delete slot.parentPreviouslySeen;}
 submitDiagnostic(run,'b');finishDiagnostic(run);const original=JSON.stringify(run);validateDiagnostic(run,q,validateAttempt);
 const result=diagnosticResult(run,q);assert.equal(result.selectionPolicy,null);assert.equal(result.composition[0].selected,30);assert.equal(result.composition[1].selected,0);assert.equal(result.correct,1);assert.equal(JSON.stringify(run),original);
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

test('継続セッションの対象パートを検証し、既存のパート指定なし記録は保持する',()=>{
 const a=createAttempt(questions[0]),s={...makeState(),attempts:[a],session:{attemptIds:[a.id],topic:null,topicId:null,examPartId:'objective'}};
 assert.equal(validateState(structuredClone(s)).session.examPartId,'objective');
 assert.throws(()=>validateState({...structuredClone(s),session:{...s.session,examPartId:'written'}}));
 assert.throws(()=>validateState({...structuredClone(s),session:{...s.session,examPartId:'unknown'}}));
 const old=structuredClone(s);delete old.session.examPartId;assert.equal(validateState(old).attempts[0].id,a.id);
});
