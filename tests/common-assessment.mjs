import test from 'node:test';
import assert from 'node:assert/strict';
import {makeState,createAttempt} from '../src/domain/study.js';
import {createStateValidator} from '../src/storage/validate.js';
import {selectDiagnostic,createDiagnostic,validateDiagnostic,submitDiagnostic,finishDiagnostic,diagnosticResult} from '../src/domain/diagnostic.js';
import {createMock,validateMock,mockQuestions} from '../src/domain/mock.js';
import {canStartDiagnostic} from '../src/domain/qualification-features.js';
import {weightedQuotas} from '../src/domain/assessment-sampling.js';
import {validateDeck} from '../src/domain/flashcards.js';

const qualification={id:'synthetic',name:'非公開テスト資格',topics:[{id:'a',name:'分野A'},{id:'b',name:'分野B'}],defaultExamPartId:'test',examParts:[{id:'test',label:'試験',practiceAvailable:true}],diagnosticBlueprint:{size:40,sampling:'topic-weighted',weights:{a:3,b:1}}};
const q=(i,topicId='a',uses=['diagnostic','mock'])=>({id:'q'+i,qualificationId:'synthetic',examPartId:'test',version:1,type:'singleChoice',sourceKind:'authored',uses,packId:'test',packLabel:'非公開テスト',number:i+1,title:'足し算',topic:topicId==='a'?'分野A':'分野B',topicId,source:'合成テスト',stem:'1＋1は？',sourceImages:[],imageSizes:[],related:[],adaptation:'',choices:[{id:'a',label:'A',text:'1'},{id:'b',label:'B',text:'2'}],correctChoiceId:'b',answer:1,enrichment:'reviewed',hintStatus:'individual',hints:[],summary:'',explanation:'1＋1＝2',takeaway:'',choiceReasons:['加算前','加算後'],syllabusId:'edition-one',language:'ja-JP',objectiveIds:['add'],sourceRefs:['https://example.com/learning']});
const extras=[...Array.from({length:36},(_,i)=>q(i)),...Array.from({length:20},(_,i)=>q(36+i,'b'))];
const normal={...q(100,'a',['practice','diagnostic']),hints:[]};delete normal.diagnosticOnly;
const check=qual=>{const validator=createStateValidator({getQuestions:()=>[normal],getTopics:()=>qual.topics.map(t=>t.name),getQualification:()=>qual,allowDiagnosticOnly:true});return attempt=>validator({...makeState(),attempts:[attempt]});};
const set={id:'fixed',label:'テスト模試',version:1,status:'ready',size:40,slots:extras.slice(0,40).map((q,i)=>({number:i+1,questionId:q.id,topicId:q.topicId}))};

test('親のない独自問題40問で重み付き診断を開始し、採点と保存を独立に確認',()=>{
 const chosen=selectDiagnostic([normal],qualification,[],()=>.42,extras);
 assert.equal(chosen.length,40);assert.equal(chosen.filter(q=>q.topicId==='a').length,30);assert.ok(chosen.every(q=>!q.parentQuestionId&&!q.uses.includes('practice')));
 const run=createDiagnostic(chosen,qualification);assert.equal(canStartDiagnostic({...qualification,assessment:{index:extras}},[normal]),true);
 assert.deepEqual(validateDiagnostic(run,qualification,check(qualification)),run);
 for(let i=0;i<40;i++)submitDiagnostic(run,i<30?'b':'a');
 const result=diagnosticResult(run,qualification);assert.equal(result.items[0].syllabusId,'edition-one');assert.equal(result.items[0].language,'ja-JP');assert.equal(result.correct,30);assert.equal(result.size,40);assert.equal(result.composition.find(r=>r.kind==='authored').selected,40);
});
test('資格の問題数・分野・対象版が更新されても開始済み診断を保持',()=>{
 const run=createDiagnostic(selectDiagnostic([normal],qualification,[],()=>.42,extras),qualification),before=JSON.stringify(run);
 const changed={...qualification,topics:[{id:'new',name:'新しい分野'}],defaultSyllabusId:'edition-two',diagnosticBlueprint:{size:60,sampling:'topic-round-robin'}};
 validateDiagnostic(run,changed,check(changed));assert.equal(JSON.stringify(run),before);
 submitDiagnostic(run,'b');finishDiagnostic(run);assert.deepEqual(diagnosticResult(run,changed).topics.filter(r=>r.answered).map(r=>r.label),[run.slots[0].attempt.questionSnapshot.topic]);
});
test('40問固定模試は親なし・順序固定で、現在のカタログに依存せず検証',()=>{
 const run=createMock(set,extras,qualification),again=createMock(set,[...extras].reverse(),qualification);
 assert.notEqual(run.id,again.id);assert.deepEqual(run.slots.map(s=>s.attempt.questionId),set.slots.map(s=>s.questionId));
 assert.deepEqual(validateMock(run,qualification,check(qualification)),run);
 for(const edit of [r=>r.size=39,r=>r.slots[0].kind='derived',r=>r.slots[0].attempt.questionSnapshot.uses=['practice'],r=>r.slots[0].attempt.hintCount=1]){const bad=structuredClone(run);edit(bad);assert.throws(()=>validateMock(bad,qualification,check(qualification)));}
});
test('用途を分離し、未確認・重複ファミリー・派生の偽親・配分不足を拒否',()=>{
 assert.throws(()=>createAttempt(extras[0]));assert.doesNotThrow(()=>createAttempt(normal));
 assert.throws(()=>mockQuestions({...set,slots:set.slots.map((s,i)=>i===1?{...s,questionId:set.slots[0].questionId}:s)},extras));
 const sameFamily=extras.map((q,i)=>i<2?{...q,familyId:'same-scenario'}:q);assert.throws(()=>mockQuestions(set,sameFamily));
 assert.throws(()=>selectDiagnostic([normal],qualification,[],()=>.42,[...extras,{...q(70),sourceKind:'derived',parentQuestionId:'missing'}]));
 assert.throws(()=>selectDiagnostic([normal],qualification,[],()=>.42,extras.slice(0,40)));
 const wrongUse=extras.map(q=>({...q,uses:['mock']}));assert.equal(canStartDiagnostic({...qualification,assessment:{index:wrongUse}},[normal]),false);assert.throws(()=>selectDiagnostic([normal],qualification,[],()=>.42,wrongUse));
});
test('重みの丸め・不正設定・prototype名を持つ分野を検証',()=>{
 assert.deepEqual([...weightedQuotas({a:3,b:1},40)], [['a',30],['b',10]]);
 const thirds=weightedQuotas({a:1,b:1,c:1},40);assert.equal([...thirds.values()].reduce((a,b)=>a+b),40);assert.equal(thirds.get('a'),14);
 assert.equal(weightedQuotas({a:1,A:1},31).get('A'),16);
 for(const blueprint of [{size:10},{size:201},{size:40,sampling:'topic-weighted',weights:{a:0}},{size:40,sampling:'topic-weighted',weights:{unknown:1}}])assert.equal(canStartDiagnostic({...qualification,diagnosticBlueprint:blueprint},extras),false);
 const special={...qualification,topics:[{id:'constructor',name:'特殊分野'}],diagnosticBlueprint:{size:30}},pool=extras.slice(0,30).map(q=>({...q,topicId:'constructor',topic:'特殊分野'}));assert.equal(selectDiagnostic([],special,[],()=>.4,pool).length,30);
});
test('問題なしでもカードを持てる。複数分野の問題へ任意に関連付ける',()=>{
 const deck={format:'hitomon-flashcards',version:1,qualificationId:qualification.id,cards:[{id:'term',version:1,topicId:'b',front:'用語',back:'意味'}]};
 validateDeck(deck,qualification,[normal]);assert.deepEqual(deck.cards[0].relatedQuestionIds,[]);assert.equal(deck.cards[0].sourceNote,'');
 deck.cards[0].relatedQuestionIds=[normal.id];assert.doesNotThrow(()=>validateDeck(deck,qualification,[normal]));
});

import {createMockViews} from '../src/ui/mocks.js';
import {createPlanningViews} from '../src/ui/planning.js';
test('模試セットの変更・公開終了後も保存済み40問の再開と結果を表示する',()=>{
 const run=createMock(set,extras,qualification),documents=[{id:run.id,kind:'mock',payload:run}];
 const updated={...qualification,mockSets:{count:1,sets:[{...set,size:20}]}};
 const activeHTML=createMockViews({qualification:updated,documents}).selectionHTML();assert.match(activeHTML,/固定20問/);assert.match(activeHTML,/0 \/ 40問/);
 const retired=createMockViews({qualification:{...qualification,mockSets:{count:0,sets:[]}},documents});assert.match(retired.selectionHTML(),/続きから/);assert.doesNotMatch(retired.selectionHTML(),/data-action="start-mock"/);
 submitDiagnostic(run,'b');finishDiagnostic(run);
 const views=createPlanningViews({qualification:{...qualification,mockSets:{count:0,sets:[]}},documents,attempts:[],currentRunId:run.id,practiceQuestionIds:new Set(),practiceTopicIds:new Set()});
 assert.equal(views.hasMocks,true);const result=views.diagnosticHTML();assert.match(result,/全40問を分母/);assert.doesNotMatch(result,/全80問|data-action="topic-session"/);assert.match(views.mockRecordsHTML(),/記録を見る/);
});
