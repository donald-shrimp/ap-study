import test from 'node:test';
import assert from 'node:assert/strict';
import {chooseFieldAction} from '../src/domain/next-action.js';
import {learningFields,summarizeFields,diagnosticFields} from '../src/domain/analytics.js';
const qualification={id:'test',topics:[{id:'db',name:'DB'},{id:'nw',name:'NW'}],defaultExamPartId:'a',examParts:[{id:'a',practiceAvailable:true},{id:'b',practiceAvailable:true}]};
const questions=[{id:'db-a',qualificationId:'test',topicId:'db',examPartId:'a',mode:'paperless'},{id:'db-b',qualificationId:'test',topicId:'db',examPartId:'b',mode:'desk'},{id:'nw-a',qualificationId:'test',topicId:'nw',examPartId:'a',mode:'paperless'}];
const paused=(patch={})=>({id:'paused',questionId:'db-a',qualificationId:'test',status:'postponed',selected:2,hintCount:1,startedAt:'2026-10-08T01:00:00Z',updatedAt:'2026-10-08T02:00:00Z',entryMode:'paperless',practiceScope:{intent:'topic',topicId:'db',topicIds:[],examPartId:null,examPartIds:[],paperMode:'paperless'},...patch});
function choose(attempts=[],patch={}){const paperMode=patch.paperMode||'paperless';return chooseFieldAction({qualification,questions,attempts,topicId:'db',paperMode,reviewInfo:()=>null,practiceAllowed:q=>paperMode==='all'||q.mode===paperMode,...patch});}
test('same explicit field and entrance resumes its existing checkpoint',()=>{assert.equal(choose([paused()]).attemptId,'paused');assert.equal(choose([paused()]).kind,'resume');});
test('a normal, review, direct or multi-field checkpoint never changes field-start scope',()=>{
 for(const scope of [{intent:'normal',topicId:null},{intent:'review',topicId:'db'},{intent:'direct',topicId:'db'},{intent:'topic',topicId:null,topicIds:['db','nw']}])assert.equal(choose([paused({practiceScope:{...paused().practiceScope,...scope}})]).kind,'question');
});
test('paper and part conditions must match rather than carrying hidden constraints in',()=>{
 assert.equal(choose([paused()],{paperMode:'all'}).kind,'question');
 assert.equal(choose([paused({practiceScope:{...paused().practiceScope,examPartId:'a'}})]).kind,'question');
 assert.equal(choose([paused({practiceScope:{...paused().practiceScope,examPartId:'a'}})],{examPartId:'a'}).kind,'resume');
 assert.equal(choose([],{paperMode:'desk',examPartId:'b'}).questionId,'db-b');
});
test('completed, deferred, foreign and continued-parent records are not resumable',()=>{
 for(const patch of [{status:'correct',completedAt:'2026-10-08T03:00:00Z'},{deferred:true},{qualificationId:'other'}])assert.notEqual(choose([paused(patch)]).kind,'resume');
 assert.equal(choose([paused(),{...paused(),id:'child',continuationOf:'paused',deferred:true}]).kind,'unavailable');
});
test('offline availability and derived-only exclusion apply to field starts too',()=>{
 assert.equal(choose([paused()],{available:()=>false,online:false}).kind,'unavailable');
 assert.equal(choose([],{questions:[{...questions[0],diagnosticOnly:true}]}).kind,'unavailable');
 assert.equal(choose([],{questions:[questions[1]]}).kind,'unavailable');
});
test('overall unassisted accuracy uses latest unique completions, not assistance or diagnostics',()=>{
 const at=new Date('2026-10-09T01:00:00Z');
 const make=(id,status,extra={})=>({id,questionId:id,qualificationId:'test',status,completedAt:'2026-10-08T02:00:00Z',questionSnapshot:{topicId:'db',examPartId:'a'},...extra});
 const attempts=[make('a','correct'),make('b','assisted'),make('c','incorrect'),make('d','revealed'),make('old','incorrect',{questionId:'a',completedAt:'2026-10-07T02:00:00Z'}),make('diagnostic','correct',{diagnosticRunId:'run'}),make('future','correct',{completedAt:'2026-10-10T02:00:00Z'}),make('expired','correct',{completedAt:'2026-09-01T02:00:00Z'}),make('unfinished','in_progress')];
 assert.deepEqual(summarizeFields(learningFields({qualification,attempts,at})),{total:4,correct:1,rate:.25});
 assert.deepEqual(summarizeFields(learningFields({qualification,attempts:[],at})),{total:0,correct:0,rate:null});
 assert.deepEqual(summarizeFields(diagnosticFields({topics:[{topicId:'db',answered:2,correct:1}]},qualification)),{total:2,correct:1,rate:.5});
});
