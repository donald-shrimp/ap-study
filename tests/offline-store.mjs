import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createOfflineStore} from '../src/features/offline-store.js';
import {requiredQuestionAssets,requiredCaseAssets} from '../src/domain/offline-assets.js';
const sha=s=>createHash('sha256').update(s).digest('hex');
function fixture(){
 const data=new Map([['data/qualifications/q/index.json','index'],['data/qualifications/q/packs/a.json','pack'],['assets/choice.svg','choice'],['assets/other.svg','other']]);
 const files=Object.fromEntries([...data].map(([url,s])=>[url,{url,bytes:Buffer.byteLength(s),sha256:sha(s),...(url.includes('index')?{keep:true}:{})}]));
 const inventory={format:'hitomon-offline-inventory',version:1,qualificationId:'q',assets:files,groups:[{id:'a',revision:sha('a'),files:[...data.keys()].slice(0,3)},{id:'b',revision:sha('b'),files:['data/qualifications/q/index.json','assets/choice.svg','assets/other.svg']}]};
 const stores=new Map(),calls=[];
 const caches={open:async name=>{if(!stores.has(name))stores.set(name,new Map());const m=stores.get(name);return {match:async k=>m.get(String(k))?.clone(),put:async(k,r)=>{m.set(String(k),r.clone());},delete:async k=>m.delete(String(k))};}};
 let fail=null;
 const fetcher=async url=>{calls.push(url);if(fail)return fail(url);return new Response(data.get(new URL(url).pathname.slice(5)),{headers:{'Content-Type':'text/plain'}});};
 const create=()=>createOfflineStore({rootURL:'https://example.com/app/',inventory,cacheStorage:caches,fetcher});
 return {inventory,data,stores,caches,calls,create,setFail:f=>fail=f};
}
test('解くための画像だけを要求し、本文画像2問・選択肢画像・図中選択肢を保持',()=>{
 const q={stem:'文字の本文',sourceImages:['original'],image:'figure',choices:[{image:'choice'}]};assert.deepEqual(requiredQuestionAssets(q),['figure','choice']);assert.deepEqual(requiredQuestionAssets({...q,stem:''}),['original','figure','choice']);assert.deepEqual(requiredQuestionAssets({...q,choicePresentation:'codes'}),['figure']);assert.deepEqual(requiredCaseAssets({sourceImages:['original'],bodyFigures:[{image:'diagram'}]}),['diagram']);
});
test('完全な教材を保存・再検証し、再開では取得済みファイルを再転送しない',async()=>{
 const f=fixture(),m=f.create();await m.scan();await m.download(['a']);assert(m.status().get('a').saved);assert(!m.status().get('b').saved);const other=f.create();await other.scan();assert(other.status().get('a').saved);assert.equal(other.estimate(['a']),0);f.calls.length=0;await other.download(['a']);assert.equal(f.calls.length,0);
});
test('切断後に残りから再開でき、完了扱いにしない',async()=>{
 const f=fixture(),m=f.create();await m.scan();f.setFail(async()=>{throw Error('offline')});await assert.rejects(m.download(['a']));assert(!m.status().get('a').saved);f.setFail(null);await m.scan();await m.download(['a']);assert(m.status().get('a').saved);
});
test('中止・不正な本文・容量不足を成功扱いにしない',async()=>{
 const f=fixture(),m=f.create();await m.scan();const c=new AbortController();c.abort();await assert.rejects(m.download(['a'],{signal:c.signal}),{name:'AbortError'});f.setFail(async()=>new Response('wrong'));await assert.rejects(m.download(['a']),/確認に失敗/);assert(!m.status().get('a').saved);f.setFail(null);
 const realOpen=f.caches.open;f.caches.open=async n=>{const cache=await realOpen(n);return {...cache,put:async()=>{throw new DOMException('quota','QuotaExceededError')}}};await assert.rejects(m.download(['a']),{name:'QuotaExceededError'});await m.scan();assert(!m.status().get('a').saved);
});
test('教材削除でも共通データと他教材の選択肢画像を保持、実体消失を検出',async()=>{
 const f=fixture(),m=f.create();await m.scan();await m.download(['a','b']);await m.remove('a');assert(!m.status().get('a').saved);assert(m.status().get('b').saved);assert(f.stores.get('hitomon-/app/content').has('https://example.com/app/data/qualifications/q/index.json'));
 const images=await f.caches.open('hitomon-/app/images');await images.delete('https://example.com/app/assets/choice.svg');await m.scan();assert(!m.status().get('b').saved);
});
test('SHA改変・破損キャッシュを再取得し、ルート外のURLを拒否',async()=>{
 const f=fixture(),m=f.create();await m.scan();await m.download(['a']);const cache=await f.caches.open('hitomon-/app/images');await cache.put('https://example.com/app/assets/choice.svg',new Response('broken'));await m.scan();assert(!m.status().get('a').saved);f.calls.length=0;await m.download(['a']);assert.equal(f.calls.length,1);assert(m.status().get('a').saved);
 f.inventory.assets['assets/../../private']={url:'assets/../../private',sha256:sha('x'),bytes:1};assert.throws(f.create);
});
test('保存中の中止は完成済みファイルを残し、再開では残りだけ取得する',async()=>{
 const f=fixture(),m=f.create(),c=new AbortController();await m.scan();
 f.setFail(async url=>{if(!url.includes('index'))await new Promise(r=>setTimeout(r,30));return new Response(f.data.get(new URL(url).pathname.slice(5)));});
 await assert.rejects(m.download(['a'],{signal:c.signal,onProgress:({done})=>{if(done)c.abort();}}),{name:'AbortError'});await m.scan();assert(!m.status().get('a').saved);assert(m.status().get('a').partial===false);assert.equal(m.estimate(['a']),10);
 f.setFail(null);f.calls.length=0;await m.download(['a']);assert.equal(f.calls.length,2);assert(m.status().get('a').saved);
});
test('新版保存後も旧版の画像とパックを追跡し、削除時に共通keepと共有画像を残す',async()=>{
 const f=fixture(),old='assets/retired.svg',next='assets/new.svg',oldPack='data/qualifications/q/packs/a.json';
 f.data.set(old,'retired');f.inventory.assets[old]={url:old,bytes:7,sha256:sha('retired')};f.inventory.groups[0].files.push(old);
 await f.create().download(['a']);
 f.data.set(next,'new');f.inventory.assets[next]={url:next,bytes:3,sha256:sha('new')};delete f.inventory.assets[old];delete f.inventory.assets[oldPack];
 f.inventory.groups[0].files=f.inventory.groups[0].files.filter(k=>![old,oldPack].includes(k)).concat(next);f.inventory.groups[0].revision=sha('v2');
 const updated=f.create();await updated.download(['a']);await updated.remove('a');
 const images=f.stores.get('hitomon-/app/images'),content=f.stores.get('hitomon-/app/content');
 assert(!images.has('https://example.com/app/'+old));assert(!images.has('https://example.com/app/'+next));assert(!content.has('https://example.com/app/'+oldPack));
 assert(images.has('https://example.com/app/assets/choice.svg'));assert(content.has('https://example.com/app/data/qualifications/q/index.json'));
});
test('旧保存台帳からも廃止画像を削除し、保護情報のない共通データは保持する',async()=>{
 const f=fixture(),old='assets/legacy.svg';f.data.set(old,'legacy');f.inventory.assets[old]={url:old,bytes:6,sha256:sha('legacy')};f.inventory.groups[0].files.push(old);await f.create().download(['a']);
 const stateCache=await f.caches.open('hitomon-/app/offline-state'),key='https://example.com/app/offline-download-state.json',receipt=await(await stateCache.match(key)).json();delete receipt.groups['q/a'].keepFiles;receipt.groups['q/a'].files.push('../outside.svg','https://elsewhere.test/file.svg','assets/../../outside.svg','assets/x.svg?query');await stateCache.put(key,new Response(JSON.stringify(receipt)));
 delete f.inventory.assets[old];f.inventory.groups[0].files=f.inventory.groups[0].files.filter(k=>k!==old);
 const images=await f.caches.open('hitomon-/app/images');for(const url of ['https://example.com/outside.svg','https://elsewhere.test/file.svg','https://example.com/app/assets/x.svg?query'])await images.put(url,new Response('keep'));
 await f.create().remove('a');assert(!f.stores.get('hitomon-/app/images').has('https://example.com/app/'+old));for(const url of ['https://example.com/outside.svg','https://elsewhere.test/file.svg','https://example.com/app/assets/x.svg?query'])assert(await images.match(url));
 assert(f.stores.get('hitomon-/app/content').has('https://example.com/app/data/qualifications/q/index.json'));
});
test('別資格の保存台帳が使う廃止画像は、その資格の削除まで保持する',async()=>{
 const f=fixture(),old='assets/shared-retired.svg';f.data.set(old,'shared');f.inventory.assets[old]={url:old,bytes:6,sha256:sha('shared')};f.inventory.groups[0].files.push(old);await f.create().download(['a']);
 const otherInventory={...structuredClone(f.inventory),qualificationId:'other'},other=createOfflineStore({rootURL:'https://example.com/app/',inventory:otherInventory,cacheStorage:f.caches,fetcher:async url=>new Response(f.data.get(new URL(url).pathname.slice(5)))});await other.download(['a']);
 delete f.inventory.assets[old];f.inventory.groups[0].files=f.inventory.groups[0].files.filter(k=>k!==old);await f.create().remove('a');assert(f.stores.get('hitomon-/app/images').has('https://example.com/app/'+old));await other.remove('a');assert(!f.stores.get('hitomon-/app/images').has('https://example.com/app/'+old));
});
