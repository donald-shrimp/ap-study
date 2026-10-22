const digest=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');
export function createOfflineStore({rootURL,inventory,cacheStorage=globalThis.caches,fetcher=globalThis.fetch}){
 const root=new URL(rootURL),prefix=`hitomon-${root.pathname}`,groups=new Map(),assets=new Map();
 if(inventory?.format!=='hitomon-offline-inventory'||inventory.version!==1||!Array.isArray(inventory.groups)||!inventory.assets||inventory.groups.length>1000)throw Error('保存用の教材一覧を確認できません。');
 for(const [key,a] of Object.entries(inventory.assets)){
  const url=new URL(key,root);
  if(a.url!==key||!/^(assets\/|data\/qualifications\/)/.test(key)||url.origin!==root.origin||!url.pathname.startsWith(root.pathname)||!/^(assets\/|data\/qualifications\/)/.test(url.pathname.slice(root.pathname.length))||!Number.isSafeInteger(a.bytes)||a.bytes<0||!/^[a-f0-9]{64}$/.test(a.sha256))throw Error('保存用ファイルを確認できません。');
  assets.set(key,{...a,href:url.href});
 }
 for(const g of inventory.groups){if(groups.has(g.id)||!Array.isArray(g.files)||!g.files.every(k=>assets.has(k))||!/^[a-f0-9]{64}$/.test(g.revision))throw Error('教材の保存範囲を確認できません。');groups.set(g.id,g);}
 const cacheName=a=>prefix+(a.url.startsWith('assets/')?'images':'content');
 const stateKey=new URL('offline-download-state.json',root).href;
 const stateCache=()=>cacheStorage.open(prefix+'offline-state');
 let state={version:1,groups:{}},valid=new Set();
 const key=id=>inventory.qualificationId+'/'+id;
 const union=ids=>[...new Set(ids.flatMap(id=>{if(!groups.has(id))throw Error('教材が見つかりません。');return groups.get(id).files;}))];
 async function loadState(){try{const r=await(await stateCache()).match(stateKey);if(r){const s=await r.json();if(s.version===1&&s.groups&&typeof s.groups==='object'&&!Array.isArray(s.groups))state=s;}}catch{state={version:1,groups:{}};}}
 async function saveState(){await(await stateCache()).put(stateKey,new Response(JSON.stringify(state),{headers:{'Content-Type':'application/json'}}));}
 async function scan(ids=[...groups.keys()]){
  valid=new Set();const files=union(ids),pending=[...files];
  await Promise.all(Array.from({length:4},async()=>{while(pending.length){const k=pending.shift(),a=assets.get(k),r=await(await cacheStorage.open(cacheName(a))).match(a.href);if(!r?.ok)continue;const data=await r.arrayBuffer();if(data.byteLength===a.bytes&&await digest(data)===a.sha256)valid.add(k);}}));
  await loadState();return status();
 }
 function status(){return new Map([...groups].map(([id,g])=>{const missing=g.files.filter(k=>!valid.has(k)),prior=state.groups[key(id)];return [id,{saved:missing.length===0,partial:g.files.some(k=>!assets.get(k).keep&&valid.has(k)),update:!!prior&&prior.revision!==g.revision,missing:missing.length,total:g.files.length,bytes:missing.reduce((n,k)=>n+assets.get(k).bytes,0)}];}));}
 function estimate(ids){return union(ids).filter(k=>!valid.has(k)).reduce((n,k)=>n+assets.get(k).bytes,0);}
 async function download(ids,{signal,onProgress=()=>{}}={}){
  await scan();
  const files=union(ids),pending=files.filter(k=>!valid.has(k)),total=pending.reduce((n,k)=>n+assets.get(k).bytes,0);let done=0,firstError;
  const abort=()=>{if(signal?.aborted)throw new DOMException('保存を中止しました。','AbortError');};
  onProgress({done,total});
  await Promise.all(Array.from({length:3},async()=>{while(pending.length&&!firstError){try{
   abort();const k=pending.shift(),a=assets.get(k),cache=await cacheStorage.open(cacheName(a)),r=await fetcher(a.href,{cache:'reload',signal});
   if(!r.ok)throw Error('教材を取得できません。接続を確認して再開してください。');
   const bytes=await r.arrayBuffer();if(bytes.byteLength!==a.bytes||await digest(bytes)!==a.sha256){await cache.delete(a.href);throw Error('教材の確認に失敗しました。もう一度保存してください。');}
   abort();await cache.put(a.href,new Response(bytes,{headers:{'Content-Type':r.headers.get('Content-Type')||'application/octet-stream'}}));valid.add(k);done+=a.bytes;onProgress({done,total});
  }catch(e){firstError||=e;}}}));
  if(firstError)throw firstError;abort();await scan();
  if(ids.some(id=>!status().get(id).saved))throw Error('保存が不足しています。接続後に再開してください。');
  for(const id of ids){const g=groups.get(id);state.groups[key(id)]={revision:g.revision,files:g.files,savedAt:new Date().toISOString()};}
  await saveState();return status();
 }
 async function remove(id){
  const g=groups.get(id);if(!g)throw Error('教材が見つかりません。');await loadState();
  const protect=new Set([...groups.values()].filter(x=>x.id!==id).flatMap(x=>x.files));
  for(const [k,v] of Object.entries(state.groups))if(k!==key(id))for(const f of v.files||[])protect.add(f);
  const previous=state.groups[key(id)]?.files||[];
  for(const k of new Set([...g.files,...previous])){const a=assets.get(k);if(!a||a.keep||protect.has(k))continue;await(await cacheStorage.open(cacheName(a))).delete(a.href);valid.delete(k);}
  delete state.groups[key(id)];await saveState();return status();
 }
 return {scan,status,estimate,download,remove};
}
