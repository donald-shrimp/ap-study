import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {decimalValue,validNumericField} from '../src/domain/decimal-answer.js';
import {validateLegalContext,legalContextLines} from '../src/domain/legal-context.js';
import {createCaseRun,caseFields,setCaseResponse,submitCaseField,viewCaseAnswer,rateCaseField,validateCaseRun,validateCaseMaterial,caseResult,buildWrittenAIPrompt} from '../src/domain/case-study.js';
import {createAttempt,selectAnswer,finalizeAttempt,gradeAttempt} from '../src/domain/study.js';
import {toRecord,fromRecord,validateRecord} from '../src/v2/records.js';
import {blankPlan,phaseProgress,validatePlan,goalsText} from '../src/domain/planning.js';
import {targetCount} from '../src/domain/study-target.js';
import {fixtureCase,numericField,sourceRecord,legalReview} from './fp2-fixtures.mjs';
const q=JSON.parse(readFileSync(new URL('../content/fp2/qualification.json',import.meta.url)));
const at='2026-10-24T00:00:00.000Z';
const filled=(text,field=numericField())=>{const c=fixtureCase();c.items[0].fields=[field];const r=createCaseRun(c,{at});setCaseResponse(r,'q1--'+field.id,text,at);submitCaseField(r,'q1--'+field.id,at);return r;};

test('case figures require unique anchors in rendering order, including saved material',()=>{
 const c=fixtureCase(),figure={image:'assets/written/synthetic/figure.png',anchor:'[one]',alt:'合成図',caption:'合成図'};
 c.body='Before [one] between [two] after';c.bodyFigures=[figure,{...figure,anchor:'[two]'}];validateCaseMaterial(c,q);validateCaseRun(createCaseRun(c,{at}),q);
 for(const change of [c=>c.bodyFigures[0].anchor='missing',c=>c.bodyFigures[0].anchor='',c=>c.body+='[one]',c=>c.bodyFigures.reverse(),c=>c.bodyFigures[1].anchor='[one]']){
  const bad=structuredClone(c);change(bad);assert.throws(()=>validateCaseMaterial(bad,q));assert.throws(()=>validateCaseRun(createCaseRun(bad,{at}),q));
 }
});

test('decimal comparison preserves large integers and exact small fractions',()=>{
 for(const [text,value] of [['１，４９０，０００','1490000'],[' +0001490000 ','1490000'],['0.4350','0.435'],['-0.00','0'],['9007199254740993','9007199254740993']])assert.equal(decimalValue(text),value);
 for(const text of ['1,49,000','1e6','149万円','1490000円','0x10','NaN','Infinity','1 490 000','0.','①','−1'])assert.equal(decimalValue(text),null,text);
});
test('wrong numeric values get an exact fail; input is never rounded or converted',()=>{
 for(const text of ['1490000','1,490,000','１４９００００']){const r=filled(text);assert.equal(r.evaluations['q1--amount'].outcome,'correct');validateCaseRun(r,q);}
 assert.equal(filled('149').evaluations['q1--amount'].outcome,'incorrect');
 const f=numericField('ratio','0.435','倍',3);f.numeric.rounding='halfUp';assert.equal(filled('0.435',f).evaluations['q1--ratio'].outcome,'correct');assert.equal(filled('0.4349',f).evaluations['q1--ratio'].outcome,'incorrect');
 const huge=numericField('large','9007199254740993');assert.equal(filled('9007199254740992',huge).evaluations['q1--large'].outcome,'incorrect');
});
test('unknown notation and skipped numeric fields require self assessment',()=>{
 const r=filled('149万円');assert.deepEqual(r.evaluations,{});viewCaseAnswer(r,'q1--amount',at);rateCaseField(r,'q1--amount','partial',at);validateCaseRun(r,q);assert.equal(r.evaluations['q1--amount'].source,'self');
 const skip=createCaseRun(fixtureCase(),{at});submitCaseField(skip,'q1--amount',at,{skip:true});assert.equal(skip.evaluations['q1--amount'],undefined);validateCaseRun(skip,q);
});
test('numeric metadata is bounded and consistent at import',()=>{
 for(const change of [f=>f.numeric.unit='',f=>f.numeric.decimalPlaces=-1,f=>f.numeric.decimalPlaces=13,f=>f.numeric.rounding='approximate',f=>f.grading.method='exactText',f=>f.referenceAnswers=['1,490,000'],f=>f.referenceAnswers=['0.5'],f=>f.maxLength=101]){const f=numericField();change(f);assert.equal(validNumericField(f),false);const c=fixtureCase();c.items[0].fields=[f];assert.throws(()=>validateCaseMaterial(c,q));}
 const r=filled('1490000');r.evaluations['q1--amount'].outcome='incorrect';assert.throws(()=>validateCaseRun(r,q));
 const unknown=filled('149万円');unknown.evaluations['q1--amount']={source:'automatic',outcome:'correct',at,assisted:false};assert.throws(()=>validateCaseRun(unknown,q));
});
test('four true/false fields are one question record with four separately assessed fields',()=>{
 const c=fixtureCase();c.items[0].fields=Array.from({length:4},(_,n)=>({id:'b'+n,label:'判定'+n,type:'singleChoice',choices:[{id:'true',label:'○',text:'正しい'},{id:'false',label:'×',text:'誤り'}],grading:{method:'exactText'},referenceAnswers:['○'],explanation:'合成の判定。',rubric:['記述の内容。']}));
 const r=createCaseRun(c,{at});for(const {key} of caseFields(c)){setCaseResponse(r,key,'true',at);submitCaseField(r,key,at);}validateCaseRun(r,q);assert.equal(caseResult(r).total,4);assert.equal(caseResult(r).automatic.correct,4);assert.equal(r.progress.status,'completed');
 const p=blankPlan(q);p.phases=[{id:'p',name:'実技',start:'2026-10-24',end:'2026-10-25',examPartIds:['jafp-practical'],focusTopicIds:[],goals:[{examPartId:'jafp-practical',unit:'cases',target:1}]}];validatePlan(p,q);assert.equal(phaseProgress(p,[],q,at,[r])[0].goalProgress[0].actual,1);assert.match(goalsText(p.phases[0].goals,q),/1問/);assert.equal(targetCount({unit:'cases',caseLabel:'問題',countLabel:'問',count:40}),'問題40問');
});
test('legal context distinguishes historical source and present verification without inferring currency',()=>{
 const c=fixtureCase();validateLegalContext(c,{required:true});assert.deepEqual(legalContextLines(c),['法令基準日：2026-04-01']);
 c.sourceRecord.publishedAt=null;validateLegalContext(c,{required:true});c.sourceRecord.legalAsOf=null;assert.deepEqual(legalContextLines(c),[]);validateLegalContext(c,{required:true});
 for(const change of [c=>delete c.sourceRecord,c=>c.sourceRecord.legalAsOf='2026-02-30',c=>c.sourceRecord.questionSha256='bad',c=>c.sourceRecord.modifiedFromOriginal=true,c=>c.legalReview.status='current',c=>c.legalReview.checkedAt='2026-10-24']){const v=fixtureCase();change(v);assert.throws(()=>validateLegalContext(v,{required:true}));}
 c.sourceRecord.legalAsOf='2026-04-01';c.legalReview={status:'outdated',checkedAt:'2026-10-24',sourceRefs:['https://example.com/law'],note:'合成テストの差異。'};validateLegalContext(c,{required:true});assert.ok(legalContextLines(c).includes('法令改正あり（学習非推奨）'));
});
test('numeric snapshot, legal basis and units survive backup, AI and new material versions',()=>{
 const r=filled('1,490,000'),snapshot=structuredClone(r.material);const copy=JSON.parse(JSON.stringify(r));validateCaseRun(copy,q);assert.deepEqual(copy.responses,r.responses);const c=fixtureCase();c.version=2;c.sourceRecord.legalAsOf='2026-10-01';assert.deepEqual(r.material,snapshot);
 const prompt=buildWrittenAIPrompt({question:r.material,attempt:{fieldKey:'q1--amount',response:r.responses['q1--amount']},baseURL:'https://example.com/'});for(const text of ['円','1490000','2026-04-01','最終法令チェック：未実施',sourceRecord.questionSha256])assert.ok(prompt.includes(text),text);assert.ok(!prompt.startsWith('科目B'));
});
test('question v2 records keep and validate the immutable legal context',()=>{
 const q0={...JSON.parse(readFileSync(new URL('../data/qualifications/ab730/manifest.json',import.meta.url))).packs[0]};const manifest=JSON.parse(readFileSync(new URL('../data/qualifications/ab730/manifest.json',import.meta.url)));const question=JSON.parse(readFileSync(new URL('../data/qualifications/ab730/'+q0.url,import.meta.url)))[0];question.sourceRecord=structuredClone(sourceRecord);question.legalReview=structuredClone(legalReview);
 const a=createAttempt(question,{at});selectAnswer(a,question.answer);finalizeAttempt(a,gradeAttempt(a),at);const r=toRecord(a);assert.deepEqual(fromRecord(r).questionSnapshot.sourceRecord,question.sourceRecord);r.material.sourceRecord.legalAsOf='yesterday';assert.throws(()=>validateRecord(r));
});
