import test from 'node:test';
import assert from 'node:assert/strict';
import {hasLawChange,legalStudyAllowed,legalContextLines,legalAIPrompt} from '../src/domain/legal-context.js';
import {selectPractice} from '../src/domain/practice.js';
import {chooseNextAction} from '../src/domain/next-action.js';
import {selectDiagnostic,createDiagnostic,validateDiagnostic} from '../src/domain/diagnostic.js';
import {canStartDiagnostic} from '../src/domain/qualification-features.js';
import {makeState} from '../src/domain/study.js';
import {createStateValidator} from '../src/storage/validate.js';
import {sourceRecord,legalReview} from './fp2-fixtures.mjs';
const qualification={id:'synthetic',topics:[{id:'t',name:'合成分野'}],examParts:[{id:'objective',label:'合成試験',practiceAvailable:true}],defaultExamPartId:'objective',diagnosticBlueprint:{size:30}};
const oldReview={status:'outdated',checkedAt:'2026-10-24',sourceRefs:['https://example.com/law'],note:'合成の法令改正情報。'};
const q=n=>({id:'q'+n,qualificationId:'synthetic',examPartId:'objective',version:1,topicId:'t',topic:'合成分野',title:'合成問題',source:'合成テスト',stem:'1+1は？',type:'singleChoice',uses:['practice','diagnostic'],sourceKind:'authored',choices:[{id:'a',label:'A',text:'1'},{id:'b',label:'B',text:'2'}],correctChoiceId:'b',answer:1,sourceImages:[],imageSizes:[],related:[],adaptation:'',hints:[],summary:'',explanation:'1+1=2',takeaway:'',choiceReasons:['加算前','加算後'],enrichment:'reviewed',hintStatus:'individual',sourceRecord:structuredClone(sourceRecord),legalReview:structuredClone(legalReview)});
test('review dates stay internal; unchecked items remain eligible and only confirmed changes warn',()=>{
 const normal=q(0),old={...q(1),legalReview:oldReview};
 assert.equal(hasLawChange(normal),false);assert.equal(hasLawChange(old),true);
 assert.equal(legalStudyAllowed(normal),true);assert.equal(legalStudyAllowed(old),false);assert.equal(legalStudyAllowed(old,{excludeOutdated:false}),true);
 assert.deepEqual(legalContextLines(normal),['法令基準日：2026-04-01']);
 const current={...normal,legalReview:{...oldReview,status:'current'}};assert.deepEqual(legalContextLines(current),legalContextLines(normal));
 assert.deepEqual(legalContextLines(old),['法令基準日：2026-04-01','法令改正あり（学習非推奨）']);
 assert.match(legalAIPrompt(old),/最終法令チェック：2026-10-24 · 法令改正フラグ：あり/);
});
test('normal, review and paused recommendations use the same exclusion, and inclusion restores candidates',()=>{
 const old={...q(1),legalReview:oldReview},fresh=q(2),options={qualification,questions:[old,fresh],reviewInfo:()=>({needs:true,isDue:true}),practiceAllowed:legalStudyAllowed};
 for(const intent of ['normal','review'])assert.equal(selectPractice({...options,intent}).questionId,fresh.id);
 const paused={id:'paused',questionId:old.id,questionSnapshot:old,status:'in_progress',updatedAt:'2026-10-24T00:00:00Z'};
 assert.equal(chooseNextAction({...options,attempts:[paused]}).kind,'question');
 assert.equal(chooseNextAction({...options,attempts:[paused],practiceAllowed:m=>legalStudyAllowed(m,{excludeOutdated:false})}).kind,'resume');
});
test('diagnostic availability and selection agree on exclusions; existing snapshots remain valid',()=>{
 const bank=Array.from({length:31},(_,n)=>q(n));bank[0].legalReview=oldReview;
 const chosen=selectDiagnostic(bank,qualification,[],()=>.5,[],legalStudyAllowed);assert.equal(chosen.length,30);assert.ok(chosen.every(legalStudyAllowed));
 const insufficient=bank.slice(0,30);assert.equal(canStartDiagnostic(qualification,insufficient,legalStudyAllowed),false);assert.throws(()=>selectDiagnostic(insufficient,qualification,[],()=>.5,[],legalStudyAllowed));
 assert.equal(canStartDiagnostic(qualification,insufficient,()=>true),true);
 const run=createDiagnostic(insufficient,qualification);const validator=createStateValidator({getQuestions:()=>bank,getTopics:()=>['合成分野'],getQualification:()=>qualification,allowDiagnosticOnly:true});
 validateDiagnostic(run,qualification,a=>validator({...makeState(),attempts:[a]}));
});
test('exclusion preference defaults safely, survives state validation, and rejects invalid types',()=>{
 const validate=createStateValidator({getQuestions:()=>[],getTopics:()=>[],getQualification:()=>qualification}),s=makeState();assert.equal(s.settings.excludeOutdated,true);
 delete s.settings.excludeOutdated;assert.equal(validate(s).settings.excludeOutdated,true);s.settings.excludeOutdated=false;assert.equal(validate(s).settings.excludeOutdated,false);s.settings.excludeOutdated='false';assert.throws(()=>validate(s));
});
