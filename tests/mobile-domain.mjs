import test from 'node:test';
import assert from 'node:assert/strict';
import {allowsQuestion} from '../src/domain/study-context.js';
import {nextCard,cardProgress,validateCardEvents,validateDeck} from '../src/domain/flashcards.js';
import {chooseNextAction} from '../src/domain/next-action.js';
const classification={items:[{questionId:'read',mode:'paperless'},{questionId:'write',mode:'desk'}]},questions=['read','write','unknown'].map(id=>({id,topicId:id==='read'?'terms':'math',examPartId:'a'}));
const qualification={id:'ap',defaultExamPartId:'a',examParts:[{id:'a',label:'選択式',practiceAvailable:true}],topics:[{id:'terms'},{id:'math'}]};
const allowed=q=>allowsQuestion(q,'paperless',classification,[]);
const choose=opts=>chooseNextAction({qualification,questions,attempts:[],reviewInfo:()=>null,practiceAllowed:allowed,paperless:true,...opts});
test('未確認・筆算問題を紙なしへ混ぜず、本人の机指定を優先する',()=>{assert.deepEqual(questions.map(allowed),[true,false,false]);assert.equal(allowsQuestion(questions[0],'paperless',classification,['read']),false);assert.equal(allowsQuestion(questions[2],'all',null,[]),true);assert.equal(allowsQuestion(questions[0],'paperless',null,[]),false);});
test('紙なしで新しい筆算の中断を飛ばしても、古い適合する中断を再開できる',()=>{const a=id=>({id,questionId:id,status:'postponed',hintCount:1,selected:null,startedAt:'2026-10-01',updatedAt:id==='read'?'2026-10-01':'2026-10-02'});assert.equal(choose({attempts:[a('read'),a('write')]}).attemptId,'read');assert.equal(choose({attempts:[a('write')]}).questionId,'read');});
test('オフラインで紙なしが0問なら未確認・筆算へフォールバックしない',()=>{assert.equal(choose({available:q=>q.id!=='read',online:false}).kind,'unavailable');});
const cards=['one','two','three'].map(id=>({id,version:1,topicId:'terms',front:id,back:'意味',sourceNote:'公式問題',relatedQuestionIds:['read']}));
const event=(cardId,outcome='again',cardVersion=1)=>({id:cardId,cardId,cardVersion,outcome,at:'2026-10-07T01:00:00.000Z'});
test('単語帳は自己評価をカード版ごとに数え、新版を未確認とする',()=>{assert.equal(cardProgress(cards,[event('one')]).again,1);assert.equal(cardProgress([{...cards[0],version:2}],[event('one')]).seen,0);});
test('一周内の既出と一周後の直前カードを避け、もう一度のカードを優先する',()=>{assert.equal(nextCard(cards,[event('two')]).cardId,'two');assert.equal(nextCard(cards,[event('two')],{seen:['two']}).cardId,'one');assert.notEqual(nextCard(cards,[event('two')],{cardId:'two',seen:['one','two','three']}).cardId,'two');assert.equal(nextCard(cards,[],{topicId:'math'}),null);});
test('カードの出典分野違い、自己評価の不正な値・重複IDを拒否する',()=>{const deck={format:'hitomon-flashcards',version:1,qualificationId:'ap',cards};assert.equal(validateDeck(deck,qualification,questions),deck);assert.throws(()=>validateDeck({...deck,cards:[{...cards[0],relatedQuestionIds:['write']}]},qualification,questions));assert.throws(()=>validateCardEvents([event('one'),event('one')]));assert.throws(()=>validateCardEvents([{...event('one'),outcome:'correct'}]));});

test('重点分野に紙なし候補がなければ、別分野を選んだ理由を明示する',()=>{const plan={timeZone:'Asia/Tokyo',phases:[{id:'p',name:'計算',start:'2026-10-01',end:'2026-10-31',examPartIds:['a'],focusTopicIds:['math']}]};const result=choose({plan,at:new Date('2026-10-07T01:00:00.000Z')});assert.equal(result.questionId,'read');assert.equal(result.reasonCode,'paperless_fallback');});
