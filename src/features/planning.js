import {createWorkspaceStore} from '../storage/workspace.js';
import {blankPlan,validatePlan,parsePlan,examPartsFor,studySummary,aiPrompt} from '../domain/planning.js';
import {selectDiagnostic,createDiagnostic,submitDiagnostic,finishDiagnostic,diagnosticAttempts,diagnosticResult,validateDiagnostic} from '../domain/diagnostic.js';
import {createPlanningViews} from '../ui/planning.js';

export function createPlanningFeature({qualification,rootPath,getStore,getState,getNavigation,content,base,validateAttempt,onUpdate,onNavigate,onNotice,onChanged,getReviewCount,download}){
 let workspace,documents=[],preview=null,previewRevision=0,jsonInput='',editingPhaseId=null,status='guest',generation=0,busy=false;
 const row=id=>documents.find(r=>r.id===id),plan=()=>row('planning')?.payload||blankPlan(qualification);
 const validate=(kind,payload)=>{if(kind==='planning')return validatePlan(payload,qualification);if(kind==='diagnostic')return validateDiagnostic(payload,qualification,validateAttempt);throw new Error('未対応の記録形式です。');};
 function allAttempts(){return [...getState().attempts,...documents.filter(r=>r.kind==='diagnostic').flatMap(r=>diagnosticAttempts(r.payload))];}
 const views=()=>createPlanningViews({qualification,documents,attempts:allAttempts(),currentRunId:getState().currentRunId,preview,jsonInput,editingPhaseId,workspaceStatus:status});
 async function bind(){const token=++generation,identity=await getStore().identity();await workspace?.close();if(token!==generation)return;workspace=createWorkspaceStore({...identity,rootPath,validate});try{documents=(await workspace.read()).filter(r=>{try{validate(r.kind,r.payload);return true;}catch{onNotice('計画・診断の保存データを読み取れません。通常学習は利用できます。');return false;}});}catch{documents=[];onNotice('計画・診断を保存できません。通常学習は利用できます。');}if(workspace.error())onNotice('計画・診断の保存データを読み取れません。通常学習は利用できます。');preview=null;jsonInput='';editingPhaseId=null;status=identity.owner.startsWith('uid:')?'pending':'guest';onUpdate();}
 async function write(kind,id,payload,revision){const token=generation,target=workspace;await target.write(kind,id,payload,revision);if(token!==generation)return;documents=await target.read();onChanged();onUpdate();}
 function summary(){return studySummary({qualification,plan:row('planning')?plan():null,attempts:allAttempts(),diagnostics:documents.filter(r=>r.kind==='diagnostic'&&r.payload.status!=='in_progress').map(r=>diagnosticResult(r.payload,qualification)),reviewCount:getReviewCount()});}
 async function copy(text){try{await navigator.clipboard.writeText(text);onNotice('コピーしました。');}catch{
  let dialog=document.getElementById('copy-dialog');if(!dialog){dialog=document.createElement('dialog');dialog.id='copy-dialog';dialog.setAttribute('aria-label','コピーするテキスト');dialog.innerHTML='<form method="dialog"><div class="dialog-head"><h2>テキストをコピー</h2><button class="button secondary">閉じる</button></div></form><p class="small">下のテキストを選択してコピーしてください。</p><textarea rows="12" readonly aria-label="コピーする内容"></textarea><button type="button" class="button secondary select-copy">全選択</button>';document.body.append(dialog);dialog.querySelector('.select-copy').onclick=()=>dialog.querySelector('textarea').select();}dialog.querySelector('textarea').value=text;dialog.showModal();
 }}
 async function cacheImages(questions){
  const urls=[...new Set(questions.flatMap(q=>[...(q.sourceImages||[]),q.image,...q.choices.map(c=>c.image)].filter(Boolean)))],cache=await globalThis.caches?.open(`hitomon-${rootPath}images`),pending=[...urls];
  await Promise.all(Array.from({length:Math.min(6,pending.length)},async()=>{while(pending.length){const url=pending.shift();if(await cache?.match(url))continue;const response=await fetch(url);if(!response.ok)throw new Error('診断の問題画像を準備できませんでした。接続を確認してください。');await cache?.put(url,response);}}));
 }
 async function startDiagnostic(){
  if(!navigator.onLine)throw new Error('新しい診断はオンラインで始めてください。中断した診断や通常学習はオフラインでも使えます。');
  const token=generation,nav=getNavigation();onNotice('診断の30問を準備しています。');
  const chosen=selectDiagnostic(base,qualification,allAttempts());await Promise.all(chosen.map(q=>content.ensure(q.id)));if(token!==generation||nav!==getNavigation())return;
  await cacheImages(chosen);if(token!==generation||nav!==getNavigation())return;
  const run=createDiagnostic(chosen,qualification,allAttempts(),content.manifest.index.sha256);await write('diagnostic',run.id,run,0);if(token!==generation||nav!==getNavigation())return;onNotice('');onNavigate('diagnostic',run.id);
 }
 async function action(el){
  const action=el.dataset.action,known=['reload-planning','copy-prompt','copy-summary','export-summary','export-plan','preview-plan','register-plan','edit-phase','cancel-phase','delete-phase','start-diagnostic','resume-diagnostic','pause-diagnostic','submit-diagnostic','skip-diagnostic','end-diagnostic','diagnostic-zoom','workspace-local','workspace-remote','workspace-copy-run','export-diagnostics'];
  if(!known.includes(action))return false;if(busy)return true;busy=true;
  try{
   if(action==='reload-planning'){editingPhaseId=null;preview=null;onUpdate();}
   else if(action==='copy-prompt')await copy(aiPrompt(qualification,summary()));
   else if(action==='copy-summary')await copy(JSON.stringify(summary(),null,2));
   else if(action==='export-summary')download(summary(),`${qualification.id}-study-summary.json`);
   else if(action==='export-plan')download(plan(),`${qualification.id}-study-plan.json`);
   else if(action==='export-diagnostics')download({format:'hitomon-diagnostics',version:1,qualificationId:qualification.id,runs:documents.filter(r=>r.kind==='diagnostic').map(r=>r.payload)},`${qualification.id}-diagnostics.json`);
   else if(action==='preview-plan'){preview=parsePlan(jsonInput,qualification);previewRevision=row('planning')?.localRevision||0;onUpdate();document.getElementById('plan-preview').scrollIntoView({block:'start'});onNotice('検証できました。登録後の内容を確認してください。');}
   else if(action==='register-plan'){if(!preview)throw new Error('先に計画を検証してください。');await write('planning','planning',preview,previewRevision);preview=null;jsonInput='';onUpdate();onNotice('受験日と計画を登録しました。');}
   else if(action==='edit-phase'){editingPhaseId=el.dataset.id;onUpdate();document.getElementById('phase-form').scrollIntoView({block:'start'});}
   else if(action==='cancel-phase'){editingPhaseId=null;onUpdate();}
   else if(action==='delete-phase'){const next=structuredClone(plan());next.phases=next.phases.filter(p=>p.id!==el.dataset.id);await write('planning','planning',next,Number(el.dataset.revision));editingPhaseId=null;}
   else if(action==='start-diagnostic')await startDiagnostic();
   else if(action==='resume-diagnostic'){const run=row(el.dataset.id)?.payload;if(!run)throw new Error('診断を見つけられません。');onNavigate('diagnostic',run.id);if(run.status==='in_progress'&&navigator.onLine){const token=generation;cacheImages(run.slots.map(s=>s.attempt.questionSnapshot)).then(()=>{if(token===generation)onNotice('診断の画像を保存しました。オフラインでも続けられます。');}).catch(()=>{if(token===generation)onNotice('未保存の診断画像があります。オフラインにする前に接続を確認してください。');});}}
   else if(action==='pause-diagnostic')onNavigate('home');
   else if(action==='workspace-copy-run'){const original=row(el.dataset.id);if(!original?.conflict)throw new Error('競合している診断がありません。');const run=structuredClone(original.payload),mapping=new Map(run.slots.map(s=>[s.id,crypto.randomUUID()]));run.id=crypto.randomUUID();run.slots.forEach(s=>s.id=mapping.get(s.id));run.responses=Object.fromEntries(Object.entries(run.responses).map(([id,value])=>[mapping.get(id),value]));await write('diagnostic',run.id,run,0);await workspace.resolve(original.id,false);documents=await workspace.read();onChanged();onNavigate('diagnostic',run.id);}
   else if(action==='workspace-local'||action==='workspace-remote'){await workspace.resolve(el.dataset.id,action==='workspace-local');documents=await workspace.read();onChanged();onUpdate();}
   else if(action==='diagnostic-zoom'){
    const q=row(getState().currentRunId)?.payload.slots[row(getState().currentRunId).payload.currentIndex].attempt.questionSnapshot,src=q?.sourceImages[Number(el.dataset.index)];if(!src)throw new Error('問題画像がありません。');
    const image=document.createElement('img');image.src=src;image.alt=q.imageAlt||q.title;image.style.width=Math.max(900,q.imageSizes[Number(el.dataset.index)].width)+'px';document.getElementById('image-scroll').replaceChildren(image);document.getElementById('image-title').textContent=q.title;document.getElementById('image-dialog').showModal();
   }else{
    const original=row(getState().currentRunId);if(!original)throw new Error('診断を見つけられません。');const run=structuredClone(original.payload);
    if(action==='end-diagnostic'){if(!confirm('ここまでで診断を終了して結果を表示します。結果を見た後は、この診断を再開できません。終了しますか？'))return true;finishDiagnostic(run);}
    else submitDiagnostic(run,action==='skip-diagnostic'?null:run.currentChoiceId);
    await write('diagnostic',run.id,run,original.localRevision);onNavigate('diagnostic',run.id);
   }
  }catch(error){onNotice(error.message);}finally{busy=false;}
  return true;
 }
 function input(el){if(el.id!=='plan-json')return false;jsonInput=el.value;preview=null;const output=document.getElementById('plan-preview');if(output)output.innerHTML='';return true;}
 async function change(el){
  if(el.name==='diagnostic-answer'){
   if(busy)return true;busy=true;const submitButton=document.querySelector('[data-action=submit-diagnostic]');if(submitButton)submitButton.disabled=true;try{const original=row(getState().currentRunId);if(!original||original.payload.status!=='in_progress')throw new Error('診断は終了しています。');const run=structuredClone(original.payload);run.currentChoiceId=el.value;await write('diagnostic',run.id,run,original.localRevision);}catch(error){onNotice(error.message);onUpdate();}finally{busy=false;}return true;
  }
  if(el.id==='import-diagnostics'){
   const file=el.files[0];if(!file)return true;
   try{if(file.size>64*1024*1024)throw new Error('診断バックアップは64MB以内にしてください。');const value=JSON.parse(await file.text());if(value.format!=='hitomon-diagnostics'||value.version!==1||value.qualificationId!==qualification.id||!Array.isArray(value.runs)||value.runs.length>100)throw new Error('この資格の診断バックアップではありません。');const candidates=value.runs.map(r=>validate('diagnostic',r));if(new Set(candidates.map(r=>r.id)).size!==candidates.length)throw new Error('診断IDが重複しています。');for(const run of candidates)if(row(run.id)&&JSON.stringify(row(run.id).payload)!==JSON.stringify(run))throw new Error('同じIDの異なる診断があります。既存の診断は変更していません。');if(!confirm(`${candidates.length}件の診断を追加します。既存の学習記録は変更しません。取り込みますか？`))return true;for(const run of candidates)if(!row(run.id))await write('diagnostic',run.id,run,0);onNotice('診断を取り込みました。');}catch(error){onNotice(error.message);}finally{el.value='';}return true;
  }
  return false;
 }
 async function submit(form){
  if(!['exam-form','phase-form'].includes(form.id))return false;
  if(busy)return true;busy=true;
  try{const fields=new FormData(form),next=structuredClone(plan());
   if(form.id==='exam-form')next.examDates=examPartsFor(qualification).map(p=>({examPartId:p.id,date:String(fields.get('exam-'+p.id)||'')})).filter(d=>d.date);
   else{const phase={id:form.dataset.id||'phase-'+crypto.randomUUID(),name:String(fields.get('name')).trim(),start:String(fields.get('start')),end:String(fields.get('end')),examPartIds:fields.getAll('part').map(String),targets:{completedAttempts:Number(fields.get('target'))},focusTopicIds:fields.getAll('topic').map(String)};next.phases=[...next.phases.filter(p=>p.id!==phase.id),phase].sort((a,b)=>a.start.localeCompare(b.start));}
   await write('planning','planning',next,Number(form.dataset.revision));editingPhaseId=null;onUpdate();onNotice(form.id==='exam-form'?'受験日を保存しました。':'フェーズを保存しました。');
  }catch(error){onNotice(error.message);}finally{busy=false;}return true;
 }
 async function importGuest(uid,deviceId){
  const guest=createWorkspaceStore({owner:`guest:${deviceId}`,deviceId,qualificationId:qualification.id,rootPath,validate});
  try{const rows=await guest.read();if(!rows.length)return;if(!confirm(`ログイン前の受験日・計画と診断${rows.filter(r=>r.kind==='diagnostic').length}件を追加します。元の記録は残します。取り込みますか？`))return;
   for(const original of rows){if(original.kind==='planning'){if(!row('planning'))await write('planning','planning',original.payload,0);else onNotice('アカウントに計画があるため、ゲスト計画は元の保存領域に残しました。JSONで確認して登録できます。');}else if(!row(original.id))await write('diagnostic',original.id,original.payload,0);}
  }finally{await guest.close();}
 }
 const backup=()=>({format:'hitomon-workspace-backup',version:1,qualificationId:qualification.id,plan:row('planning')?.payload||null,runs:documents.filter(r=>r.kind==='diagnostic').map(r=>r.payload)});
 function validateBackup(value){if(value===undefined)return;if(!value||value.format!=='hitomon-workspace-backup'||value.version!==1||value.qualificationId!==qualification.id||!Array.isArray(value.runs)||value.runs.length>1000)throw new Error('受験日・計画・診断のバックアップを確認できません。記録は変更していません。');if(value.plan)validate('planning',value.plan);const ids=new Set();for(const run of value.runs){validate('diagnostic',run);if(ids.has(run.id))throw new Error('診断IDが重複しています。');ids.add(run.id);if(row(run.id)&&JSON.stringify(row(run.id).payload)!==JSON.stringify(run))throw new Error('同じIDの異なる診断があります。既存の記録は変更していません。');}}
 async function restoreBackup(value){if(!value)return;validateBackup(value);if(value.plan&&!row('planning'))await write('planning','planning',value.plan,0);for(const run of value.runs)if(!row(run.id))await write('diagnostic',run.id,run,0);}
 async function clearDiagnostics(){await workspace.clearDiagnostics();documents=await workspace.read();onUpdate();}
 return {bind,views,allAttempts,action,input,change,submit,summary,importGuest,backup,validateBackup,restoreBackup,clearDiagnostics,store:()=>workspace,derivedRun:id=>documents.find(r=>r.kind==='diagnostic'&&r.payload.slots.some(s=>s.id===id))?.id,onDocuments:rows=>{if(rows.some(r=>r.owner!==workspace.identity().owner))return;const changed=JSON.stringify(rows.map(r=>[r.id,r.localRevision,r.payload,r.conflict]))!==JSON.stringify(documents.map(r=>[r.id,r.localRevision,r.payload,r.conflict]));documents=rows;if(getState().view==='planning'){const conflicts=document.getElementById('workspace-conflicts');if(conflicts)conflicts.innerHTML=views().conflictsHTML();if(changed){const stale=document.getElementById('planning-stale');if(stale)stale.hidden=false;}onUpdate({preserveForm:true});}else if(changed)onUpdate();},onStatus:kind=>{status=kind;const markup=views().statusHTML();document.querySelectorAll('.workspace-status').forEach(el=>el.outerHTML=markup);const settingsStatus=document.getElementById('workspace-sync-state');if(settingsStatus)settingsStatus.innerHTML=markup;},refresh:()=>onUpdate()};
}
