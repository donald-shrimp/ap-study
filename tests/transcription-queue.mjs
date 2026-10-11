import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {planQueue,validateManifest,validateDraft} from '../tools/transcription-queue-domain.mjs';

const ids=['r01h-q1','r01h-q2','r01h-q3','r01h-q4','r01h-q5','r01h-q6','r02a-q1','r02a-q2'];
const progress={
 total:8,reviewed:2,imageRetained:1,processed:3,remainingReview:5,
 packs:[{id:'r01h',count:2,ids:['r01h-q1','r01h-q2']}],
 imageRetainedIds:['r01h-q5'],nextBatch:{packId:'r01h',numbers:[3,4]}
};
function manifest(questionIds=['r01h-q3','r01h-q4'],skips=[]){
 const prefix=questionIds[0].split('-')[0];
 const batchId=prefix+'-q'+questionIds[0].split('-q')[1]+'-'+questionIds.at(-1).split('-q')[1];
 return {
  format:'hitomon-transcription-queue',version:1,batchId,questionIds,
  author:'ChatGPT',status:'awaiting-review',
  draftFile:'data/transcription-drafts/chatgpt_'+batchId.replaceAll('-','_')+'.json',
  skipProposals:skips
 };
}
function draftRow(id){
 return {id,format:'hitomon-markdown-math-v1',stem:'正確な原文',choices:['ア','イ','ウ','エ'].map(label=>({label,text:'原文の選択肢'})),image:null,imageAlt:'',sourceImageSHA256:['a'.repeat(64)],author:'ChatGPT'};
}

test('未処理と画像維持を別集計し、次の同一回から取り出す',()=>{
 const result=planQueue({questionIds:ids,progress,count:2});
 assert.equal(result.total,8);assert.equal(result.reviewed,2);
 assert.equal(result.imageRetained,1);assert.equal(result.processed,3);
 assert.equal(result.unclaimed,5);
 assert.deepEqual(result.nextQuestionIds,['r01h-q3','r01h-q4']);
 assert.equal(result.nextBatchId,'r01h-q3-4');
});

test('既存PRの10問を予約すると次の問題へ進む',()=>{
 const first=manifest();
 const result=planQueue({questionIds:ids,progress,manifests:[first],count:2});
 assert.equal(result.queued,2);assert.equal(result.unclaimed,3);
 assert.deepEqual(result.nextQuestionIds,['r01h-q6']);
 assert.equal(result.nextBatchId,'r01h-q6-6');
});

test('同じ問題を予約する複数のPRは厳格に拒否',()=>{
 const same=manifest();
 assert.throws(()=>planQueue({questionIds:ids,progress,manifests:[same,same]}),/duplicate reservation/);
});
test('すでに確認済みの問題を含む古いPRは止める',()=>{
 assert.throws(()=>planQueue({questionIds:ids,progress,manifests:[manifest(['r01h-q1'])]}),/completed question/);
});
test('進捗ファイルの件数乖離を検出',()=>{
 assert.throws(()=>planQueue({questionIds:ids,progress:{...progress,processed:4}}),/processed total mismatch/);
 assert.throws(()=>planQueue({questionIds:ids,progress:{...progress,remainingReview:6}}),/remainingReview total mismatch/);
 assert.throws(()=>planQueue({questionIds:ids,progress:{...progress,imageRetainedIds:['r01h-q2']}}),/image-retained ID/);
});
test('不正な予約と未知のID、混在回を拒否',()=>{
 assert.throws(()=>validateManifest({...manifest(),batchId:'different'},new Set(ids)),/batchId/);
 assert.throws(()=>validateManifest(manifest(['r01h-q3','r02a-q1']),new Set(ids)),/one exam pack/);
 assert.throws(()=>validateManifest(manifest(['r01h-q3','r01h-q3']),new Set(ids)),/duplicate question/);
 assert.throws(()=>validateManifest(manifest(['r01h-q999']),new Set(ids)),/unknown question/);
});
test('原稿構造のチェック、スキップ提案とレビュー済みの区別',()=>{
 const skip=manifest(['r01h-q3','r01h-q4'],[{id:'r01h-q4',reason:'図が複雑で現行の表示形式に対応していない'}]);
 assert.deepEqual(validateDraft(skip,[draftRow('r01h-q3')],new Set(ids)),{batchId:'r01h-q3-4',transcribed:1,skipProposed:1});
 assert.throws(()=>validateDraft(skip,[draftRow('r01h-q3'),draftRow('r01h-q4')],new Set(ids)),/draft count/);
 assert.throws(()=>validateDraft(manifest(),[draftRow('r01h-q3')],new Set(ids)),/draft count/);
 assert.throws(()=>validateDraft(manifest(),[draftRow('r01h-q3'),{...draftRow('r01h-q4'),choices:[]}],new Set(ids)),/four choices/);
 assert.throws(()=>validateDraft(manifest(),[draftRow('r01h-q3'),{...draftRow('r01h-q4'),sourceImageSHA256:['bad']}],new Set(ids)),/source image hash/);
});

test('現行APの生成カタログと進捗は同じ800問を参照する',async()=>{
 const config=JSON.parse(await readFile(new URL('../data/qualifications/ap/manifest.json',import.meta.url)));
 const live=JSON.parse(await readFile(new URL('../data/transcription-progress.json',import.meta.url)));
 const questionIds=config.packs.flatMap(p=>Array.from({length:p.count},(_,i)=>p.id+'-q'+(i+1)));
 const result=planQueue({questionIds,progress:live});
 assert.equal(result.total,config.count);
 assert.equal(result.reviewed,live.reviewed);
 assert.equal(result.processed,live.processed);
 assert.equal(result.unclaimed,live.remainingReview);
 if(live.nextBatch&&result.nextQuestionIds.length){
  assert.equal(result.nextQuestionIds[0],live.nextBatch.packId+'-q'+live.nextBatch.numbers[0]);
 }
});
