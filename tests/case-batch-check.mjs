import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createCaseRun,caseFields,setCaseResponse,submitCaseField,checkCaseItem,viewCaseAnswer,rateCaseField,validateCaseRun} from '../src/domain/case-study.js';
import {encodeResource,decodeResource} from '../src/v2/resources.js';
const read=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url)));
const q=read('data/qualifications/ap/manifest.json'),material=read('content/ap/written-cases.json').find(c=>c.id==='ap-r07h-pm1');
const at='2026-10-25T07:00:00.000Z',later='2026-10-25T07:01:00.000Z';
const correct=f=>f.type==='singleChoice'?f.choices.find(c=>c.label===f.referenceAnswers[0]).id:f.referenceAnswers[0];
function enter(run,itemId){for(const s of caseFields(run.material).filter(s=>s.item.id===itemId))setCaseResponse(run,s.key,correct(s.field),at);}
test('小問群を全て確定してから開示し、同じ一括操作内は支援付きにしない',()=>{
 const r=createCaseRun(material,{at});enter(r,'q2');checkCaseItem(r,'q2',at);
 assert.deepEqual(r.progress.submittedFieldKeys,['q2--a','q2--b']);assert.deepEqual(r.assistance.viewedFields,['q2--a','q2--b']);
 for(const e of Object.values(r.evaluations)){assert.equal(e.outcome,'correct');assert.equal(e.assisted,false);}
 assert.equal(r.responses['q1--answer'],undefined);assert.equal(r.progress.status,'in_progress');validateCaseRun(r,q);
 const before=structuredClone(r);checkCaseItem(r,'q2',later);assert.deepEqual(r,before);
 assert.deepEqual(decodeResource('case',encodeResource('case',r)),r);
});
test('短答の未知表現と記述は公式解答を開くだけで自己評価を捏造しない',()=>{
 const r=createCaseRun(material,{at});setCaseResponse(r,'q3--setting','未知の表現',at);setCaseResponse(r,'q3--reason','自分の説明',at);checkCaseItem(r,'q3',at);
 assert.deepEqual(r.evaluations,{});assert.equal(r.assistance.viewedFields.length,2);assert.equal(r.progress.status,'in_progress');
 rateCaseField(r,'q3--setting','partial',later);assert.equal(r.evaluations['q3--reason'],undefined);validateCaseRun(r,q);
});
test('空欄は未回答で残し、開示後に解く欄には既存の支援フラグを付ける',()=>{
 const r=createCaseRun(material,{at}),before=structuredClone(r);checkCaseItem(r,'q3',at);assert.deepEqual(r,before);
 setCaseResponse(r,'q3--setting','未確認の表現',at);checkCaseItem(r,'q3',at);assert.equal(r.responses['q3--reason'],undefined);
 const first=structuredClone(r.responses['q3--setting']);setCaseResponse(r,'q3--reason','後から考えた説明',later);checkCaseItem(r,'q3',later);
 assert.deepEqual(r.responses['q3--setting'],first);assert.equal(r.responses['q3--reason'].answerViewedBefore,true);validateCaseRun(r,q);
});
test('最後にまとめてモードは全欄確定まで一括でも正答を開かない',()=>{
 const r=createCaseRun(material,{mode:'exam',at});enter(r,'q2');checkCaseItem(r,'q2',at);assert.deepEqual(r.assistance.viewedFields,[]);assert.equal(r.assistance.firstAnswerViewedAt,null);
 for(const s of caseFields(material))if(!r.responses[s.key]?.submittedAt){setCaseResponse(r,s.key,correct(s.field),at);submitCaseField(r,s.key,at);}
 checkCaseItem(r,'q2',later);assert.deepEqual(r.assistance.viewedFields,['q2--a','q2--b']);assert.equal(r.responses['q1--answer'].answerViewedBefore,false);validateCaseRun(r,q);
});
test('既に解答を見ている取り組みの支援判定と手動確定済み回答を保つ',()=>{
 const r=createCaseRun(material,{at});enter(r,'q1');submitCaseField(r,'q1--answer',at);viewCaseAnswer(r,'q1--answer',at);enter(r,'q2');submitCaseField(r,'q2--a',later);const a=structuredClone(r.responses['q2--a']);checkCaseItem(r,'q2',later);
 assert.deepEqual(r.responses['q2--a'],a);assert.equal(r.evaluations['q2--b'].assisted,true);validateCaseRun(r,q);
 const before=structuredClone(r);assert.throws(()=>checkCaseItem(r,'missing',later));assert.deepEqual(r,before);
});
test('FP実技の選択肢・数値も共通の自動判定と保存形式を使う',()=>{
 const fq=read('data/qualifications/fp2/manifest.json'),cases=read('content/fp2/practical-cases.json');
 for(const c of [cases[0],cases.find(c=>c.items.some(i=>i.fields.length>1&&i.fields.some(f=>f.type==='numeric')))]){
  assert.ok(c);const r=createCaseRun(c,{at});for(const i of c.items){enter(r,i.id);checkCaseItem(r,i.id,at);}
  assert.equal(r.progress.status,'completed');assert.ok(Object.values(r.evaluations).every(e=>e.outcome==='correct'));validateCaseRun(r,fq);
 }
});
