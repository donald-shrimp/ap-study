import {encodeWorkspaceBackup,decodeWorkspaceBackup} from './resources.js';
// The sole persisted question-record contract. UI projection is not an old-file reader.
const clone=v=>JSON.parse(JSON.stringify(v));
const keys=(v,allowed)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).every(k=>allowed.includes(k));
const id=v=>typeof v==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(v);
export function toRecord(a){
 const q=clone(a.questionSnapshot),correct=q.type==='multipleChoice'?q.correctChoiceIds:[q.correctChoiceId];
 delete q.answer;delete q.correctChoiceId;q.correctChoiceIds=correct;
 const selected=a.selectedChoiceIds??(a.selectedChoiceId?[a.selectedChoiceId]:[]);
 return {format:'hitomon-learning-record',version:2,id:a.id,qualificationId:a.qualificationId,examPartId:q.examPartId,kind:'question',questionId:a.questionId,questionVersion:a.questionVersion,contentRevision:a.contentRevision,material:q,lesson:clone(a.materialSnapshot),response:{choiceIds:clone(selected)},evaluation:a.completedAt?{source:'automatic',outcome:a.status,at:a.completedAt,hintsBeforeAnswer:a.hintsBeforeAnswer}:null,assistance:{hintCount:a.hintCount,hintEvents:clone(a.hintEvents),answerViewedBefore:a.answerViewedBefore},progress:{status:a.completedAt?'completed':a.status,confidence:a.confidence,scrollY:a.scrollY??0,readingNote:a.readingNote??'',topic:a.topic??null,...Object.fromEntries(['topicId','entryMode','practiceScope','deferred'].filter(k=>a[k]!==undefined).map(k=>[k,clone(a[k])]))},startedAt:a.startedAt,updatedAt:a.updatedAt,...Object.fromEntries(['continuationOf','continuedAt','importedFrom'].filter(k=>a[k]!==undefined).map(k=>[k,a[k]]))};
}
export function fromRecord(r){
 validateRecord(r);const q=clone(r.material);
 if(q.type==='singleChoice'){q.correctChoiceId=q.correctChoiceIds[0];q.answer=q.choices.findIndex(c=>c.id===q.correctChoiceId);delete q.correctChoiceIds;}else q.answer=null;
 const p=r.progress,a={id:r.id,qualificationId:r.qualificationId,questionId:r.questionId,questionVersion:r.questionVersion,contentRevision:r.contentRevision,questionSnapshot:q,materialSnapshot:clone(r.lesson),status:r.evaluation?.outcome||p.status,startedAt:r.startedAt,updatedAt:r.updatedAt,completedAt:r.evaluation?.at||null,hintsBeforeAnswer:r.evaluation?.hintsBeforeAnswer??null,selected:null,selectedChoiceId:null,...clone(r.assistance),...clone(p),...Object.fromEntries(['continuationOf','continuedAt','importedFrom'].filter(k=>r[k]!==undefined).map(k=>[k,r[k]]))};
 a.status=r.evaluation?.outcome||p.status;delete a.progress;
 if(q.type==='multipleChoice')a.selectedChoiceIds=clone(r.response.choiceIds);else if(r.response.choiceIds.length){a.selectedChoiceId=r.response.choiceIds[0];a.selected=q.choices.findIndex(c=>c.id===a.selectedChoiceId);}
 return a;
}
export function validateRecord(r){
 const fail=()=>{throw Error('新形式の学習記録を確認できません。旧形式は変換ツールで変換してください。');};
 if(!keys(r,['format','version','id','qualificationId','examPartId','kind','questionId','questionVersion','contentRevision','material','lesson','response','evaluation','assistance','progress','startedAt','updatedAt','continuationOf','continuedAt','importedFrom'])||r.format!=='hitomon-learning-record'||r.version!==2||r.kind!=='question'||![r.id,r.qualificationId,r.examPartId,r.questionId].every(id)||r.material?.id!==r.questionId||r.material.qualificationId!==r.qualificationId||r.material.examPartId!==r.examPartId||r.material.version!==r.questionVersion||!['singleChoice','multipleChoice'].includes(r.material.type)||'answer' in r.material||'correctChoiceId' in r.material)fail();
 const q=r.material,ids=q.choices?.map(c=>c.id),answer=q.correctChoiceIds,selected=r.response?.choiceIds;
 if(!Array.isArray(ids)||ids.length<2||ids.length>20||new Set(ids).size!==ids.length||!Array.isArray(answer)||!answer.length||new Set(answer).size!==answer.length||answer.some(v=>!ids.includes(v))||q.type==='singleChoice'&&answer.length!==1||!keys(r.response,['choiceIds'])||!Array.isArray(selected)||new Set(selected).size!==selected.length||selected.some(v=>!ids.includes(v))||q.type==='singleChoice'&&selected.length>1)fail();
 if(!keys(r.evaluation,['source','outcome','at','hintsBeforeAnswer'])&&r.evaluation!==null||r.evaluation&&(r.evaluation.source!=='automatic'||!['correct','assisted','incorrect','revealed'].includes(r.evaluation.outcome)||!Number.isFinite(Date.parse(r.evaluation.at))))fail();
 if(!r.progress||!['in_progress','postponed','completed'].includes(r.progress.status)||Boolean(r.evaluation)!==(r.progress.status==='completed')||!r.assistance||!r.lesson||!Number.isFinite(Date.parse(r.startedAt))||!Number.isFinite(Date.parse(r.updatedAt)))fail();
 const a=r.assistance,p=r.progress,e=r.evaluation;
 if(!keys(a,['hintCount','hintEvents','answerViewedBefore'])||typeof a.answerViewedBefore!=='boolean'||!Number.isInteger(a.hintCount)||a.hintCount<0||a.hintCount>20||!Array.isArray(a.hintEvents)||a.hintEvents.length!==a.hintCount||a.hintEvents.some((event,i)=>!keys(event,['step','at','phase'])||event.step!==i+1||!['before','after'].includes(event.phase)||!Number.isFinite(Date.parse(event.at)))||!Array.isArray(r.lesson.hints)||a.hintCount>r.lesson.hints.length)fail();
 if(!keys(p,['status','confidence','scrollY','readingNote','topic','topicId','entryMode','practiceScope','deferred'])||typeof p.confidence!=='boolean'||!Number.isFinite(p.scrollY)||p.scrollY<0||typeof p.readingNote!=='string'||p.readingNote.length>200||e&&(!Number.isInteger(e.hintsBeforeAnswer)||e.hintsBeforeAnswer<0||e.hintsBeforeAnswer>a.hintCount))fail();
 if(r.evaluation){const right=selected.length===answer.length&&selected.every(v=>answer.includes(v)),e=r.evaluation,s=r.assistance;if(e.outcome==='correct'&&(!right||e.hintsBeforeAnswer!==0||s.answerViewedBefore)||e.outcome==='assisted'&&(!right||e.hintsBeforeAnswer<1||s.answerViewedBefore)||e.outcome==='incorrect'&&(!selected.length||right||s.answerViewedBefore)||e.outcome==='revealed'&&!s.answerViewedBefore)fail();}
 return r;
}
export function encodeState(s){const {attempts,...rest}=s;return {...rest,format:'hitomon-study-state',version:2,records:attempts.map(toRecord),...(rest.workspaceBackup?{workspaceBackup:encodeWorkspaceBackup(rest.workspaceBackup)}:{})};}
export function decodeState(s){if(s?.format!=='hitomon-study-state'||s.version!==2||!Array.isArray(s.records))throw Error('新形式のバックアップではありません。');const {records,format,...rest}=s;return {...rest,attempts:records.map(fromRecord),...(rest.workspaceBackup?{workspaceBackup:decodeWorkspaceBackup(rest.workspaceBackup)}:{})};}
// Logged-in import adds verified v2 records without replacing account history.
export function mergeBackupState(current,incoming){
 const canonical=v=>JSON.stringify(v,(_,x)=>x&&typeof x==='object'&&!Array.isArray(x)?Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])):x);
 const records=new Map(current.attempts.map(a=>[a.id,a]));
 for(const a of incoming.attempts){const old=records.get(a.id);if(old&&canonical(toRecord(old))!==canonical(toRecord(a)))throw Error('同じIDの異なる学習記録があります。取り込み前の記録は保持しています。');if(!old)records.set(a.id,clone(a));}
 const overrides=clone(current.overrides);for(const [id,value] of Object.entries(incoming.overrides)){if(overrides[id]&&canonical(overrides[id])!==canonical(value))throw Error('教材編集の内容が競合しています。取り込み前の教材は保持しています。');overrides[id]=clone(value);}
 return {...(current.attempts.length?clone(current):clone(incoming)),attempts:[...records.values()],overrides,readingNotes:{...clone(incoming.readingNotes),...clone(current.readingNotes)}};
}
