import {test} from 'node:test';
import assert from 'node:assert/strict';
import {validatePersonal,checkpointAvailable,personalId} from '../src/domain/personal.js';
const qualification={topics:[{id:'network'},{id:'database'}]},cp={cardId:'one',cardVersion:2,flipped:true,seen:['one'],recent:['one'],topicId:'network'};
test('メモ・端末別位置は資格の分野と限定形式を検証する',()=>{
 assert.deepEqual(validatePersonal('note',{topicId:'network',text:''},qualification),{topicId:'network',text:''});
 validatePersonal('checkpoint',{deviceId:'phone',checkpoint:cp,at:'2026-10-11T01:00:00.000Z'},qualification);
 validatePersonal('checkpoint',{deviceId:'phone',checkpoint:null,at:'2026-10-11T01:00:00.000Z'},qualification);
 assert.equal(personalId('checkpoint',{deviceId:'phone'}),'checkpoint--phone');
 for(const p of [{topicId:'other',text:'x'},{topicId:'network',text:'x'.repeat(201)},{topicId:'network',text:'x',unexpected:true}])assert.throws(()=>validatePersonal('note',p,qualification));
 for(const delta of [{flipped:1},{cardVersion:0},{recent:Array(11).fill('one')},{seen:['one','one']},{topicId:'other'},{unexpected:true}])assert.throws(()=>validatePersonal('checkpoint',{deviceId:'phone',checkpoint:{...cp,...delta},at:'2026-10-11T01:00:00.000Z'},qualification));
 assert.throws(()=>validatePersonal('draft',{topicId:'network',text:'x',baseRevision:-1},qualification));
});
test('他端末の再開はカード版・分野・履歴の参照が現教材で使える場合だけ提供する',()=>{
 const deck={cards:[{id:'one',version:2,topicId:'network'}]};
 assert.equal(checkpointAvailable(cp,deck),true);
 for(const delta of [{cardVersion:1},{cardId:'missing'},{topicId:'database'},{seen:['missing']},{recent:['missing']}])assert.equal(checkpointAvailable({...cp,...delta},deck),false);
});
