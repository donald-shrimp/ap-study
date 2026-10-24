import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {loadCatalog,appRoot,contentCacheName} from '../src/content/catalog.js';
const digest=s=>createHash('sha256').update(s).digest('hex');
const url=path=>new URL(path,appRoot).href;
const manifestURL=url('data/qualifications/ab730/manifest.json');
async function fixture(t){
 const saved=new Map(),overrides=new Map(),calls=[];
 const cache={match:async key=>saved.get(String(key))?.clone(),put:async(key,r)=>{saved.set(String(key),r.clone());},delete:async key=>saved.delete(String(key))};
 const prior=Object.getOwnPropertyDescriptor(globalThis,'caches');
 Object.defineProperty(globalThis,'caches',{configurable:true,value:{open:async name=>{assert.equal(name,contentCacheName);return cache;}}});
 t.after(()=>{if(prior)Object.defineProperty(globalThis,'caches',prior);else delete globalThis.caches;});
 t.mock.method(globalThis,'fetch',async(input,options)=>{const key=String(input);calls.push({key,options});const override=overrides.get(key),body=typeof override==='function'?await override(options):override??await readFile(new URL(key),'utf8');return body instanceof Response?body.clone():new Response(body);});
 const manifest=JSON.parse(await readFile(new URL(manifestURL),'utf8')),indexURL=new URL(manifest.index.url,manifestURL).href;
 // Node imports this module from file://. Give the FP image an HTTP fixture
 // URL while retaining the real corpus; production intentionally rejects file assets.
 const fpURL=url('data/qualifications/fp2/manifest.json'),fp=JSON.parse(await readFile(new URL(fpURL),'utf8')),fpIndexURL=new URL(fp.index.url,fpURL).href,fpIndex=JSON.parse(await readFile(new URL(fpIndexURL),'utf8'));
 for(const q of fpIndex)if(q.image)q.image=new URL(q.image,'https://fixture.test/').href;
 const fpBody=JSON.stringify(fpIndex);fp.index.sha256=digest(fpBody);overrides.set(fpIndexURL,fpBody);overrides.set(fpURL,JSON.stringify(fp));
 return {saved,cache,overrides,calls,manifest,indexURL,fpManifest:fp};
}
test('SHAが一致する保存済み教材はfetchせず使い、資格manifestの更新経路を残す',async t=>{
 const f=await fixture(t);await loadCatalog('ab730');f.calls.length=0;
 const c=await loadCatalog('ab730');assert.equal(c.questions.length,174);assert(!f.calls.some(c=>c.key===f.indexURL));assert(f.calls.some(c=>c.key===manifestURL));
});
test('壊れた教材キャッシュを使用せず、SWも迂回して再取得・再検証する',async t=>{
 const f=await fixture(t);await loadCatalog('ab730');f.saved.set(f.indexURL,new Response('[{"id":"wrong"}]'));f.calls.length=0;
 const c=await loadCatalog('ab730');assert.equal(c.questions.length,174);assert.equal(f.calls.find(c=>c.key===f.indexURL).options.cache,'reload');assert.equal(digest(await f.saved.get(f.indexURL).clone().text()),f.manifest.index.sha256);
});
test('manifestのSHA更新時は同じURLでも古い本文を使わない',async t=>{
 const f=await fixture(t);await loadCatalog('ab730');const index=JSON.parse(await readFile(new URL(f.indexURL),'utf8'));index[0].title+=' 更新確認';const body=JSON.stringify(index);f.manifest.index.sha256=digest(body);f.overrides.set(manifestURL,JSON.stringify(f.manifest));f.overrides.set(f.indexURL,body);f.calls.length=0;
 const c=await loadCatalog('ab730');assert(c.questions[0].title.endsWith('更新確認'));assert.equal(f.calls.find(c=>c.key===f.indexURL).options.cache,'reload');
});
test('再取得も不正なSHAならfail closedで、壊れた内容を保存しない',async t=>{
 const f=await fixture(t);await loadCatalog('ab730');f.saved.set(f.indexURL,new Response('[]'));f.overrides.set(f.indexURL,'[]');await assert.rejects(loadCatalog('ab730'),e=>e.name==='ContentLoadError'&&e.detail.includes('教材の確認に失敗'));assert(!f.saved.has(f.indexURL));
});
test('SWが返した古いmanifestで、裏で更新済みのキャッシュを上書きしない',async t=>{
 const f=await fixture(t),listingURL=url('data/qualifications/catalog.json'),old=await readFile(new URL(listingURL),'utf8');const fresh=JSON.parse(old);fresh.qualifications[0].name+=' 更新確認';await f.cache.put(listingURL,new Response(JSON.stringify(fresh)));f.overrides.set(listingURL,new Response(old,{headers:{'X-Hitomon-Cache':'1'}}));
 await loadCatalog(null,{choose:true});assert.equal((await f.saved.get(listingURL).clone().json()).qualifications[0].name,fresh.qualifications[0].name);
});
test('CacheStorageが使えなくてもオンライン教材を読める',async t=>{
 await fixture(t);globalThis.caches.open=async()=>{throw Error('quota')};assert.equal((await loadCatalog('ab730')).questions.length,174);
});
test('古い資格一覧に新しい資格がなくても、SWの再検証を待たず直接開ける',async t=>{
 const f=await fixture(t),listingURL=url('data/qualifications/catalog.json'),fresh=await readFile(new URL(listingURL),'utf8'),old=JSON.parse(fresh);
 old.qualifications=old.qualifications.filter(q=>q.id!=='fp2');
 f.overrides.set(listingURL,options=>options.cache==='reload'?fresh:new Response(JSON.stringify(old),{headers:{'X-Hitomon-Cache':'1'}}));
 const c=await loadCatalog('fp2',{requestedPartId:'jafp-practical'});
 assert.equal(c.manifest.cases.count,40);assert.equal(f.calls.filter(c=>c.key===listingURL).length,2);assert.equal(f.calls.filter(c=>c.key===listingURL)[1].options.cache,'reload');
 f.calls.length=0;assert.equal((await loadCatalog(null,{preferredId:'fp2'})).manifest.id,'fp2');assert.equal(f.calls.filter(c=>c.key===listingURL).length,2);
});
test('新科目を含まない資格manifestも一度取り直し、選択画面へ戻さない',async t=>{
 const f=await fixture(t),key=url('data/qualifications/fp2/manifest.json'),fresh=JSON.stringify(f.fpManifest),old=JSON.parse(fresh);
 old.studyTargets=old.studyTargets.filter(p=>p.examPartId!=='jafp-practical');old.cases.count=0;
 f.overrides.set(key,options=>options.cache==='reload'?fresh:new Response(JSON.stringify(old),{headers:{'X-Hitomon-Cache':'1'}}));
 const c=await loadCatalog('fp2',{requestedPartId:'jafp-practical'});
 assert.equal(c.choose,undefined);assert.equal(c.manifest.cases.count,40);assert.equal(f.calls.filter(c=>c.key===key).length,2);assert.equal(f.calls.filter(c=>c.key===key)[1].options.cache,'reload');
});
test('古い一覧から開く科目選択でも、新しい科目を表示する',async t=>{
 const f=await fixture(t),key=url('data/qualifications/catalog.json'),fresh=await readFile(new URL(key),'utf8'),old=JSON.parse(fresh);
 old.qualifications.find(q=>q.id==='fp2').studyTargets=old.qualifications.find(q=>q.id==='fp2').studyTargets.filter(p=>p.examPartId==='objective');
 f.overrides.set(key,options=>options.cache==='reload'?fresh:new Response(JSON.stringify(old),{headers:{'X-Hitomon-Cache':'1'}}));
 const c=await loadCatalog('fp2',{choose:true,requestedPartId:'jafp-practical'});
 assert(c.qualifications.find(q=>q.id==='fp2').studyTargets.some(p=>p.examPartId==='jafp-practical'));assert(!f.calls.some(c=>c.key.endsWith('/fp2/manifest.json')));
});
test('本当に存在しない科目は再取得を繰り返さず、選び直せる',async t=>{
 const f=await fixture(t),c=await loadCatalog('fp2',{requestedPartId:'not-published'});
 assert.equal(c.choose,true);assert.equal(c.invalidTarget,true);
 for(const key of [url('data/qualifications/catalog.json'),url('data/qualifications/fp2/manifest.json')])assert.equal(f.calls.filter(c=>c.key===key).length,2);
 assert(!f.calls.some(c=>c.key.includes('/packs/')));
});
