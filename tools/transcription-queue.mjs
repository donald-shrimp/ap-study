#!/usr/bin/env node
/**
 * Inspect the transcription queue and safely choose the next unclaimed batch.
 * No API usage charges: the only remote API is the public GitHub REST API.
 *
 * Commands:
 *   node tools/transcription-queue.mjs status
 *   node tools/transcription-queue.mjs next --count 10
 *   node tools/transcription-queue.mjs check --manifest path.json --draft path.json
 *   node tools/transcription-queue.mjs next --offline  # unsafe preview ONLY
 */
import {readFile} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import * as http from 'node:http';
import {planQueue,validateManifest,validateDraft} from './transcription-queue-domain.mjs';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const DEFAULT_REPO='donald-shrimp/ap-study';
const BATCH_BRANCH='transcription/';
const JSON_HEADERS={
 'Accept':'application/vnd.github+json',
 'User-Agent':'hitomon-transcription-queue/1.0',
 'X-GitHub-Api-Version':'2022-11-28'
};

function argValue(args,name,fallback){
 const pos=args.indexOf(name);
 if(pos<0)return fallback;
 if(pos===args.length-1)throw Error(name+' needs an argument');
 return args[pos+1];
}
function safeRepo(value){
 if(!/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/.test(value))throw Error('invalid repository name');
 return value;
}
async function load(path){return JSON.parse(await readFile(resolve(ROOT,path),'utf8'));}
function manifestPath(batchId){return 'data/transcription-queue/'+batchId+'.json';}
async function api(url){
 const token=process.env.GITHUB_TOKEN||process.env.GH_TOKEN;
 const headers={...JSON_HEADERS,...(token?{Authorization:'Bearer '+token}:{})};
 let result;
 try{result=await fetch(url,{headers,signal:AbortSignal.timeout(20000)});}
 catch(error){throw Error('GitHub queue query failed. Refusing unsafe selection: '+error.message);}
 if(!result.ok)throw Error('GitHub queue query failed (HTTP '+result.status+'). Refusing unsafe selection.');
 return result.json();
}
async function remoteJSON(repo,path,ref){
 const file=await api('https://api.github.com/repos/'+repo+'/contents/'+path+'?ref='+encodeURIComponent(ref));
 if(file.encoding!=='base64'||!file.content)throw Error('Missing GitHub JSON: '+path);
 return JSON.parse(Buffer.from(file.content.replace(/\s/g,''),'base64').toString('utf8'));
}
async function mainRef(repo){
 const ref=await api('https://api.github.com/repos/'+repo+'/git/ref/heads/main');
 if(!/^[a-f0-9]{40}$/.test(ref.object?.sha))throw Error('Invalid main reference');
 return ref.object.sha;
}
async function remoteManifests(repo){
 const collected=[];
 for(let page=1;;page++){
  if(page>20)throw Error('More than 2000 open PRs; stopping without selecting.');
  const prs=await api('https://api.github.com/repos/'+repo+'/pulls?state=open&per_page=100&page='+page);
  if(!Array.isArray(prs))throw Error('Unexpected pull request result');
  for(const pr of prs){
   const head=pr.head?.ref||'';
   if(!head.startsWith(BATCH_BRANCH))continue;
   if(pr.base?.ref!=='main')throw Error('Transcription PR must target main: #'+pr.number);
   if(pr.head?.repo?.full_name!==repo)throw Error('Transcription PR from another repository: #'+pr.number);
   const id=head.slice(BATCH_BRANCH.length);
   if(!/^[a-z0-9]+-q[1-9][0-9]*-[1-9][0-9]*$/.test(id))throw Error('Unexpected transcription PR branch: '+head);
   const payload=await remoteJSON(repo,manifestPath(id),pr.head.sha);
   if(payload.batchId!==id)throw Error('PR branch and batch manifest disagree in #'+pr.number);
   collected.push(payload);
  }
  if(prs.length<100)break;
 }
 return collected;
}
async function main(){
 const args=process.argv.slice(2),command=args[0]||'status';
 if(!['status','next','check'].includes(command))throw Error('Use status, next, or check');
 const repo=safeRepo(argValue(args,'--repo',DEFAULT_REPO));
 const offline=args.includes('--offline');
 if(!offline&&(process.env.HTTPS_PROXY||process.env.HTTP_PROXY||process.env.https_proxy||process.env.http_proxy)){
  if(typeof http.setGlobalProxyFromEnv!=='function')throw Error('Proxy configured: use Node.js 24.5+ for inherited proxy support.');
  http.setGlobalProxyFromEnv();
 }
 const count=Number(argValue(args,'--count','10'));
 const sourceRef=offline?null:await mainRef(repo);
 const [progress,catalog]=await Promise.all([
  offline?load('data/transcription-progress.json'):remoteJSON(repo,'data/transcription-progress.json',sourceRef),
  offline?load('data/qualifications/ap/manifest.json'):remoteJSON(repo,'data/qualifications/ap/manifest.json',sourceRef)
 ]);
 if(catalog.id!=='ap'||!Array.isArray(catalog.packs))throw Error('AP catalog not available');
 if(!catalog.packs.every(p=>p.count===80&&/^[a-z0-9]+$/.test(p.id)))throw Error('AP pack layout changed; update queue tooling');
 const questionIds=catalog.packs.flatMap(p=>Array.from({length:p.count},(_,i)=>p.id+'-q'+(i+1)));
 const known=new Set(questionIds);
 const manifests=offline?[]:await remoteManifests(repo);
 const plan=planQueue({questionIds,progress,manifests,count});
 if(command==='check'){
  const manifestFile=argValue(args,'--manifest',null),draftFile=argValue(args,'--draft',null);
  if(!manifestFile||!draftFile)throw Error('check requires --manifest and --draft');
  const [manifest,draft]=await Promise.all([load(manifestFile),load(draftFile)]);
  const info=validateManifest(manifest,known);
  if(resolve(ROOT,draftFile)!==resolve(ROOT,info.draftFile))throw Error('Draft path does not match manifest');
  const colliding=manifests.filter(other=>other.batchId!==info.batchId&&other.questionIds.some(id=>info.questionIds.includes(id)));
  if(colliding.length)throw Error('Overlapping queue PR(s): '+colliding.map(x=>x.batchId).join(', '));
  // A local manifest needs the same completed-ID check as a remote PR.
  planQueue({questionIds,progress,manifests:[manifest],count});
  const result=validateDraft(manifest,draft,known);
  if(!offline&&await mainRef(repo)!==sourceRef)throw Error('Main changed during queue query; retry.');
  console.log(JSON.stringify({ok:true,remoteVerified:!offline,sourceRef,...result},null,2));
  return;
 }
 if(!offline&&await mainRef(repo)!==sourceRef)throw Error('Main changed during queue query; retry.');
 const result={...plan,remoteVerified:!offline,safeToEnqueue:!offline,repo,sourceRef};
 if(offline)result.warning='OFFLINE PREVIEW ONLY: open PRs were not checked. Do not enqueue based on this output.';
 if(command==='next'&&plan.nextBatchId){
  const batchId=plan.nextBatchId;
  result.suggested={
   branch:BATCH_BRANCH+batchId,
   manifestPath:manifestPath(batchId),
   draftFile:'data/transcription-drafts/chatgpt_'+batchId.replaceAll('-','_')+'.json',
   manifest:{
    format:'hitomon-transcription-queue',version:1,batchId,
    questionIds:plan.nextQuestionIds,author:'ChatGPT',status:'awaiting-review',
    draftFile:'data/transcription-drafts/chatgpt_'+batchId.replaceAll('-','_')+'.json',
    skipProposals:[]
   }
  };
 }
 console.log(JSON.stringify(result,null,2));
}
main().catch(error=>{console.error('transcription-queue: '+error.message);process.exitCode=1;});
