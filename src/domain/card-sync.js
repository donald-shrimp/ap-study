import {validateCardEvents} from './flashcards.js';
const validId=v=>typeof v==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(v);
const ids=v=>Array.isArray(v)&&v.length>0&&v.length<=200&&new Set(v).size===v.length&&v.every(validId);
export const cardDocumentId=(kind,id)=>`${kind}--${id}`;
export const sameCardPayload=(a,b)=>JSON.stringify(a,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v)===JSON.stringify(b,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
export function validateCardDocument(row){
 const p=row?.payload;
 if(!p||!['rating','reset','restore'].includes(row.kind)||!validId(p.id)||row.id!==cardDocumentId(row.kind,p.id))throw new Error('単語帳の同期記録が正しくありません。');
 if(row.kind==='rating')validateCardEvents([p]);
 else if(Object.keys(p).some(k=>!(row.kind==='reset'?['id','eventIds']:['id','eventIds','resetIds']).includes(k))||!ids(p.eventIds)||row.kind==='restore'&&!ids(p.resetIds))throw new Error('単語帳の削除・復元記録が正しくありません。');
 return row;
}
// A reset only removes observed event IDs. A restore only cancels observed
// reset IDs: late/offline ratings survive, and later deletions remain effective.
export function visibleCardEvents(rows){
 const ratings=new Map(),removed=new Map(),restored=new Map();
 for(const row of rows){validateCardDocument(row);const p=row.payload;
  if(row.kind==='rating'){if(ratings.has(p.id)&&!sameCardPayload(ratings.get(p.id),p))throw new Error('同じIDの異なる単語帳記録があります。');ratings.set(p.id,p);}
  if(row.kind==='reset')for(const id of p.eventIds){if(!removed.has(id))removed.set(id,new Set());removed.get(id).add(p.id);}
  if(row.kind==='restore')for(const id of p.eventIds){if(!restored.has(id))restored.set(id,new Set());for(const reset of p.resetIds)restored.get(id).add(reset);}
 }
 return validateCardEvents([...ratings.values()].filter(e=>![...(removed.get(e.id)||[])].some(reset=>!restored.get(e.id)?.has(reset))).sort((a,b)=>a.at.localeCompare(b.at)||a.id.localeCompare(b.id)));
}
