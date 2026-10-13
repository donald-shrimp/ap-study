import {esc} from '../utils.js';
import {summarizeSync,syncLabels} from '../domain/sync-status.js';

let signedIn=false,enabled=new Set(),states={};
function render(){
 const active=Object.fromEntries(Object.entries(states).filter(([key])=>!signedIn||enabled.has(key))),summary=summarizeSync(active,signedIn);
 const el=document.getElementById('sync-state');
 if(el){el.textContent=summary.text;el.dataset.status=summary.kind;for(const scope of Object.keys(syncLabels))el.dataset[scope]=active[scope]?.kind||'';}
 const foot=document.getElementById('cloud-state');if(foot){foot.hidden=!signedIn;foot.textContent=summary.kind==='error'?'同期を確認してください':summary.text;}
 const details=document.getElementById('sync-details');
 if(details){details.hidden=!summary.details.length;details.innerHTML=summary.details.map(s=>`<p><strong>${esc(s.label)}</strong>：${s.kind==='conflict'?'変更が重なっています。':s.scope==='local'?'保存できません。':'同期できません。'}${s.kind==='conflict'?'<span class="small">該当画面で使う内容を選んでください。</span>':''}</p>`).join('');}
 const technical=document.getElementById('sync-technical');
 if(technical){technical.hidden=summary.kind!=='error';const out=technical.querySelector('pre');if(out)out.textContent=summary.details.map(s=>`${s.label}: ${s.kind}${s.error?`\n${s.error}`:''}`).join('\n\n');}
}
export function setSyncAccount(value,scopes=[]){const local=states.local||{kind:'synced'};signedIn=value;enabled=new Set(['local',...scopes]);states={local,...Object.fromEntries(scopes.map(scope=>[scope,{kind:value?'pending':'guest'}]))};render();}
export function setSyncStatus(scope,kind,error){states[scope]={kind,error:error?`${error.code||error.name||''}: ${error.message||error}`:null};render();}
export function workspaceStatusHTML(kind){
 const failed=['rules','mock-rules','history-rules','extended-rules','error'].includes(kind);
 const text=kind==='conflict'?'計画などの変更が重なっています。使う内容を選んでください。':failed?'計画などを同期できません。「表示・データ」で確認してください。':'';
 return `<div class="workspace-status" ${text?'':'hidden'}><p class="small" role="status">${esc(text)}</p></div>`;
}
