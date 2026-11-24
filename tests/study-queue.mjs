import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {studyQueue,caseRecommendation,validCaseScope} from '../src/domain/study-queue.js';
const items=[{id:'q10',examPartId:'written',topicId:'network',packId:'2025',number:10},{id:'q2',examPartId:'written',topicId:'security',packId:'2025',number:2},{id:'q1',examPartId:'written',topicId:'network',packId:'2025',number:1},{id:'other',examPartId:'objective',topicId:'network',packId:'2025',number:1},{id:'old',examPartId:'written',topicId:'network',packId:'2024',number:1}];
test('scope + number ordering preserves whole materials, numeric order and visited exclusions',()=>{
 assert.deepEqual(studyQueue(items,{scope:{examPartId:'written',packId:'2025',order:'number'}}).map(x=>x.id),['q1','q2','q10']);
 assert.deepEqual(studyQueue(items,{scope:{examPartId:'written',packId:'2025',topicId:'network',order:'number'},visited:['q1']}).map(x=>x.id),['q10']);
 assert.equal(studyQueue(items,{scope:{examPartId:'written'},allowed:c=>c.id!=='q1',available:c=>c.id==='q1'}).length,0);
 assert.equal(studyQueue(items,{visited:items.map(c=>c.id)}).length,0);
});
test('recommendation prefers unseen, then fields needing another attempt; seeded ties are stable',()=>{
 const runs=[{caseId:'q1',updatedAt:'2026-10-01',evaluations:{a:{outcome:'correct'}}},{caseId:'q2',updatedAt:'2026-10-02',evaluations:{a:{outcome:'partial'}}}];
 const order=studyQueue(items.slice(0,3),{compareRecommended:caseRecommendation(runs,{seed:'scope'})});
 assert.deepEqual(order.map(c=>c.id),['q10','q2','q1']);
 assert.deepEqual(studyQueue(items,{compareRecommended:caseRecommendation([],{seed:'same'})}),studyQueue(items,{compareRecommended:caseRecommendation([],{seed:'same'})}));
});
for(const id of ['ap','fp2'])test(`${id}: explicit case catalog covers current source without modifying reviewed material`,()=>{
 const read=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url)));
 const q=read(`content/${id}/qualification.json`),cs=read(q.caseSource),catalog=read(q.caseCatalogSource),manifest=read(`data/qualifications/${id}/manifest.json`);
 assert.equal(catalog.entries.length,cs.length);assert.deepEqual(new Set(catalog.entries.map(e=>e.caseId)),new Set(cs.map(c=>c.id)));
 assert.deepEqual(manifest.cases.index,catalog.entries);
 const scope={examPartId:q.examParts.find(p=>p.unit==='cases').id,topicId:null,topicIds:[],packId:catalog.entries[0].packId,order:'number',sessionId:'fixture'};
 assert.equal(validCaseScope(scope,q,catalog.entries),true);assert.equal(validCaseScope({...scope,order:'random'},q,catalog.entries),false);
 assert.equal(validCaseScope({...scope,examPartId:'objective'},q,catalog.entries),false);
 assert.equal(validCaseScope({...scope,topicIds:['unknown']},q,catalog.entries),false);
 for(const packId of new Set(catalog.entries.map(e=>e.packId))){const numbers=catalog.entries.filter(e=>e.packId===packId).map(e=>e.number).sort((a,b)=>a-b);assert.deepEqual(numbers,Array.from({length:numbers.length},(_,i)=>i+1));}
});

test('AP subject B uses the IPA booklet fields across published sessions',()=>{
 const read=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url)));
 const manifest=read('data/qualifications/ap/manifest.json');
 const catalog=read('content/ap/case-catalog.json');
 const materials=read('content/ap/written-cases.json');
 const topics=manifest.cases.topics;
 const expected=['情報セキュリティ','経営戦略','プログラミング','システムアーキテクチャ','ネットワーク','データベース',
  '組込みシステム開発','情報システム開発','プロジェクトマネジメント','サービスマネジメント','システム監査'];
 assert.deepEqual(topics,catalog.topics);
 assert.deepEqual(topics.map(t=>t.name),expected);
 const index=manifest.cases.index;
 const byId=new Map(materials.map(c=>[c.id,c]));
 const items=index.map(entry=>({...byId.get(entry.caseId),...entry}));
 assert.equal(items.length,materials.length);
 for(const item of items)assert.equal(topics.find(t=>t.id===item.caseTopicId)?.name,expected[item.number-1]);
 const scope={examPartId:'written',topicId:topics[10].id,topicIds:[],packId:null,order:'recommended',sessionId:'fixture'};
 assert.equal(validCaseScope(scope,manifest,index),true);
 assert.deepEqual(studyQueue(items,{scope}).map(c=>c.number),items.filter(c=>c.number===11).map(c=>c.number));
 assert.deepEqual(studyQueue(items,{scope:{...scope,topicId:topics[9].id}}).map(c=>c.number),items.filter(c=>c.number===10).map(c=>c.number));
 const legacy={...scope,topicId:'service'};
 assert.equal(validCaseScope(legacy,manifest,index),true);
 assert(new Set(studyQueue(items,{scope:legacy}).map(c=>c.number)).size>=2);
 assert.deepEqual(studyQueue(items,{scope:legacy}).map(c=>c.id),items.filter(c=>c.topicId==='service').map(c=>c.id));
});
