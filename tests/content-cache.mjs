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
 t.mock.method(globalThis,'fetch',async(input,options)=>{const key=String(input);calls.push({key,options});const body=overrides.get(key)??await readFile(new URL(key),'utf8');return body instanceof Response?body.clone():new Response(body);});
 const manifest=JSON.parse(await readFile(new URL(manifestURL),'utf8')),indexURL=new URL(manifest.index.url,manifestURL).href;
 return {saved,cache,overrides,calls,manifest,indexURL};
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
