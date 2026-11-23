import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {linkedCaseField,withAnswerSets} from '../src/domain/case-answer-set.js';
import {caseFields,checkCaseItem,createCaseRun,mayViewAnswer,rateCaseField,setCaseResponse,submitCaseField,validateCaseRun,viewCaseAnswer} from '../src/domain/case-study.js';
import {decodeResource,encodeResource} from '../src/v2/resources.js';

const read=path=>JSON.parse(readFileSync(new URL('../data/qualifications/ap/'+path,import.meta.url)));
const manifest=read('manifest.json');
const bank=read(manifest.cases.url);
const answerSets=read(manifest.cases.answerSets.url).revisions;
const byCase=new Map(bank.cases.map(c=>[c.id,c]));
const revised=id=>withAnswerSets(byCase.get(id),answerSets[id]);
const date='2026-11-19T00:00:00.000Z';
const makeRun=(id,mode='learning')=>createCaseRun(revised(id),{mode,at:date});
const input=(run,key,values)=>setCaseResponse(run,key,JSON.stringify(values),date);

test('38 groups preserve original material, round data and the original answer links',()=>{
 let groups=0;
 for(const [id,revision] of Object.entries(answerSets)){
  const original=byCase.get(id),updated=revised(id);
  assert.equal(updated.version,original.version+1);
  assert.equal(updated.body,original.body);
  assert.deepEqual(updated.bodyFigures,original.bodyFigures);
  assert.ok(caseFields(updated).length<=20);
  for(const item of original.items){
   const active=updated.items.find(i=>i.id===item.id);
   for(const old of item.fields)assert.ok(linkedCaseField(active,old.id),id+' '+old.id);
   groups+=revision.items[item.id]?.groups.length??0;
  }
  validateCaseRun(createCaseRun(original,{at:date}),manifest);
  const run=createCaseRun(updated,{at:date});
  for(const {key,field} of caseFields(updated)){
   if(field.type!=='answerSet')continue;
   input(run,key,field.referenceAnswers.map(v=>field.choices?.find(c=>c.label===v).id??v).reverse());
   submitCaseField(run,key,date);
   assert.equal(run.evaluations[key].outcome,'correct',id+' '+key);
  }
  validateCaseRun(decodeResource('case',encodeResource('case',run)),manifest);
 }
 assert.equal(groups,38);
 assert.equal(Object.keys(answerSets).length,29);
});

test('named choices require both entries, then accept either order and reject duplicates',()=>{
 const id='ap-r07h-pm2',key='q2-1--bc';
 for(const [answers,expected] of [
  [['choice-2','choice-3'],'correct'],[['choice-3','choice-2'],'correct'],
  [['choice-2','choice-2'],'incorrect'],[['choice-2','choice-4'],'incorrect']
 ]){
  const run=makeRun(id,'exam');
  input(run,key,[answers[0],'']);
  checkCaseItem(run,'q2-1',date,{reveal:false});
  assert.equal(run.responses[key].submittedAt,null);
  assert.throws(()=>submitCaseField(run,key,date));
  input(run,key,answers);
  checkCaseItem(run,'q2-1',date,{reveal:false});
  assert.equal(run.evaluations[key].outcome,expected);
  assert.equal(mayViewAnswer(run,key),false);
  assert.throws(()=>viewCaseAnswer(run,key,date));
  validateCaseRun(run,manifest);
 }
});

test('unordered text rejects missing, duplicate or extra items and leaves new spellings for review',()=>{
 const id='ap-r04h-pm8',key='q4--ab',field=caseFields(revised(id)).find(slot=>slot.key===key).field;
 const [first,second]=field.referenceAnswers;
 const invalid=makeRun(id);
 assert.throws(()=>input(invalid,key,[first,'文'.repeat(21)]));
 const run=makeRun(id);
 input(run,key,[second,'ヘッダーにあるレコード件数']);
 submitCaseField(run,key,date);
 assert.equal(run.evaluations[key],undefined);
 viewCaseAnswer(run,key,date);
 rateCaseField(run,key,'meets',date);
 validateCaseRun(run,manifest);
 const dynamic='q3-1--answer',dynamicCase='ap-r05a-pm8';
 for(const values of [['処理2'],['処理２','処理2'],['処理2','処理7','処理3']]){
  const run=makeRun(dynamicCase);
  input(run,dynamic,values);
  submitCaseField(run,dynamic,date);
  assert.equal(run.evaluations[dynamic].outcome,'incorrect');
  validateCaseRun(run,manifest);
 }
});
