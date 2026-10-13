export const syncLabels={local:'端末の保存',study:'回答・ヒント',planning:'計画・診断・模試',learning:'出題の設定',cards:'単語帳',personal:'メモ・再開位置'};
const failed=new Set(['error','blocked','rules','mock-rules','history-rules','extended-rules']);
export function summarizeSync(states,signedIn){
 const special={'mock-rules':'模試','history-rules':'計画の履歴','extended-rules':'模試・計画の履歴'};
 const entries=Object.entries(states).map(([scope,state])=>({scope,label:special[state.kind]||syncLabels[scope],...state}));
 const failures=entries.filter(e=>failed.has(e.kind)),conflicts=entries.filter(e=>e.kind==='conflict');
 if(failures.some(e=>e.scope==='local'))return {kind:'error',text:'記録を保存できません。書き出して保管してください。',details:[...failures,...conflicts]};
 if(failures.length)return {kind:'error',text:signedIn?'一部の記録を同期できません。記録はこの端末に残っています。':'記録の保存を確認してください。',details:[...failures,...conflicts]};
 if(conflicts.length)return {kind:'conflict',text:'別端末の変更と重なっています。使う内容を選んでください。',details:conflicts};
 if(!signedIn)return {kind:'guest',text:'ログインすると、別の端末でも続けられます。',details:[]};
 if(entries.length&&entries.every(e=>e.kind==='synced'))return {kind:'synced',text:'同期済み',details:[]};
 if(entries.some(e=>e.kind==='offline'))return {kind:'offline',text:'オフライン · 接続後に同期します',details:[]};
 const syncing=entries.some(e=>e.kind==='syncing');
 return {kind:syncing?'syncing':'pending',text:syncing?'同期中…':'同期待ち',details:[]};
}
