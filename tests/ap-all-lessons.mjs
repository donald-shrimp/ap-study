import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createAttempt,selectAnswer,openHint,gradeAttempt,finalizeAttempt} from '../src/domain/study.js';
const root=new URL('../',import.meta.url),read=p=>JSON.parse(readFileSync(new URL(p,root),'utf8'));
const dir='data/qualifications/ap/',manifest=read(dir+'manifest.json');
const bank=manifest.packs.flatMap(p=>read(dir+p.url));
test('all 800 published AP lessons grade each cumulative hint state and freeze completed outcomes',()=>{
 assert.equal(bank.length,800);assert.equal(new Set(bank.map(q=>q.id)).size,800);
 let cases=0;
 for(const q of bank){
  assert.equal(q.hints.length,3,q.id);assert.equal(q.choiceReasons.length,4,q.id);
  for(let count=0;count<=3;count++){
   const a=createAttempt(q);selectAnswer(a,q.answer,q);
   for(let n=0;n<count;n++)assert.equal(openHint(a),true,q.id);
   const expected=q.hints.slice(0,count).some(h=>h.revealsAnswer)?'revealed':count?'assisted':'correct';
   assert.equal(gradeAttempt(a),expected,`${q.id} H${count}`);finalizeAttempt(a,expected);
   while(openHint(a)){}
   assert.equal(gradeAttempt(a),expected,`${q.id} completed`);assert.equal(a.hintsBeforeAnswer,count);cases++;
  }
 }
 assert.equal(cases,3200);
});
test('confirmed AP legal change reaches pack and index without changing the historical answer',()=>{
 const q=bank.find(q=>q.id==='r05h-q78');
 assert.equal(q.answer,1);assert.equal(q.correctChoiceId,'choice-1');assert.equal(q.legalReview.status,'outdated');
 const indexed=read(dir+manifest.index.url).find(q=>q.id==='r05h-q78');assert.deepEqual(indexed.legalReview,q.legalReview);
 assert.equal(q.sourceRecord.legalAsOf,null);
});
