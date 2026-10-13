import {setSyncStatus} from '../ui/sync-status.js';
import {createWorkspaceStore} from '../storage/workspace.js';
import {validatePersonal,personalId} from '../domain/personal.js';
import {esc,now} from '../utils.js';
export function createPersonalFeature({qualification,rootPath,getStore,getState,onChanged,onNotice,onApplied,onCheckpoints}){
 let workspace,rows=[],identity,generation=0,queue=Promise.resolve(),status='guest';const editing=new Map(),unsaved=new Set();
 const row=id=>rows.find(r=>r.id===id);
 function show(kind,error){if(kind==='synced'&&rows.some(r=>r.kind==='draft'))kind=rows.some(r=>r.kind==='draft'&&r.payload.baseRevision!==(row('note--'+r.payload.topicId)?.localRevision||0))?'conflict':'pending';status=kind;setSyncStatus('personal',kind,error);}

 function projected(){const state=getState();let changed=false;for(const r of rows.filter(r=>r.kind==='note')){if(editing.has(r.payload.topicId)||unsaved.has(r.payload.topicId)||row('draft--'+r.payload.topicId))continue;if(state.readingNotes[r.payload.topicId]!==r.payload.text){state.readingNotes[r.payload.topicId]=r.payload.text;changed=true;}}return changed;}
 function conflictsHtml(topicId){const r=row('note--'+topicId),d=row('draft--'+topicId);if(!r?.conflict&&(!d||d.payload.baseRevision===(r?.localRevision||0)))return '';const remote=r?.conflict?.payload.text??r?.payload.text??'';return `<p class="small">別端末のメモ：${esc(remote||'（空欄）')}</p><div class="button-row"><button class="button secondary" data-action="note-local" data-topic-id="${esc(topicId)}">この端末のメモを使う</button><button class="button secondary" data-action="note-remote" data-topic-id="${esc(topicId)}">別端末のメモを使う</button></div>`;}
 function refreshControls(){for(const t of qualification.topics){const box=document.getElementById('note-conflict-'+t.id);if(box){const html=conflictsHtml(t.id);if(box.innerHTML!==html&&!box.contains(document.activeElement))box.innerHTML=html;}}onCheckpoints?.();}
 async function bind(){await queue.catch(()=>{});const token=++generation;await workspace?.close();identity=await getStore().identity();if(token!==generation)return;workspace=createWorkspaceStore({...identity,rootPath,namespaceName:'personal',validate:(k,p)=>validatePersonal(k,p,qualification)});rows=await workspace.read();editing.clear();unsaved.clear();
  // Preserve existing local notes. New accounts never inherit guest notes.
  for(const t of qualification.topics){const text=getState().readingNotes[t.id]??getState().readingNotes[t.name];if(typeof text==='string'&&!row('note--'+t.id))rows.push(await workspace.write('note','note--'+t.id,{topicId:t.id,text},0));}
  for(const r of rows.filter(r=>r.kind==='draft')){getState().readingNotes[r.payload.topicId]=r.payload.text;const note=row('note--'+r.payload.topicId);if(!note?.conflict&&r.payload.baseRevision===(note?.localRevision||0)){await workspace.write('note','note--'+r.payload.topicId,{topicId:r.payload.topicId,text:r.payload.text},r.payload.baseRevision);await workspace.removeDraft(r.id);}}rows=await workspace.read();projected();show(identity.owner.startsWith('uid:')?navigator.onLine?'pending':'offline':'guest');
 }
 async function accept(next){const token=generation;if(next.some(r=>r.owner!==identity.owner||r.qualificationId!==qualification.id))return;rows=next;show(status);const changed=projected();if(token!==generation)return;if(changed)onApplied();refreshControls();}
 function focus(topicId){if(!editing.has(topicId))editing.set(topicId,row('draft--'+topicId)?.payload.baseRevision??row('note--'+topicId)?.localRevision??0);}
 function edit(topicId,text){if(!qualification.topics.some(t=>t.id===topicId))return;const token=generation,target=workspace;unsaved.add(topicId);
  focus(topicId);
  const operation=queue.catch(()=>{}).then(async()=>{if(token!==generation||target!==workspace)return;const base=editing.get(topicId);await target.write('draft','draft--'+topicId,{topicId,text,baseRevision:base});rows=await target.read();const current=row('note--'+topicId);
   if(current?.conflict||(current?.localRevision||0)!==base){refreshControls();show('conflict');return;}
   try{const saved=await target.write('note','note--'+topicId,{topicId,text},base);editing.set(topicId,saved.localRevision);await target.removeDraft('draft--'+topicId);unsaved.delete(topicId);rows=await target.read();if(token===generation){show(identity.owner.startsWith('uid:')?navigator.onLine?'pending':'offline':'guest');onChanged();refreshControls();}}catch(error){rows=await target.read();refreshControls();show('conflict');onNotice(error.message);}
  });queue=operation;operation.catch(error=>{if(token===generation)onNotice('メモはこの端末に残っています。'+error.message);});return operation;
 }
 async function blur(topicId){const token=generation;await queue.catch(()=>{});if(token!==generation)return;editing.delete(topicId);if(projected())onApplied();}
 async function action(el){if(!['note-local','note-remote'].includes(el.dataset.action))return false;const topicId=el.dataset.topicId,token=generation,target=workspace;if(!qualification.topics.some(t=>t.id===topicId))return true;await queue.catch(()=>{});if(token!==generation)return true;
  let current=row('note--'+topicId),draft=row('draft--'+topicId);if(current?.conflict){await target.resolve(current.id,el.dataset.action==='note-local');if(token!==generation)return true;rows=await target.read();current=row(current.id);}
  if(el.dataset.action==='note-local'){const text=draft?.payload.text??getState().readingNotes[topicId]??current?.payload.text??'';await target.write('note','note--'+topicId,{topicId,text},current?.localRevision||0);}if(token!==generation)return true;await target.removeDraft('draft--'+topicId);editing.delete(topicId);unsaved.delete(topicId);rows=await target.read();if(token===generation){projected();onChanged();onApplied();const box=document.getElementById('note-conflict-'+topicId);if(box)box.innerHTML=conflictsHtml(topicId);refreshControls();}return true;
 }
 async function saveCheckpoint(checkpoint){const token=generation,target=workspace,id=personalId('checkpoint',identity),fresh=await target.read(),old=fresh.find(r=>r.id===id);if(token!==generation)return;
  if(old?.conflict)await target.resolve(id,false);if(token!==generation)return;const current=(await target.read()).find(r=>r.id===id);if(token!==generation)return;await target.write('checkpoint',id,{deviceId:identity.deviceId,checkpoint,at:now()},current?.localRevision||0);if(token===generation){rows=await target.read();show(identity.owner.startsWith('uid:')?navigator.onLine?'pending':'offline':'guest');onChanged();}
 }
 async function importNotes(notes,{keepExisting=false}={}){
  await queue.catch(()=>{});const token=generation,target=workspace;
  const items=qualification.topics.filter(t=>!keepExisting||typeof(notes[t.id]??notes[t.name])==='string').map(t=>({topicId:t.id,text:notes[t.id]??notes[t.name]??''}));
  await target.writeNotes(items,{keepExisting});if(token!==generation)return;rows=await target.read();editing.clear();unsaved.clear();projected();onChanged();refreshControls();
 }
 const checkpoints=()=>rows.filter(r=>r.kind==='checkpoint'&&r.payload.deviceId!==identity?.deviceId&&r.payload.checkpoint&&!r.conflict).sort((a,b)=>b.payload.at.localeCompare(a.payload.at));
 const syncStore=()=>workspace?{identity:workspace.identity,read:async()=>(await workspace.read()).filter(r=>r.kind!=='draft'),merge:async remote=>{if(remote.id!==personalId(remote.kind,remote.payload)||remote.kind==='draft')throw new Error('個人設定の同期IDが一致しません。');return workspace.merge(remote);},acknowledge:workspace.acknowledge}:null;
 return {focus,importNotes,bind,edit,blur,action,saveCheckpoint,checkpoints,conflictsHtml,flush:async()=>{await queue;await workspace?.flush();},syncStore,onRows:async()=>{const token=generation,target=workspace;try{const next=await target.read();if(token===generation)await accept(next);}catch(error){if(token===generation){show('error');onNotice(error.message);}}},onStatus:show};
}
