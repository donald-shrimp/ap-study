import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, mkdir, writeFile, copyFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';

const sha='a'.repeat(40);
test('CLI uses pinned remote main; offline, stale local manifests and API errors are safe',async()=>{
 const root=await mkdtemp(join(tmpdir(),'transcription-queue-cli-'));
 try{
  for(const folder of ['tools','data/qualifications/ap','data/transcription-queue','data/transcription-drafts'])await mkdir(join(root,folder),{recursive:true});
  for(const file of ['transcription-queue.mjs','transcription-queue-domain.mjs'])await copyFile(new URL('../tools/'+file,import.meta.url),join(root,'tools',file));
  const local={total:80,reviewed:0,imageRetained:0,processed:0,remainingReview:80,packs:[],imageRetainedIds:[],nextBatch:{packId:'r01h',numbers:[1]}};
  const remote={...local,reviewed:1,processed:1,remainingReview:79,packs:[{id:'r01h',count:1,ids:['r01h-q1']}]};
  const catalog={id:'ap',packs:[{id:'r01h',count:80}]};
  await writeFile(join(root,'data/transcription-progress.json'),JSON.stringify(local));
  await writeFile(join(root,'data/qualifications/ap/manifest.json'),JSON.stringify(catalog));
  const batchId='r01h-q1-1',draftFile='data/transcription-drafts/chatgpt_r01h_q1_1.json';
  const manifest={format:'hitomon-transcription-queue',version:1,batchId,questionIds:['r01h-q1'],author:'ChatGPT',status:'awaiting-review',draftFile,skipProposals:[]};
  await writeFile(join(root,'data/transcription-queue/'+batchId+'.json'),JSON.stringify(manifest));
  await writeFile(join(root,draftFile),JSON.stringify([{id:'r01h-q1',format:'hitomon-markdown-math-v1',stem:'原文',choices:['ア','イ','ウ','エ'].map(label=>({label,text:'原文'})),author:'ChatGPT',sourceImageSHA256:['b'.repeat(64)]}]));
  const fixture=join(root,'fixture.json');await writeFile(fixture,JSON.stringify({remote,catalog}));
  const loader=join(root,'fake-github.mjs');
  await writeFile(loader,`import {readFileSync} from 'node:fs';
const {remote,catalog}=JSON.parse(readFileSync(process.env.QUEUE_TEST_FIXTURE));let refs=0;
globalThis.fetch=async address=>{
 const url=new URL(address);if(url.origin!=='https://api.github.com')throw Error('unexpected host');
 if(process.env.QUEUE_TEST_MODE==='http-error')return new Response('{}',{status:503});
 if(url.pathname.endsWith('/git/ref/heads/main')){refs++;return Response.json({object:{sha:process.env.QUEUE_TEST_MODE==='changed'&&refs>1?'c'.repeat(40):'a'.repeat(40)}});}
 if(url.pathname.endsWith('/pulls'))return Response.json([]);
 if(url.searchParams.get('ref')!=='a'.repeat(40))throw Error('main data not pinned');
 const data=url.pathname.endsWith('/transcription-progress.json')?remote:url.pathname.endsWith('/manifest.json')?catalog:null;
 if(!data)throw Error('unexpected path');return Response.json({encoding:'base64',content:Buffer.from(JSON.stringify(data)).toString('base64')});
};`);
  const run=(args,mode='ok')=>spawnSync(process.execPath,['--import',loader,join(root,'tools/transcription-queue.mjs'),...args],{encoding:'utf8',env:{...process.env,QUEUE_TEST_FIXTURE:fixture,QUEUE_TEST_MODE:mode}});
  let r=run(['next']);assert.equal(r.status,0,r.stderr);let data=JSON.parse(r.stdout);assert.equal(data.processed,1);assert.equal(data.sourceRef,sha);assert.equal(data.nextQuestionIds[0],'r01h-q2');assert.equal(data.safeToEnqueue,true);
  r=run(['next','--offline'],'http-error');assert.equal(r.status,0,r.stderr);data=JSON.parse(r.stdout);assert.equal(data.processed,0);assert.equal(data.safeToEnqueue,false);assert.equal(data.sourceRef,null);
  r=run(['check','--manifest','data/transcription-queue/'+batchId+'.json','--draft',draftFile]);assert.equal(r.status,1);assert.match(r.stderr,/completed question/);
  r=run(['status'],'http-error');assert.equal(r.status,1);assert.match(r.stderr,/HTTP 503/);assert.equal(r.stdout,'');
  r=run(['next'],'changed');assert.equal(r.status,1);assert.match(r.stderr,/Main changed/);assert.equal(r.stdout,'');
  r=run(['check','--offline','--manifest','data/transcription-queue/'+batchId+'.json','--draft','fixture.json']);assert.equal(r.status,1);assert.match(r.stderr,/Draft path does not match/);
 }finally{await rm(root,{recursive:true,force:true});}
});
