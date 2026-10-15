import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {studyTargets,resolveStudyTarget,rememberPart,rememberedPart,targetLabel,targetCount,targetURL} from '../src/domain/study-target.js';
const root=new URL('https://donald-shrimp.github.io/ap-study/');
const read=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url)));
const ap=read('data/qualifications/ap/manifest.json'),ab=read('data/qualifications/ab730/manifest.json');
test('公開カタログは科目Aの800問と科目Bの22大問を分け、単一科目の資格を1行にする',()=>{
 const catalog=read('data/qualifications/catalog.json');
 assert.deepEqual(catalog.qualifications.find(q=>q.id==='ap').studyTargets,ap.studyTargets);
 assert.deepEqual(studyTargets(ap).map(p=>[p.examPartId,targetCount(p)]),[['objective','800問'],['written','大問22題']]);
 assert.equal(studyTargets(ab).length,1);assert.equal(targetCount(studyTargets(ab)[0]),'174問');
 assert.equal(targetLabel(ap,'written',{short:true}),'応用情報・科目B');assert.equal(targetLabel(ab,'objective',{short:true}),'AB-730');
});
test('明示した科目を記憶より優先し、無効URLと古い記憶を区別する',()=>{
 assert.equal(resolveStudyTarget(ap,{requestedPartId:'objective',rememberedPartId:'written'}),'objective');
 assert.equal(resolveStudyTarget(ap,{rememberedPartId:'written'}),'written');
 assert.equal(resolveStudyTarget(ap,{rememberedPartId:'retired'}),'objective');
 assert.equal(resolveStudyTarget(ap,{requestedPartId:'retired'}),null);
 assert.equal(resolveStudyTarget(ab,{requestedPartId:'written'}),null);
 const old={count:10,defaultExamPartId:'objective',examParts:[{id:'objective',label:'科目A',practiceAvailable:true},{id:'written',label:'科目B',unit:'cases',practiceAvailable:true}]};
 assert.deepEqual(studyTargets(old).map(p=>p.examPartId),['objective']);
});
test('端末の科目記憶を資格ごとに保持し、保存拒否時も明示URLを作れる',()=>{
 const previous=globalThis.localStorage,map=new Map();
 try{
  globalThis.localStorage={getItem:k=>map.get(k)||null,setItem:(k,v)=>map.set(k,v)};
  rememberPart(root,'ap','written');rememberPart(root,'ab730','objective');assert.equal(rememberedPart(root,'ap'),'written');
  globalThis.localStorage={getItem:()=>{throw Error('blocked');},setItem:()=>{throw Error('blocked');}};
  assert.equal(rememberedPart(root,'ap'),null);assert.doesNotThrow(()=>rememberPart(root,'ap','written'));
  assert.equal(targetURL(root,'ap','written',{home:true}).href,'https://donald-shrimp.github.io/ap-study/ap/?part=written&entry=home');
 }finally{if(previous===undefined)delete globalThis.localStorage;else globalThis.localStorage=previous;}
});
test('ローカル試験のAuth設定だけを選択往復で保持し、本番ではエミュレータを指定しない',()=>{
 const local=new URL('http://127.0.0.1:4173/'),from=new URL('http://127.0.0.1:4173/ap/?firebase-emulator=1');
 assert.equal(targetURL(local,'ap','written',{from}).searchParams.get('firebase-emulator'),'1');
 assert.equal(targetURL(root,'ap','written',{from:new URL(root+'?firebase-emulator=1')}).searchParams.get('firebase-emulator'),null);
});
