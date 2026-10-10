import {test} from 'node:test';
import assert from 'node:assert/strict';
import {visibleCardEvents,validateCardDocument} from '../src/domain/card-sync.js';
const event=id=>({id,cardId:'one',cardVersion:1,outcome:'again',at:'2026-10-10T00:00:00.000Z'});
const doc=(kind,payload)=>({id:`${kind}--${payload.id}`,kind,payload});
const rating=id=>doc('rating',event(id));
test('削除は観測済み評価だけを消し、順序・端末時刻によらずオフライン評価を残す',()=>{
 const rows=[rating('old'),rating('offline'),doc('reset',{id:'delete',eventIds:['old']})];
 assert.deepEqual(visibleCardEvents(rows).map(e=>e.id),['offline']);assert.deepEqual(visibleCardEvents(rows.toReversed()).map(e=>e.id),['offline']);
});
test('明示復元は観測した削除だけを取り消し、後の削除を無効にしない',()=>{
 const rows=[rating('old'),doc('reset',{id:'d1',eventIds:['old']}),doc('restore',{id:'r1',eventIds:['old'],resetIds:['d1']})];
 assert.equal(visibleCardEvents(rows).length,1);rows.push(doc('reset',{id:'d2',eventIds:['old']}));assert.equal(visibleCardEvents(rows).length,0);
 rows.push(doc('restore',{id:'r2',eventIds:['old'],resetIds:['d2']}));assert.equal(visibleCardEvents(rows.toReversed()).length,1);
});
test('未到着の評価・削除に先行して復元を受信しても同じ結果になる',()=>{
 const restore=doc('restore',{id:'r',eventIds:['e'],resetIds:['d']}),reset=doc('reset',{id:'d',eventIds:['e']});
 assert.deepEqual(visibleCardEvents([restore,reset]),[]);assert.deepEqual(visibleCardEvents([restore,reset,rating('e')]),[event('e')]);
});
test('削除・復元の件数境界・形式・同じIDの異なる評価を拒否する',()=>{
 for(const p of [{id:'d',eventIds:[]},{id:'d',eventIds:['e','e']},{id:'d',eventIds:Array.from({length:201},(_,i)=>`e${i}`)},{id:'d',eventIds:['bad/id']},{id:'d',eventIds:['e'],unexpected:1}])assert.throws(()=>validateCardDocument(doc('reset',p)));
 assert.throws(()=>validateCardDocument(doc('restore',{id:'r',eventIds:['e'],resetIds:[]})));
 assert.throws(()=>visibleCardEvents([rating('e'),doc('rating',{...event('e'),outcome:'recalled'})]));
 assert.doesNotThrow(()=>validateCardDocument(doc('reset',{id:'d',eventIds:Array.from({length:200},(_,i)=>`e${i}`)})));
});
