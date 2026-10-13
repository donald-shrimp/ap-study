import test from 'node:test';
import assert from 'node:assert/strict';
import {canStartDiagnostic} from '../src/domain/qualification-features.js';
import {createPlanningViews} from '../src/ui/planning.js';

test('診断は明示設定と対応パートの独立30問が揃った資格だけで開始できる',()=>{
 const q={id:'second',topics:[{id:'basic',name:'基礎'}],diagnosticBlueprint:{size:30},examParts:[{id:'a',practiceAvailable:true},{id:'b',practiceAvailable:false}]};
 const questions=Array.from({length:30},(_,i)=>({id:'q'+i,qualificationId:'second',examPartId:'a',topicId:'basic'}));
 assert.equal(canStartDiagnostic(q,questions),true);
 assert.equal(canStartDiagnostic({...q,diagnosticBlueprint:undefined},questions),false);
 assert.equal(canStartDiagnostic({...q,diagnosticBlueprint:{size:10}},questions),false);
 assert.equal(canStartDiagnostic(q,questions.slice(1)),false);
 assert.equal(canStartDiagnostic(q,[...questions.slice(1),{...questions[29]}]),false);
 for(const extra of [{qualificationId:'other'},{examPartId:'b'},{diagnosticOnly:true}])
  assert.equal(canStartDiagnostic(q,[...questions.slice(1),{...questions[0],...extra}]),false);
});

test('診断提供を止めても、保存済みの中断と結果への入口は残す',()=>{
 const qualification={id:'second',name:'検証資格',topics:[{id:'basic',name:'基礎'}]};
 const run={id:'existing',status:'in_progress',startedAt:'2026-10-01T00:00:00Z',completedAt:null,size:30,currentIndex:0,responses:{},slots:[]};
 const views=payload=>createPlanningViews({qualification,documents:payload?[{id:payload.id,kind:'diagnostic',payload}]:[],attempts:[],diagnosticEnabled:false});
 assert.equal(views().hasDiagnostics,false);
 assert.ok(!views().diagnosticsHTML().includes('data-action="start-diagnostic"'));
 assert.equal(views(run).hasDiagnostics,true);
 assert.ok(views(run).diagnosticsHTML().includes('data-action="resume-diagnostic"'));
 const ended={...run,status:'ended_early',completedAt:'2026-10-01T00:01:00Z'};
 assert.equal(views(ended).hasDiagnostics,true);
 assert.ok(views(ended).diagnosticsHTML().includes('結果を見る'));
 assert.ok(!views(ended).diagnosticsHTML().includes('data-action="start-diagnostic"'));
});
