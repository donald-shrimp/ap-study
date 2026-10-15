import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createCaseRun,caseFields,setCaseResponse,submitCaseField,viewCaseAnswer,rateCaseField,validateCaseMaterial,validateCaseRun,caseResult,buildWrittenAIPrompt} from '../src/domain/case-study.js';
const read=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url)));
const qualification=read('data/qualifications/ap/manifest.json'),cases=read('content/ap/written-cases.json');
const expected=[6,7].flatMap(year=>['h','a'].flatMap(season=>Array.from({length:11},(_,i)=>`ap-r0${year}${season}-pm${i+1}`)));
const date='2026-10-15T00:00:00.000Z';
test('公開4回の全44大問が重複せず生成され、Aの800問とは別に数えられる',()=>{
 assert.deepEqual(cases.map(c=>c.id).sort(),expected.sort());assert.equal(qualification.cases.count,44);
 assert.equal(qualification.count,800);assert.equal(qualification.studyTargets.find(p=>p.examPartId==='written').count,44);
});
for(const c of cases)test(`${c.id}: 全欄の回答・評価・記録往復・AIと原本参照`,()=>{
 validateCaseMaterial(c,qualification);const run=createCaseRun(c,{mode:'exam',at:date}),slots=caseFields(c);
 for(const slot of slots){const f=slot.field,value=f.type==='singleChoice'?f.choices.find(choice=>choice.label===f.referenceAnswers[0]).id:f.referenceAnswers[0];setCaseResponse(run,slot.key,value,date);submitCaseField(run,slot.key,date);}
 for(const slot of slots){viewCaseAnswer(run,slot.key,date);if(!run.evaluations[slot.key])rateCaseField(run,slot.key,'meets',date);}
 assert.equal(run.progress.status,'completed');validateCaseRun(JSON.parse(JSON.stringify(run)),qualification);
 assert.equal(caseResult(run).submitted,slots.length);assert.equal(caseResult(run).evaluated,slots.length);
 const first=slots[0],prompt=buildWrittenAIPrompt({question:c,attempt:{fieldKey:first.key,response:run.responses[first.key]},baseURL:'https://donald-shrimp.github.io/ap-study/'});
 assert.ok(prompt.includes(c.body));assert.ok(prompt.includes(first.item.prompt));assert.ok(prompt.includes(first.field.referenceAnswers[0]));for(const p of c.sourceImages)assert.ok(prompt.includes(p));
});
