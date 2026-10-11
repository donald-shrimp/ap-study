// Pure queue planning for transcription work. No AI/remote API required here.
// "Queued" means a submitted draft PR, NOT a reviewed or published question.
export const QUEUE_FORMAT='hitomon-transcription-queue';
export const QUEUE_VERSION=1;
const ID=/^([a-z0-9]+)-q([1-9][0-9]*)$/;
const hex=/^[a-f0-9]{64}$/i;

function need(test,message){if(!test)throw new Error(message);}
function idsOf(items,label){
 need(Array.isArray(items),label+' must be an array');
 const seen=new Set();
 for(const id of items){
  need(typeof id==='string'&&ID.test(id),label+': invalid question ID '+String(id));
  need(!seen.has(id),label+': duplicate question ID '+id);
  seen.add(id);
 }
 return seen;
}
function pack(id){return ID.exec(id)?.[1];}
function number(id){return Number(ID.exec(id)?.[2]);}
function slug(ids){
 need(ids.length>0,'empty batch');
 const prefix=pack(ids[0]);
 need(ids.every(id=>pack(id)===prefix),'batch must contain only one exam pack');
 const numbers=ids.map(number);
 need(numbers.every((n,i)=>i===0||n>numbers[i-1]),'batch IDs must be sorted numerically');
 return prefix+'-q'+numbers[0]+'-'+numbers[numbers.length-1];
}

export function validateManifest(record,knownIds){
 need(record&&typeof record==='object'&&!Array.isArray(record),'manifest must be an object');
 need(record.format===QUEUE_FORMAT&&record.version===QUEUE_VERSION,'unsupported queue manifest format');
 const ids=idsOf(record.questionIds,'manifest.questionIds');
 need(ids.size>=1&&ids.size<=20,'batch must contain 1–20 questions');
 for(const id of ids)need(knownIds.has(id),'unknown question ID '+id);
 need(record.batchId===slug(record.questionIds),'batchId must match question IDs');
 need(record.author==='ChatGPT','draft producer must be explicitly ChatGPT');
 need(record.status==='awaiting-review','initial queue status must be awaiting-review');
 need(record.draftFile==='data/transcription-drafts/chatgpt_'+record.batchId.replaceAll('-','_')+'.json','unexpected draft filename');
 const proposals=record.skipProposals??[];
 need(Array.isArray(proposals),'skipProposals must be an array');
 const seen=new Set();
 for(const row of proposals){
  need(row&&typeof row.id==='string'&&ids.has(row.id),'skip proposal outside batch');
  need(!seen.has(row.id),'duplicate skip proposal');
  need(typeof row.reason==='string'&&row.reason.trim().length>=12,'skip proposal needs a specific reason');
  seen.add(row.id);
 }
 return {batchId:record.batchId,questionIds:[...ids],skipIds:seen,draftFile:record.draftFile};
}

export function validateDraft(manifest,draft,knownIds){
 const batch=validateManifest(manifest,knownIds);
 need(Array.isArray(draft),'draft file must contain an array');
 const expected=new Set(batch.questionIds.filter(id=>!batch.skipIds.has(id)));
 need(draft.length===expected.size,'draft count does not match non-skipped batch entries');
 const seen=new Set();
 for(const row of draft){
  need(row&&expected.has(row.id)&&!seen.has(row.id),'draft contains unreserved or duplicate question');
  seen.add(row.id);
  need(row.format==='hitomon-markdown-math-v1','invalid transcription format: '+row.id);
  need(typeof row.stem==='string'&&row.stem.trim(),'missing stem: '+row.id);
  need(Array.isArray(row.choices)&&row.choices.length===4,'expected four choices: '+row.id);
  need(['ア','イ','ウ','エ'].every((label,i)=>row.choices[i]?.label===label&&typeof row.choices[i].text==='string'),'incorrect choice order/shape: '+row.id);
  need(Array.isArray(row.sourceImageSHA256)&&row.sourceImageSHA256.length>0&&row.sourceImageSHA256.every(d=>typeof d==='string'&&hex.test(d)),'missing source image hash: '+row.id);
  need(typeof row.author==='string'&&row.author.trim(),'missing draft author: '+row.id);
 }
 return {batchId:batch.batchId,transcribed:draft.length,skipProposed:batch.skipIds.size};
}

export function planQueue({questionIds,progress,manifests=[],count=10}){
 const known=idsOf(questionIds,'questionIds');
 need(known.size===progress?.total,'bank count differs from transcription progress');
 need(Array.isArray(progress?.packs),'missing reviewed pack list');
 const reviewed=new Set();
 for(const group of progress.packs){
  need(Array.isArray(group.ids)&&group.count===group.ids.length,'malformed reviewed pack '+group.id);
  for(const id of group.ids){
   need(known.has(id)&&pack(id)===group.id&&!reviewed.has(id),'invalid/duplicate reviewed ID '+id);
   reviewed.add(id);
  }
 }
 const retained=idsOf(progress.imageRetainedIds??[],'imageRetainedIds');
 for(const id of retained)need(known.has(id)&&!reviewed.has(id),'invalid/duplicated image-retained ID '+id);
 const processed=new Set([...reviewed,...retained]);
 need(reviewed.size===progress.reviewed,'reviewed total mismatch');
 need(retained.size===(progress.imageRetained??0),'image-retained total mismatch');
 need(processed.size===(progress.processed??reviewed.size+retained.size),'processed total mismatch');
 need(progress.remainingReview===known.size-processed.size,'remainingReview total mismatch');
 const queued=new Set();
 const batches=[];
 for(const item of manifests){
  const info=validateManifest(item,known);
  for(const id of info.questionIds){
   need(!processed.has(id),'open queue PR contains a completed question: '+id);
   need(!queued.has(id),'duplicate reservation in open queue PRs: '+id);
   queued.add(id);
  }
  batches.push({batchId:info.batchId,questionIds:info.questionIds,skipProposals:info.skipIds.size});
 }
 need(Number.isInteger(count)&&count>=1&&count<=20,'count must be between 1 and 20');
 const nextPref=progress.nextBatch?.packId&&Array.isArray(progress.nextBatch.numbers)
  ?progress.nextBatch.numbers.map(n=>progress.nextBatch.packId+'-q'+n):[];
 const currentPack=progress.nextBatch?.packId;
 const priority=[...nextPref,...questionIds.filter(id=>pack(id)===currentPack),...questionIds];
 const uniqueOrder=[...new Set(priority)].filter(id=>known.has(id));
 const free=uniqueOrder.filter(id=>!processed.has(id)&&!queued.has(id));
 const next=[];
 for(const id of free){
  if(next.length&&pack(id)!==pack(next[0]))break;
  next.push(id);
  if(next.length===count)break;
 }
 return {
  total:known.size,reviewed:reviewed.size,imageRetained:retained.size,processed:processed.size,
  queued:queued.size,unclaimed:known.size-processed.size-queued.size,
  queueBatches:batches,nextQuestionIds:next,nextBatchId:next.length?slug(next):null,
  complete:processed.size===known.size&&queued.size===0
 };
}
