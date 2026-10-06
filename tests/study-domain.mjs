import test from 'node:test';
import assert from 'node:assert/strict';
import {createAttempt,selectAnswer,openHint,gradeAttempt,finalizeAttempt,makeState} from '../src/domain/study.js';
import {createStateValidator} from '../src/storage/validate.js';

// These are synthetic fixtures, never registered as public study material.
function question(count=5) {
  return {id:'same-question',qualificationId:'example',version:1,type:'singleChoice',packId:'first',packLabel:'テスト',number:1,title:'2＋3',topic:'基礎',topicId:'basic',source:'テスト作成者',stem:'2＋3は幾つですか。',sourceImages:[],imageSizes:[],related:[],adaptation:'検証用',choices:Array.from({length:count},(_,i)=>({id:`c${i}`,label:String(i+1),text:String(i+1)})),correctChoiceId:`c${count-1}`,answer:count-1,enrichment:'reviewed',hintStatus:'individual',hints:[{title:'操作',text:'2から3回、1ずつ増やす。',revealsAnswer:false},{title:'答え',text:`正答の選択肢は${count}。`,revealsAnswer:true}],summary:'まとめ',explanation:'説明',takeaway:'要点',choiceReasons:Array(count).fill('理由')};
}
const qualification={id:'example',topics:[{id:'basic',name:'基礎'}]};
function state(a){return {...makeState(),attempts:[a],currentId:a.id};}
function validate(questions,qual=qualification){return createStateValidator({getQuestions:()=>questions,getTopics:()=>['基礎'],getQualification:()=>qual});}

test('5択の選択と、回答後のヒントは確定結果を変えない',()=>{
  const q=question(),a=createAttempt(q);assert.equal(selectAnswer(a,4),true);
  assert.equal(selectAnswer(a,5),false);assert.equal(a.selectedChoiceId,'c4');
  assert.equal(gradeAttempt(a,q.answer),'correct');finalizeAttempt(a,'correct');
  openHint(a);openHint(a);assert.equal(a.hintEvents[1].phase,'after');
  assert.equal(a.hintsBeforeAnswer,0);assert.equal(a.answerViewedBefore,false);
  assert.equal(gradeAttempt(a,q.answer),'correct');assert.equal(finalizeAttempt(a,'revealed'),false);
  validate([q])(state(a));
});

test('支援された正解と、正答開示を区別する',()=>{
  const q=question(2),a=createAttempt(q);openHint(a);selectAnswer(a,1);
  assert.equal(gradeAttempt(a,q.answer),'assisted');openHint(a);
  assert.equal(gradeAttempt(a,q.answer),'revealed');
  finalizeAttempt(a,'revealed');validate([q])(state(a));
});

test('問題訂正・取り下げ後も、保存した問題と正答で記録を検証する',()=>{
  const q=question(),a=createAttempt(q);selectAnswer(a,4);
  q.answer=0;q.correctChoiceId='c0';q.hints[0].text='変更したヒント';
  assert.equal(a.materialSnapshot.hints[0].text,'2から3回、1ずつ増やす。');
  assert.equal(gradeAttempt(a,q.answer),'correct');finalizeAttempt(a,'correct');
  validate([q])(state(a));validate([])(state(a));
});

test('別資格と、実行可能なURLを含むスナップショットを拒否する',()=>{
  const a=createAttempt(question());
  assert.throws(()=>validate([],{id:'other',topics:[]})(state(a)));
  a.questionSnapshot.image='javascript:alert(1)';
  assert.throws(()=>validate([])(state(a)));
});
