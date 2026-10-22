import {esc} from '../utils.js';
import {createOfflineStore} from './offline-store.js';
const amount=n=>n<1000000?`${Math.ceil(n/1000)} KB`:`${(n/1000000).toFixed(1)} MB`;
async function workerReady(){
 const registration=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('アプリのオフライン準備が完了していません。接続中に更新してからお試しください。')),10000);navigator.serviceWorker.ready.then(r=>{clearTimeout(timer);resolve(r);},e=>{clearTimeout(timer);reject(e);});});
 const worker=navigator.serviceWorker.controller||registration.active;
 const ok=await new Promise(resolve=>{const channel=new MessageChannel(),timer=setTimeout(()=>{channel.port1.close();resolve(false);},800);channel.port1.onmessage=e=>{clearTimeout(timer);channel.port1.close();resolve(e.data?.offlineProtocol===1);};worker?.postMessage({type:'OFFLINE_READY'},[channel.port2]);});
 if(!ok)throw Error('先に設定の「更新して再読み込み」でアプリを更新してください。');
}
export async function openOffline({content,qualification,partId,rootURL,onChanged,getOnline=()=>navigator.onLine}){
 document.getElementById('offline-dialog')?.remove();const d=document.createElement('dialog');d.id='offline-dialog';d.className='offline-dialog';d.setAttribute('aria-labelledby','offline-title');document.body.append(d);
 let controller,busy=false,model,groups=[],selected=new Set(),statuses=new Map();
 d.innerHTML='<div class="dialog-head"><h2 id="offline-title">オフライン学習用に保存</h2><button class="button secondary" data-offline-close>閉じる</button></div><p role="status">教材と保存状況を確認しています…</p>';d.showModal();
 const close=()=>{controller?.abort();d.close();};d.addEventListener('cancel',()=>controller?.abort());d.addEventListener('click',e=>{if(e.target.closest('[data-offline-close]'))close();});
 function message(text){const el=d.querySelector('#offline-message');if(el)el.textContent=text;}
 function controls(){
  for(const input of d.querySelectorAll('[data-offline-group]'))input.disabled=busy;
  for(const b of d.querySelectorAll('[data-offline-select],[data-offline-remove]'))b.disabled=busy;
  const button=d.querySelector('[data-offline-save]');button.disabled=busy||!selected.size||(!getOnline()&&model.estimate([...selected])>0);d.querySelector('[data-offline-cancel]').hidden=!busy;
  const bytes=model.estimate([...selected]);d.querySelector('#offline-total').textContent=`追加保存の目安：${amount(bytes)}（共通データを含む）`;
 }
 function refresh(){
  for(const g of groups){const s=statuses.get(g.id),row=d.querySelector(`[data-offline-row="${CSS.escape(g.id)}"]`);row.querySelector('.offline-status').textContent=s.saved?'保存済み':s.update?'更新あり':s.partial?'途中まで保存':'未保存';row.querySelector('.offline-size').textContent=`追加 ${amount(s.bytes)}`;row.querySelector('[data-offline-remove]').hidden=!s.saved&&!s.partial&&!s.update;}
  controls();
 }
 async function run(){
  if(busy)return;busy=true;controller=new AbortController();controls();message('保存を準備しています…');
  try{
   await workerReady();if(controller.signal.aborted)throw new DOMException('中止','AbortError');
   const additional=model.estimate([...selected]);if(additional&&!getOnline())throw Error('まだ保存されていない教材があります。接続後に再開してください。');
   const storage=await navigator.storage?.estimate?.();if(additional&&storage?.quota&&storage.quota-storage.usage<additional*1.1+100000)throw Error('端末の空き容量が足りません。不要な教材を削除してから再開してください。');
   navigator.storage?.persist?.().catch(()=>{});
   statuses=await model.download([...selected],{signal:controller.signal,onProgress:({done,total})=>{const p=d.querySelector('progress');p.max=Math.max(total,1);p.value=total?done:1;message(`保存中 ${amount(done)} / ${amount(total)}`);}});
   refresh();message('保存できました。');await onChanged();
  }catch(e){message(e.name==='AbortError'?'保存を中止しました。保存できた分から再開できます。':e.name==='QuotaExceededError'?'端末の空き容量が足りません。不要な教材を削除して再開してください。':e.name==='TypeError'?'通信または保存を完了できませんでした。接続を確認して再開してください。':e.message);}
  finally{try{statuses=await model.scan();await onChanged();}catch{}busy=false;refresh();}
 }
 try{
  if(!globalThis.caches||!navigator.serviceWorker)throw Error('このブラウザでは教材を保存できません。');
  const inventory=await content.loadOffline();if(inventory.qualificationId!==qualification.id)throw Error('教材の資格が一致しません。');
  groups=inventory.groups.filter(g=>g.examPartId===partId);model=createOfflineStore({rootURL,inventory});statuses=await model.scan();selected=new Set(groups.filter(g=>!statuses.get(g.id).saved).map(g=>g.id));
  d.innerHTML=`<div class="dialog-head"><h2 id="offline-title">オフライン学習用に保存</h2><button class="button secondary" data-offline-close>閉じる</button></div><details class="offline-info"><summary>保存対象</summary><p>問題文・解説・図・選択肢画像。原本画像・外部資料・新しい診断／模試の準備は対象外。</p></details><div class="button-row"><button class="button secondary" data-offline-select="all">すべて選択</button><button class="button secondary" data-offline-select="none">選択を解除</button></div><div class="offline-list">${groups.map(g=>`<section class="offline-row" data-offline-row="${esc(g.id)}"><label><input type="checkbox" data-offline-group="${esc(g.id)}" ${selected.has(g.id)?'checked':''}><span><strong>${esc(g.label)}</strong><span class="small">${g.count}${g.unit==='cases'?'大問':g.unit==='cards'?'枚':'問'} · <span class="offline-size"></span></span><span class="badge offline-status"></span></span></label><button class="button quiet" data-offline-remove="${esc(g.id)}">保存を削除</button></section>`).join('')}</div><p id="offline-total"></p><progress max="1" value="0" aria-label="教材の保存進捗"></progress><p id="offline-message" role="status" aria-live="polite"></p><div class="button-row"><button class="button primary" data-offline-save>選んだ教材を保存</button><button class="button secondary" data-offline-cancel hidden>保存を中止</button></div>`;
  d.addEventListener('change',e=>{const id=e.target.dataset.offlineGroup;if(id){e.target.checked?selected.add(id):selected.delete(id);controls();}});
  d.addEventListener('click',async e=>{
   const el=e.target.closest('[data-offline-save],[data-offline-cancel],[data-offline-select],[data-offline-remove]');if(!el)return;
   if(el.hasAttribute('data-offline-save'))return run();
   if(el.hasAttribute('data-offline-cancel'))return controller?.abort();
   if(busy)return;
   if(el.hasAttribute('data-offline-select')){selected=el.dataset.offlineSelect==='all'?new Set(groups.map(g=>g.id)):new Set();for(const input of d.querySelectorAll('[data-offline-group]'))input.checked=selected.has(input.dataset.offlineGroup);controls();}
   if(el.dataset.offlineRemove){busy=true;controls();try{statuses=await model.remove(el.dataset.offlineRemove);message('削除しました。');await onChanged();}catch(e){message(e.message);}finally{busy=false;refresh();}}
  });refresh();
 }catch(e){d.innerHTML=`<div class="dialog-head"><h2 id="offline-title">オフライン学習用に保存</h2><button class="button secondary" data-offline-close>閉じる</button></div><p role="status">${esc(e.message)}</p><p>接続中にアプリを更新してから、もう一度開いてください。</p>`;}
}
