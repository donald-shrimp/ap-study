import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {practicePool,selectPractice} from '../src/domain/practice.js';
import {chooseNextAction} from '../src/domain/next-action.js';
import {createProgress} from '../src/domain/review.js';
import {nextCard} from '../src/domain/flashcards.js';
import {createDiagnostic,diagnosticExposure,diagnosticAttempts,diagnosticResult,selectDiagnostic,submitDiagnostic,finishDiagnostic} from '../src/domain/diagnostic.js';
import {blankPlan} from '../src/domain/planning.js';

const published=new URL('../data/qualifications/ap/',import.meta.url),manifest=JSON.parse(readFileSync(new URL('manifest.json',published)));
const qualification={id:'ap',defaultExamPartId:'a',topics:[{id:'db',name:'DB'},{id:'nw',name:'NW'}],examParts:[{id:'a',practiceAvailable:true},{id:'b',practiceAvailable:false}]};
const questions=Array.from({length:12},(_,i)=>({id:'q'+i,qualificationId:'ap',topicId:i%2?'nw':'db',examPartId:'a',packId:i%3?'old':'new'}));
const noReview=()=>null;
const select=options=>selectPractice({qualification,questions,attempts:[],reviewInfo:noReview,...options});
const paused=(q,id=q.id)=>({id,qualificationId:'ap',questionId:q.id,status:'postponed',selected:null,hintCount:1,startedAt:'2026-10-07T01:00:00Z',updatedAt:'2026-10-07T01:00:00Z',entryMode:'all'});

test('3入口の選択器は計画を固定条件にせず、明示した分野だけを限定する',()=>{
 const opts={qualification,questions,attempts:[],reviewInfo:noReview,plan:{...blankPlan(qualification),phases:[{start:'2000-01-01',end:'2100-01-01',focusTopicIds:['db'],examPartIds:['a']}]}};
 const initial=chooseNextAction(opts),next=selectPractice(opts);assert.equal(initial.questionId,next.questionId);assert.equal(initial.scope.topicId,null);
 assert.equal(select({scope:{topicId:'db'}}).topicId,'db');assert.deepEqual(select({scope:{topicIds:['db','nw']}}).scope.topicIds,['db','nw']);
});
test('別資格・派生・未対応パートは初回・継続・再開の全入口で除外する',()=>{
 const invalid=[{...questions[0],id:'other',qualificationId:'other'},{...questions[0],id:'derived',diagnosticOnly:true},{...questions[0],id:'written',examPartId:'b'}];
 assert.equal(practicePool({qualification,questions:invalid}).length,0);
 assert.equal(select({questions:invalid}).kind,'unavailable');
 assert.equal(chooseNextAction({qualification,questions:invalid,attempts:invalid.map(q=>paused(q)),reviewInfo:noReview}).kind,'unavailable');
});
test('古い復習期限を初回・継続とも先にし、同順位だけ分散する',()=>{
 const info=new Map(questions.slice(0,3).map((q,i)=>[q.id,{a:{completedAt:'2026-10-01T00:00:00Z'},isDue:true,needs:true,due:new Date('2026-10-0'+(3-i))}]));
 const opts={qualification,questions,attempts:[],reviewInfo:q=>info.get(q.id)};
 assert.equal(chooseNextAction(opts).questionId,'q2');assert.equal(selectPractice(opts).questionId,'q2');
 assert.equal(selectPractice({...opts,visitedQuestionIds:['q2']}).questionId,'q1');
});
test('復習入口は未着手を混ぜず、復習が尽きたら停止する',()=>{
 const info=q=>q.id==='q1'?{needs:true,isDue:false,a:{completedAt:'2026-10-01'},due:new Date('2026-10-02')}:null;
 assert.equal(select({intent:'review',reviewInfo:info}).questionId,'q1');
 assert.equal(select({intent:'review',reviewInfo:info,visitedQuestionIds:['q1']}).kind,'unavailable');
 assert.equal(select({intent:'review'}).kind,'unavailable');
});
test('先送りはホームの再開にも次の問題にも選ばず、条件不足で黙って範囲を広げない',()=>{
 const a={...paused(questions[0]),deferred:true};
 const opts={qualification,questions:[questions[0]],attempts:[a],reviewInfo:noReview};
 assert.equal(chooseNextAction(opts).kind,'unavailable');assert.equal(selectPractice(opts).kind,'unavailable');
 assert.equal(select({scope:{topicId:'unknown'}}).kind,'unavailable');
 assert.equal(select({available:()=>false}).kind,'unavailable');
});
test('他入口の未回答と指定問題の中断を自動で重複開始しない',()=>{
 const chosen=select().questionId,q=questions.find(q=>q.id===chosen),a={...paused(q),practiceScope:{intent:'direct'}};
 assert.notEqual(select({attempts:[a]}).questionId,q.id);
 assert.equal(chooseNextAction({qualification,questions,attempts:[a],reviewInfo:noReview}).kind,'question');
});
test('実教材で直近20問の分野・年度の固まりを避け、順序を固定配列に依存させない',()=>{
 const q=JSON.parse(readFileSync(new URL('../content/ap/qualification.json',import.meta.url)));
 const rows=JSON.parse(readFileSync(new URL(manifest.index.url,published)));
 const attempts=[],chosen=[];
 for(let i=0;i<20;i++){
  const result=selectPractice({qualification:q,questions:rows,attempts,reviewInfo:noReview}),item=rows.find(q=>q.id===result.questionId);chosen.push(item);
  attempts.push({...paused(item,'a'+i),status:'correct',startedAt:new Date(Date.UTC(2026,9,8,0,i)).toISOString()});
 }
 assert.ok(new Set(chosen.map(q=>q.topicId)).size>=10);assert.ok(new Set(chosen.map(q=>q.packId)).size>=5);
 assert.equal(selectPractice({qualification:q,questions:rows,attempts:[],reviewInfo:noReview}).questionId,selectPractice({qualification:q,questions:rows.slice().reverse(),attempts:[],reviewInfo:noReview}).questionId);
});
test('UTC/JST端末で基準タイムゾーンの復習日と成功日数が一致する',()=>{
 const script=`import {createProgress} from './src/domain/review.js';const a={id:'a',questionId:'q',status:'incorrect',completedAt:'2026-10-07T15:30:00Z'};const r=createProgress([a],{timeZone:'Asia/Tokyo'}).reviewInfo({id:'q'},'2026-10-08T01:00:00Z');console.log(JSON.stringify({due:r.dueDate,isDue:r.isDue}));`;
 const results=['UTC','Asia/Tokyo','America/New_York'].map(TZ=>{const r=spawnSync(process.execPath,['--input-type=module','-e',script],{cwd:new URL('..',import.meta.url),env:{...process.env,TZ},encoding:'utf8'});assert.equal(r.status,0,r.stderr);return JSON.parse(r.stdout);});
 assert.deepEqual(results,[{due:'2026-10-09',isDue:false},{due:'2026-10-09',isDue:false},{due:'2026-10-09',isDue:false}]);
 const a=t=>({id:t,questionId:'q',status:'correct',completedAt:t});
 const progress=createProgress([a('2026-10-07T14:59:00Z'),a('2026-10-07T15:01:00Z')],{timeZone:'Asia/Tokyo'});
 assert.equal(progress.reviewInfo({id:'q'}).successes,2);assert.equal(progress.reviewInfo({id:'q'}).dueDate,'2026-10-15');
});
test('全681枚でももう一度は別の3枚後に戻り、思い出せた後は新規へ進む',()=>{
 const cards=JSON.parse(readFileSync(new URL('../content/ap/flashcards.json',import.meta.url))).cards;
 let checkpoint=nextCard(cards,[]),first=checkpoint.cardId;const events=[],shown=[first];
 for(let i=0;i<4;i++){events.push({id:'e'+i,cardId:checkpoint.cardId,cardVersion:checkpoint.cardVersion,outcome:i===0?'again':'recalled',at:new Date(Date.UTC(2026,9,8,0,i)).toISOString()});checkpoint=nextCard(cards,events,{...checkpoint,seen:[...new Set([...checkpoint.seen,checkpoint.cardId])],recent:[...checkpoint.recent,checkpoint.cardId].slice(-10)});shown.push(checkpoint.cardId);}
 assert.equal(new Set(shown.slice(0,4)).size,4);assert.equal(shown[4],first);
 events.push({id:'e4',cardId:first,cardVersion:checkpoint.cardVersion,outcome:'recalled',at:'2026-10-08T00:04:00.000Z'});
 assert.notEqual(nextCard(cards,events,{...checkpoint,recent:[...checkpoint.recent,first]}).cardId,first);
 for(const length of [1,2,3]){const small=cards.slice(0,length),c=small[0];const next=nextCard(small,[{id:'e',cardId:c.id,cardVersion:c.version,outcome:'again',at:'2026-10-08T00:00:00.000Z'}],{cardId:c.id,recent:[c.id]});assert.ok(next);if(length>1)assert.notEqual(next.cardId,c.id);}
});
test('診断の表示・スキップと回答を区別し、未表示枠を既出にしない',()=>{
 const original=JSON.parse(readFileSync(new URL(manifest.packs.find(p=>p.id==='r07h').url,published)));
 const q=JSON.parse(readFileSync(new URL('../content/ap/qualification.json',import.meta.url)));
 const chosen=selectDiagnostic(original,q),run=createDiagnostic(chosen,q),first=run.slots[0].attempt.questionId,unopened=run.slots[2].attempt.questionId;
 submitDiagnostic(run,null);finishDiagnostic(run);
 assert.deepEqual(diagnosticExposure(run).map(a=>a.questionId),run.slots.slice(0,2).map(s=>s.attempt.questionId));
 assert.equal(diagnosticAttempts(run).length,0);const result=diagnosticResult(run,q);assert.equal(result.answered,0);assert.equal(result.skipped,1);assert.equal(result.exposed,2);
 assert.equal(result.items[0].skipped,true);assert.equal(result.items[2].exposed,false);
 const next=createDiagnostic(chosen,q,diagnosticExposure(run));assert.equal(next.slots.find(s=>s.attempt.questionId===first).previouslySeen,true);assert.equal(next.slots.find(s=>s.attempt.questionId===unopened).previouslySeen,false);
});
