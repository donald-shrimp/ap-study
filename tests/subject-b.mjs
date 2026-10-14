import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createCaseRun,caseFields,setCaseResponse,submitCaseField,viewCaseAnswer,rateCaseField,mayViewAnswer,caseResult,validateCaseRun,buildWrittenAIPrompt} from '../src/domain/case-study.js';
import {createAttempt,makeState,selectAnswer,finalizeAttempt,gradeAttempt,openHint} from '../src/domain/study.js';
import {blankPlan,validatePlan,phaseProgress,studySummary} from '../src/domain/planning.js';
import {toRecord,fromRecord,encodeState,decodeState,validateRecord,mergeBackupState} from '../src/v2/records.js';
import {createDiagnostic,submitDiagnostic} from '../src/domain/diagnostic.js';
import {encodeResource,decodeResource} from '../src/v2/resources.js';
import {convertBackup,convertPlan} from '../tools/convert-study-backup.mjs';
const read=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url)));
const q=read('data/qualifications/ap/manifest.json'),bank=read('content/ap/written-cases.json'),c=bank[0];
const questions=q.packs.flatMap(p=>read('data/qualifications/ap/'+p.url));
const date='2026-10-15T00:00:00.000Z',run=options=>createCaseRun(c,{at:date,...options});
const fill=(r,slot)=>{const f=slot.field,value=f.type==='singleChoice'?f.choices.find(a=>a.label===f.referenceAnswers[0]).id:f.referenceAnswers[0];setCaseResponse(r,slot.key,value,date);submitCaseField(r,slot.key,date);};
test('別端末の同一バックアップ再取り込みは表示位置を保持し、回答・教材の差だけを拒否する',()=>{
 const a=createAttempt(questions[0],{at:date});selectAnswer(a,a.questionSnapshot.answer);finalizeAttempt(a,gradeAttempt(a),date);
 const current={...makeState(),attempts:[a]},incoming=structuredClone(current);incoming.attempts[0].scrollY=420;incoming.attempts[0].readingNote='別端末の表示メモ';
 const before=structuredClone(current),merged=mergeBackupState(current,incoming);
 assert.equal(merged.attempts.length,1);assert.equal(merged.attempts[0].scrollY,0);assert.equal(merged.attempts[0].readingNote,'');assert.deepEqual(current,before);
 const answer=structuredClone(incoming);answer.attempts[0].selectedChoiceId=a.questionSnapshot.choices.find(c=>c.id!==a.selectedChoiceId).id;
 assert.throws(()=>mergeBackupState(current,answer),/同じIDの異なる学習記録/);
 const lesson=structuredClone(incoming);lesson.attempts[0].materialSnapshot.summary+='改訂';assert.throws(()=>mergeBackupState(current,lesson),/同じIDの異なる学習記録/);
 const assistance=structuredClone(incoming);assistance.attempts[0].answerViewedBefore=!a.answerViewedBefore;assert.throws(()=>mergeBackupState(current,assistance),/同じIDの異なる学習記録/);
 assert.deepEqual(current,before);
});
test('記録・回答ベクトルは新形式のみ。状態・診断にも旧回答形式を残さない',()=>{
 const a=createAttempt(questions[0],{at:date});openHint(a,date);selectAnswer(a,a.questionSnapshot.answer);finalizeAttempt(a,gradeAttempt(a),date);const r=toRecord(a);assert.equal(r.version,2);assert.equal(r.evaluation.outcome,'assisted');assert.deepEqual(r.response.choiceIds,[a.selectedChoiceId]);assert.ok(!('answer' in r.material)&&!('correctChoiceId' in r.material));assert.deepEqual(fromRecord(r),a);
 const state={...makeState(),attempts:[a]},encoded=encodeState(state);assert.ok(!('attempts' in encoded));assert.deepEqual(decodeState(encoded).attempts,[a]);assert.throws(()=>decodeState({...state,version:1}));assert.throws(()=>validateRecord({...r,selected:0}));assert.throws(()=>validateRecord({...r,assistance:{...r.assistance,extra:true}}));assert.throws(()=>validateRecord({...r,progress:{...r.progress,confidence:'yes'}}));
 const d=createDiagnostic(questions.slice(0,30),q);submitDiagnostic(d,d.slots[0].attempt.questionSnapshot.correctChoiceId);const wire=encodeResource('diagnostic',d);assert.ok(!('attempt' in wire.slots[0]));assert.ok(!('currentChoiceId' in wire));assert.deepEqual(decodeResource('diagnostic',wire),d);assert.throws(()=>decodeResource('diagnostic',{...wire,version:1}));
});
test('8欄を持つ大問。選択は自動、短答の未知表現は自己評価へ残す',()=>{
 const r=run(),slots=caseFields(c);assert.equal(slots.length,8);setCaseResponse(r,slots[0].key,'未知表現',date);submitCaseField(r,slots[0].key,date);assert.equal(r.evaluations[slots[0].key],undefined);validateCaseRun(r,q);assert.throws(()=>rateCaseField(r,slots[0].key,'meets',date));viewCaseAnswer(r,slots[0].key,date);rateCaseField(r,slots[0].key,'unsure',date);validateCaseRun(r,q);assert.equal(r.evaluations[slots[0].key].source,'self');
 const choice=slots.find(s=>s.field.type==='singleChoice');fill(r,choice);assert.equal(r.evaluations[choice.key].outcome,'correct');assert.equal(r.evaluations[choice.key].assisted,true);assert.throws(()=>setCaseResponse(r,choice.key,choice.field.choices[0].id,date));
});
test('解答を最後に確認する練習では、小問解答・自己評価・AIへの解答提供を伏せる',()=>{
 const r=run({mode:'exam'}),slots=caseFields(c);fill(r,slots[0]);assert.equal(mayViewAnswer(r,slots[0].key),false);assert.throws(()=>viewCaseAnswer(r,slots[0].key,date));for(const slot of slots.slice(1))fill(r,slot);assert.equal(r.progress.status,'awaiting_evaluation');assert.equal(r.completedAt,null);for(const slot of slots){viewCaseAnswer(r,slot.key,date);if(!r.evaluations[slot.key])rateCaseField(r,slot.key,'meets',date);}validateCaseRun(r,q);assert.equal(r.progress.status,'completed');assert.equal(caseResult(r).automatic.correct,5);assert.equal(caseResult(r).self.meets,3);
});
test('分からない欄も明示して確定できる。空欄の自動正解・完了の偽装はしない',()=>{
 const r=run();for(const slot of caseFields(c)){submitCaseField(r,slot.key,date,{skip:true});viewCaseAnswer(r,slot.key,date);if(!r.evaluations[slot.key])rateCaseField(r,slot.key,'notYet',date);}validateCaseRun(r,q);assert.equal(r.progress.status,'completed');assert.equal(caseResult(r).automatic.correct,0);assert.equal(caseResult(r).self.notYet,5);const fake=run();fake.progress.status='completed';fake.completedAt=date;assert.throws(()=>validateCaseRun(fake,q));
});
test('Aの問数とBの題数・評価方法を混ぜず、未来の完了を集計しない',()=>{
 const p=blankPlan(q);p.phases=[{id:'both',name:'共通計画',start:'2026-10-15',end:'2026-10-20',examPartIds:['objective','written'],focusTopicIds:[],goals:[{examPartId:'objective',unit:'questionAttempts',target:2},{examPartId:'written',unit:'cases',target:1}]}];validatePlan(p,q);const a=createAttempt(questions[0],{at:date});selectAnswer(a,a.questionSnapshot.answer);finalizeAttempt(a,'correct',date);const r=run();for(const slot of caseFields(c)){fill(r,slot);if(!r.evaluations[slot.key]){viewCaseAnswer(r,slot.key,date);rateCaseField(r,slot.key,'partial',date);}}
 assert.deepEqual(phaseProgress(p,[a],q,date,[r])[0].goalProgress.map(g=>g.actual),[1,1]);assert.deepEqual(phaseProgress(p,[a],q,'2026-10-14T23:00:00Z',[r])[0].goalProgress.map(g=>g.actual),[0,0]);assert.equal(studySummary({qualification:q,plan:p,attempts:[a],caseRuns:[r],at:'2026-10-14T23:00:00Z'}).learningByPart[1].completedCases,0);const invalid=structuredClone(p);invalid.phases[0].goals[1].unit='questionAttempts';assert.throws(()=>validatePlan(invalid,q));
});
test('不正な回答・評価・教材画像・字数・別資格をImport前に拒否する',()=>{
 for(const change of [r=>r.qualificationId='ab730',r=>r.material.bodyFigures[0].image='javascript:alert(1)',r=>r.responses.x={value:'x',submittedAt:date,evaluation:null,answerViewedBefore:false},r=>r.progress.pane='bad',r=>r.progress.questionScroll=-1,r=>r.material.items[0].fields[0].maxLength=100000]){const r=run();change(r);assert.throws(()=>validateCaseRun(r,q));}
 const r=run(),slot=caseFields(c)[0];assert.throws(()=>setCaseResponse(r,slot.key,'長'.repeat(13),date));fill(r,slot);const fake=structuredClone(r);fake.evaluations[slot.key].outcome='incorrect';assert.throws(()=>validateCaseRun(fake,q));
});
test('BのAI質問はこの欄と本文・原本URL・解説を含み、未確定欄の解答を渡さない',()=>{
 const r=run(),slots=caseFields(c),slot=slots[0];fill(r,slot);const text=buildWrittenAIPrompt({question:c,attempt:{fieldKey:slot.key,response:r.responses[slot.key]},baseURL:'https://example.com/ap-study/'});assert.ok(text.includes(c.body));assert.ok(text.includes(slot.field.referenceAnswers[0]));assert.ok(!text.includes(slots.at(-1).field.explanation));assert.ok(text.includes('https://example.com/ap-study/assets/written/'));assert.throws(()=>buildWrittenAIPrompt({question:c,attempt:{fieldKey:slots.at(-1).key,response:{}},baseURL:'https://example.com/'}));
});
test('旧ファイルはCLIで一回変換。元の記録・日時・支援・計画履歴を失わない',()=>{
 const a=createAttempt(questions[0],{at:date});openHint(a,date);selectAnswer(a,a.questionSnapshot.answer);finalizeAttempt(a,'assisted',date);const old={...makeState(),version:1,attempts:[a]};const p={...blankPlan(q),version:1,phases:[{id:'old',name:'旧計画',start:'2026-10-15',end:'2026-10-20',examPartIds:['objective'],targets:{completedAttempts:5},focusTopicIds:[],weeklyTargets:[{id:'week',start:'2026-10-15',end:'2026-10-20',completedAttempts:5}]}]};old.workspaceBackup={format:'hitomon-workspace-backup',version:1,qualificationId:q.id,plan:p,runs:[],planRevisions:[{format:'hitomon-plan-revision',version:1,id:'plan--one',qualificationId:q.id,savedAt:date,origin:'registered',previousId:null,plan:p}]};const before=JSON.stringify(old),converted=convertBackup(old,q,{questions});assert.equal(JSON.stringify(old),before);assert.equal(converted.records[0].evaluation.outcome,'assisted');assert.equal(converted.records[0].assistance.hintEvents.length,1);assert.equal(converted.workspaceBackup.plan.phases[0].goals[0].unit,'questionAttempts');assert.equal(converted.workspaceBackup.planRevisions[0].version,2);assert.throws(()=>convertBackup(converted,q,{questions}));const mixed=structuredClone(p);mixed.phases[0].examPartIds=['objective','written'];assert.equal(convertPlan(mixed,q).phases[0].goals[0].examPartId,'objective');
});
