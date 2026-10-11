const id=v=>typeof v==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(v);
const keys=(v,allowed)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).every(k=>allowed.includes(k));
export function validateCheckpoint(cp,qualification){
 if(cp===null)return cp;
 if(!keys(cp,['cardId','cardVersion','flipped','seen','recent','topicId'])||!id(cp.cardId)||!Number.isInteger(cp.cardVersion)||cp.cardVersion<1||typeof cp.flipped!=='boolean'||!Array.isArray(cp.seen)||cp.seen.length>10000||new Set(cp.seen).size!==cp.seen.length||!cp.seen.every(id)||!Array.isArray(cp.recent)||cp.recent.length>10||!cp.recent.every(id)||cp.topicId!==null&&!qualification.topics.some(t=>t.id===cp.topicId))throw new Error('単語帳の再開位置を確認できません。');return cp;
}
export function validatePersonal(kind,p,qualification){
 if(kind==='note'||kind==='draft'){
  if(!keys(p,kind==='draft'?['topicId','text','baseRevision']:['topicId','text'])||!qualification.topics.some(t=>t.id===p.topicId)||typeof p.text!=='string'||p.text.length>200||kind==='draft'&&(!Number.isInteger(p.baseRevision)||p.baseRevision<0))throw new Error('分野メモの形式が正しくありません。');
 }else if(kind==='checkpoint'){
  if(!keys(p,['deviceId','checkpoint','at'])||!id(p.deviceId)||typeof p.at!=='string'||Number.isNaN(Date.parse(p.at))||new Date(p.at).toISOString()!==p.at)throw new Error('端末の再開情報を確認できません。');validateCheckpoint(p.checkpoint,qualification);
 }else throw new Error('未対応の個人設定です。');return p;
}
export const personalId=(kind,p)=>`${kind}--${kind==='checkpoint'?p.deviceId:p.topicId}`;
export function checkpointAvailable(cp,deck){
 const card=deck.cards.find(c=>c.id===cp?.cardId);return !!card&&card.version===cp.cardVersion&&(!cp.topicId||card.topicId===cp.topicId)&&[...cp.seen,...cp.recent].every(id=>deck.cards.some(c=>c.id===id));
}
