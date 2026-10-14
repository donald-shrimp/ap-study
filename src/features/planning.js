import {encodeResource,decodeResource} from '../v2/resources.js';
import {chooseAssessment} from '../domain/assessment.js';
import {canUseQuestion} from '../domain/content-policy.js';
import {setSyncStatus,workspaceStatusHTML} from '../ui/sync-status.js';
import {planRevisionHTML} from '../ui/plan-history.js';
import {createPlanRevision,validatePlanRevision,canonical} from '../domain/plan-history.js';
import {createMock,validateMock,mockResult} from '../domain/mock.js';
import {createWorkspaceStore,MAX_WORKSPACE_BYTES} from '../storage/workspace.js';
import {createPlanningDrafts} from '../ui/planning-drafts.js';
import {blankPlan,validatePlan,parsePlan,examPartsFor,studySummary,aiPrompt,CONTEXT_FIELDS,dateInZone,goalUnit} from '../domain/planning.js';
import {selectDiagnostic,createDiagnostic,submitDiagnostic,finishDiagnostic,diagnosticAttempts,diagnosticExposure,diagnosticResult,validateDiagnostic} from '../domain/diagnostic.js';
import {createPlanningViews} from '../ui/planning.js';
import {canStartDiagnostic} from '../domain/qualification-features.js';
import {diagnosticSize} from '../domain/assessment-policy.js';

export function createPlanningFeature({qualification,rootPath,getStore,getState,getNavigation,content,base,validateAttempt,onUpdate,onNavigate,onNotice,onChanged,getReviewCount,download,getTargetPart=()=>null,getCaseRuns=()=>[]}){
 let workspace,documents=[],preview=null,previewRevision=0,jsonInput='',editingPhaseId=null,editingWeek=null,editingMilestone=null,editorOpen=false,aiOpen=false,status='guest',generation=0,busy=false,stale=false;
 function setBusy(value){
  busy=value;
  const controls=document.querySelectorAll('[name="diagnostic-answer"], [data-action="submit-diagnostic"], [data-action="skip-diagnostic"], [data-action="end-diagnostic"], [data-action="pause-diagnostic"]');
  for(const control of controls){
   if(value&&!control.disabled){control.dataset.saveBusy='true';control.disabled=true;}
   else if(!value&&control.dataset.saveBusy){delete control.dataset.saveBusy;control.disabled=false;}
  }
 }
 const row=id=>documents.find(r=>r.id===id),plan=()=>row('planning')?.payload||blankPlan(qualification);
 const validate=(kind,payload)=>{if(kind==='planRevision')return validatePlanRevision(payload,qualification);if(kind==='planning')return validatePlan(payload,qualification);if(kind==='diagnostic')return validateDiagnostic(payload,qualification,validateAttempt);if(kind==='mock')return validateMock(payload,qualification,validateAttempt);throw new Error('未対応の記録形式です。');};
 function assessmentAttempts(){return [...getState().attempts,...documents.filter(r=>r.kind==='diagnostic').flatMap(r=>diagnosticAttempts(r.payload))];}
 function allAttempts(){return assessmentAttempts().filter(a=>canUseQuestion(a.questionSnapshot,'practice'));}
 const drafts=createPlanningDrafts(()=>getState().view==='planning');
 const views=()=>{drafts.capture();return createPlanningViews({qualification,documents,attempts:allAttempts(),summaryData:summary(),currentRunId:getState().currentRunId,currentMockSetId:getState().currentMockSetId,diagnosticEnabled:canStartDiagnostic(qualification,base),practiceQuestionIds:new Set(base.map(q=>q.id)),practiceTopicIds:new Set(base.filter(q=>canUseQuestion(q,'practice')).map(q=>q.topicId)),preview,jsonInput,editingPhaseId,editingWeek,editingMilestone,workspaceStatus:status,editorOpen,aiOpen,stale,targetPartId:getTargetPart(),caseRuns:getCaseRuns()});};
 // Preserve actual drafts, rather than freezing every open planning page.
 function hasPlanningDraft(){
  if(drafts.has()||preview||jsonInput.trim()||editingPhaseId||editingWeek||editingMilestone)return true;
  if(getState().view!=='planning')return false;
  return [...document.querySelectorAll('#main form input, #main form textarea, #main form select')].some(el=>{
   if(el.tagName==='SELECT')return [...el.options].some(option=>option.selected!==option.defaultSelected);
   if(['checkbox','radio'].includes(el.type))return el.checked!==el.defaultChecked;
   if(['submit','button','file','hidden'].includes(el.type))return false;
   return el.value!==el.defaultValue;
  });
 }
 function phaseIn(next,id){const phase=next.phases.find(p=>p.id===id);if(!phase)throw new Error('フェーズが更新されています。計画を開き直してください。');return phase;}
 async function bind(){document.getElementById('plan-revision-dialog')?.remove();const token=++generation,identity=await getStore().identity();await workspace?.close();if(token!==generation)return;workspace=createWorkspaceStore({...identity,rootPath,validate,planHistory:{canonical,create:(plan,options)=>createPlanRevision(plan,qualification,options)}});try{documents=(await workspace.read()).filter(r=>{try{validate(r.kind,r.payload);return true;}catch{onNotice('計画・診断・模試の保存データを読み取れません。通常学習は利用できます。');return false;}});}catch{documents=[];onNotice('計画・診断・模試を保存できません。通常学習は利用できます。');}if(workspace.error())onNotice('計画・診断・模試の保存データを読み取れません。通常学習は利用できます。');drafts.reset();stale=false;preview=null;jsonInput='';editingPhaseId=null;editingWeek=null;editingMilestone=null;editorOpen=false;aiOpen=false;status=identity.owner.startsWith('uid:')?'pending':'guest';onUpdate();}
 async function write(kind,id,payload,revision,{clearForm=null,discardDrafts=false,historyOrigin='edited'}={}){if(!workspace)throw new Error('このブラウザでは計画・診断・模試の記録を保存できません。通常演習は続けられます。');const token=generation,target=workspace,previousRevision=row('planning')?.localRevision||0;drafts.capture();const written=await target.write(kind,id,payload,revision,{historyOrigin});if(token!==generation)return;documents=await target.read();if(kind==='planning')drafts.advance(previousRevision,written.localRevision);if(discardDrafts){drafts.reset();stale=false;}else if(clearForm)drafts.clear(clearForm);onChanged();onUpdate();if(busy)setBusy(true);}
 function summary(){const result=studySummary({qualification,plan:row('planning')?plan():null,attempts:allAttempts(),diagnostics:documents.filter(r=>r.kind==='diagnostic'&&r.payload.status!=='in_progress').map(r=>diagnosticResult(r.payload,qualification)),reviewCount:getReviewCount(),caseRuns:getCaseRuns()});result.mockExams=documents.filter(r=>r.kind==='mock'&&r.payload.status!=='in_progress').map(r=>mockResult(r.payload,qualification));return result;}
 async function copy(text){try{await navigator.clipboard.writeText(text);onNotice('コピーしました。');}catch{
  let dialog=document.getElementById('copy-dialog');if(!dialog){dialog=document.createElement('dialog');dialog.id='copy-dialog';dialog.setAttribute('aria-label','コピーするテキスト');dialog.innerHTML='<form method="dialog"><div class="dialog-head"><h2>テキストをコピー</h2><button class="button secondary">閉じる</button></div></form><p class="small">下のテキストを選択してコピーしてください。</p><textarea rows="12" readonly aria-label="コピーする内容"></textarea><button type="button" class="button secondary select-copy">全選択</button>';document.body.append(dialog);dialog.querySelector('.select-copy').onclick=()=>dialog.querySelector('textarea').select();}dialog.querySelector('textarea').value=text;dialog.showModal();
 }}
 async function cacheImages(questions){
  const urls=[...new Set(questions.flatMap(q=>[...(q.sourceImages||[]),q.image,...q.choices.map(c=>c.image)].filter(Boolean)))],cache=await globalThis.caches?.open(`hitomon-${rootPath}images`),pending=[...urls];
  await Promise.all(Array.from({length:Math.min(6,pending.length)},async()=>{while(pending.length){const url=pending.shift();if(await cache?.match(url))continue;const response=await fetch(url);if(!response.ok)throw new Error('診断の問題画像を準備できませんでした。接続を確認してください。');await cache?.put(url,response);}}));
 }
 async function startDiagnostic(){
  if(!canStartDiagnostic(qualification,base))throw new Error('この資格の診断はまだ利用できません。通常学習は利用できます。');
  if(!navigator.onLine)throw new Error('新しい診断はオンラインで始めてください。中断した診断や通常学習はオフラインでも使えます。');
  const token=generation,nav=getNavigation();onNotice(`診断の${diagnosticSize(qualification)}問を準備しています。`);
  const variants=await content.loadAssessments();if(token!==generation||nav!==getNavigation())return;
  const attempts=[...assessmentAttempts(),...documents.filter(r=>['diagnostic','mock'].includes(r.kind)).flatMap(r=>diagnosticExposure(r.payload))],chosen=selectDiagnostic(base,qualification,attempts,Math.random,variants);await Promise.all(chosen.filter(q=>canUseQuestion(q,'practice')).map(q=>content.ensure(q.id)));if(token!==generation||nav!==getNavigation())return;
  await cacheImages(chosen);if(token!==generation||nav!==getNavigation())return;
  const revision=[content.manifest.index.sha256,content.manifest.assessment?.sha256||''].filter(Boolean).join(':');
  const run=createDiagnostic(chosen,qualification,attempts,revision);await write('diagnostic',run.id,run,0);if(token!==generation||nav!==getNavigation())return;onNotice('');onNavigate('diagnostic',run.id);
 }
 async function startMock(setId){
  const ongoing=documents.some(r=>r.kind==='mock'&&r.payload.mockSet.id===setId&&r.payload.status==='in_progress');
  if(ongoing&&!confirm('同じ模試が中断中です。中断した回は残して、新しい回を始めますか？'))return;
  if(!navigator.onLine)throw new Error('新しい模試はオンラインで始めてください。中断した模試はオフラインで続けられます。');
  const token=generation,nav=getNavigation();onNotice('模試の問題を準備しています。');
  const [sets,variants]=await Promise.all([content.loadMockSets(),content.loadAssessments()]);if(token!==generation||nav!==getNavigation())return;
  const set=sets.find(s=>s.id===setId),exposure=[...assessmentAttempts(),...documents.filter(r=>['diagnostic','mock'].includes(r.kind)).flatMap(r=>diagnosticExposure(r.payload))];
  if(!set)throw new Error('この模試は現在の教材にありません。');
  const byId=new Map(variants.map(q=>[q.id,q]));
  const fixed=await Promise.all(set.slots.map(slot=>byId.get(slot.questionId)||content.ensure(slot.questionId)));
  if(token!==generation||nav!==getNavigation())return;
  const run=createMock(set,fixed,qualification,exposure,[content.manifest.mockSets.sha256,content.manifest.assessment?.sha256||content.manifest.index.sha256].join(':'));
  await cacheImages(run.slots.map(s=>s.attempt.questionSnapshot));if(token!==generation||nav!==getNavigation())return;
  await write('mock',run.id,run,0);if(token!==generation||nav!==getNavigation())return;onNotice('');onNavigate('diagnostic',run.id);
 }

 async function action(el){
  const action=el.dataset.action,known=['view-plan-revision','open-editor','open-ai','reload-planning','copy-prompt','copy-summary','export-summary','export-plan','preview-plan','register-plan','edit-phase','cancel-phase','delete-phase','edit-week','cancel-week','delete-week','edit-milestone','cancel-milestone','delete-milestone','toggle-milestone','start-diagnostic','start-mock','mock-records','mock-history','resume-diagnostic','pause-diagnostic','submit-diagnostic','skip-diagnostic','end-diagnostic','diagnostic-zoom','workspace-local','workspace-remote','workspace-copy-run','export-diagnostics'];
  if(!known.includes(action))return false;if(busy)return true;setBusy(true);
  try{
   if(action==='view-plan-revision'){const revision=row(el.dataset.id);if(revision?.kind!=='planRevision')throw new Error('計画履歴を見つけられません。');let dialog=document.getElementById('plan-revision-dialog');if(!dialog){dialog=document.createElement('dialog');dialog.id='plan-revision-dialog';dialog.setAttribute('aria-labelledby','plan-revision-title');document.body.append(dialog);}dialog.innerHTML='<div class="dialog-head"><h2 id="plan-revision-title">保存した計画</h2><button class="button secondary history-close">閉じる</button></div>'+planRevisionHTML(revision.payload,qualification,allAttempts(),getCaseRuns())+'<button class="button secondary history-export">この計画を書き出す</button>';dialog.querySelector('.history-close').onclick=()=>dialog.close();dialog.querySelector('.history-export').onclick=()=>download(revision.payload.plan,qualification.id+'-plan-'+revision.id+'.json');dialog.showModal();}
   else if(action==='open-editor'||action==='open-ai'){if(action==='open-editor')editorOpen=true;else aiOpen=true;onUpdate();document.getElementById(action==='open-editor'?'plan-editor':'plan-ai')?.scrollIntoView({block:'start'});}
   else if(action==='reload-planning'){drafts.reset();stale=false;editingPhaseId=null;editingWeek=null;editingMilestone=null;preview=null;previewRevision=0;jsonInput='';onUpdate();}
   else if(action==='copy-prompt')await copy(aiPrompt(qualification,summary()));
   else if(action==='copy-summary')await copy(JSON.stringify(summary(),null,2));
   else if(action==='export-summary')download(summary(),`${qualification.id}-study-summary.json`);
   else if(action==='export-plan')download(plan(),`${qualification.id}-study-plan.json`);
   else if(action==='export-diagnostics')download({format:'hitomon-diagnostics',version:2,qualificationId:qualification.id,runs:documents.filter(r=>r.kind==='diagnostic').map(r=>encodeResource('diagnostic',r.payload))},`${qualification.id}-diagnostics.json`);
   else if(action==='preview-plan'){preview=parsePlan(jsonInput,qualification);const retained=!Object.hasOwn(preview,'context')&&plan().context!==undefined;if(retained)preview.context=structuredClone(plan().context);previewRevision=row('planning')?.localRevision||0;onUpdate();document.getElementById('plan-preview').scrollIntoView({block:'start'});onNotice(retained?'検証できました。JSONに前提がないため、現在の前提を引き継ぎます。登録後の内容を確認してください。':'検証できました。登録後の内容を確認してください。');}
   else if(action==='register-plan'){if(!preview)throw new Error('先に計画を検証してください。');await write('planning','planning',preview,previewRevision,{discardDrafts:true,historyOrigin:'imported'});preview=null;jsonInput='';onUpdate();onNotice('受験日と計画を登録しました。');}
   else if(action==='edit-phase'){editingPhaseId=el.dataset.id;onUpdate();document.getElementById('phase-form').scrollIntoView({block:'start'});}
   else if(action==='cancel-phase'){drafts.clear(document.getElementById('phase-form'));editingPhaseId=null;onUpdate();}
   else if(action==='edit-week'||action==='edit-milestone'){const selected={phaseId:el.dataset.phase,id:el.dataset.id};if(action==='edit-week')editingWeek=selected;else editingMilestone=selected;onUpdate();document.querySelector(`form[data-planning-form="${action==='edit-week'?'week':'milestone'}"][data-phase="${selected.phaseId}"]`).scrollIntoView({block:'center'});}
   else if(action==='cancel-week'||action==='cancel-milestone'){drafts.clear(document.querySelector(`form[data-planning-form="${action==='cancel-week'?'week':'milestone'}"][data-phase="${(action==='cancel-week'?editingWeek:editingMilestone)?.phaseId}"]`));if(action==='cancel-week')editingWeek=null;else editingMilestone=null;onUpdate();}
   else if(['delete-week','delete-milestone','toggle-milestone'].includes(action)){
    const next=structuredClone(plan()),phase=phaseIn(next,el.dataset.phase);
    if(action==='delete-week')phase.weeklyTargets=(phase.weeklyTargets||[]).filter(w=>w.id!==el.dataset.id);
    else if(action==='delete-milestone')phase.milestones=(phase.milestones||[]).filter(m=>m.id!==el.dataset.id);
    else{const milestone=phase.milestones?.find(m=>m.id===el.dataset.id);if(!milestone)throw new Error('予定が更新されています。計画を開き直してください。');milestone.completed=!milestone.completed;}
    await write('planning','planning',next,Number(el.dataset.revision));editingWeek=null;editingMilestone=null;onUpdate();onNotice(action==='toggle-milestone'?'予定の完了状態を保存しました。':'目標・予定を削除しました。');
   }
   else if(action==='delete-phase'){const next=structuredClone(plan());next.phases=next.phases.filter(p=>p.id!==el.dataset.id);await write('planning','planning',next,Number(el.dataset.revision));editingPhaseId=null;}
   else if(action==='start-diagnostic')await startDiagnostic();
   else if(action==='start-mock')await startMock(el.dataset.set);
   else if(action==='mock-records')onNavigate('mock-records',el.dataset.set);
   else if(action==='mock-history')onNavigate('history-mock');
   else if(action==='resume-diagnostic'){const run=row(el.dataset.id)?.payload;if(!run)throw new Error('診断を見つけられません。');onNavigate('diagnostic',run.id);if(run.status==='in_progress'&&navigator.onLine){const token=generation;cacheImages(run.slots.map(s=>s.attempt.questionSnapshot)).catch(()=>{if(token===generation)onNotice('未保存の診断画像があります。オフラインにする前に接続を確認してください。');});}}
   else if(action==='pause-diagnostic')onNavigate('home');
   else if(action==='workspace-copy-run'){const original=row(el.dataset.id);if(!original?.conflict)throw new Error('競合している診断がありません。');const run=structuredClone(original.payload),mapping=new Map(run.slots.map(s=>[s.id,crypto.randomUUID()]));run.id=crypto.randomUUID();run.slots.forEach(s=>s.id=mapping.get(s.id));run.responses=Object.fromEntries(Object.entries(run.responses).map(([id,value])=>[mapping.get(id),value]));await write(original.kind,run.id,run,0);await workspace.resolve(original.id,false);documents=await workspace.read();onChanged();onNavigate('diagnostic',run.id);}
   else if(action==='workspace-local'||action==='workspace-remote'){await workspace.resolve(el.dataset.id,action==='workspace-local');documents=await workspace.read();onChanged();onUpdate();}
   else if(action==='diagnostic-zoom'){
    const activeRun=row(getState().currentRunId)?.payload,q=activeRun?.slots[activeRun.currentIndex].attempt.questionSnapshot,isFigure=el.dataset.index==='figure',index=Number(el.dataset.index),src=isFigure?q?.image:q?.sourceImages[index];if(!src)throw new Error('問題画像がありません。');
    const image=document.createElement('img');image.src=src;image.alt=q.imageAlt||q.title;image.style.width=Math.max(900,isFigure?el.querySelector('img').naturalWidth:q.imageSizes?.[index]?.width||900)+'px';document.getElementById('image-scroll').replaceChildren(image);document.getElementById('image-title').textContent=q.title;document.getElementById('image-dialog').showModal();document.getElementById('image-scroll').scrollTo(0,0);
   }else{
    const original=row(getState().currentRunId);if(!original)throw new Error('診断を見つけられません。');const run=structuredClone(original.payload);
    if(action==='end-diagnostic'){if(!confirm(`ここまでで${run.mode==='mock'?'模試':'診断'}を終了して結果を表示します。結果を見た後は、この回を再開できません。終了しますか？`))return true;finishDiagnostic(run);}
    else submitDiagnostic(run,action==='skip-diagnostic'?null:run.currentChoiceId);
    await write(original.kind,run.id,run,original.localRevision);onNavigate('diagnostic',run.id);
   }
  }catch(error){onNotice(error.message);}finally{setBusy(false);}
  return true;
 }
 function input(el){if(el.id!=='plan-json'){if(getState().view==='planning'&&el.closest('form')){drafts.capture();return true;}return false;}jsonInput=el.value;preview=null;const output=document.getElementById('plan-preview');if(output)output.innerHTML='';return true;}
 async function change(el){
  if(getState().view==='planning'&&el.closest('form')){drafts.capture();return true;}
  if(el.name==='diagnostic-answer'){
   if(busy)return true;setBusy(true);try{const original=row(getState().currentRunId);if(!original||original.payload.status!=='in_progress')throw new Error('この回は終了しています。');const run=structuredClone(original.payload);chooseAssessment(run,el.value,el.checked);await write(original.kind,run.id,run,original.localRevision);}catch(error){onNotice(error.message);onUpdate();}finally{setBusy(false);}return true;
  }
  if(el.id==='import-diagnostics'){
   const file=el.files[0];if(!file)return true;
   try{if(file.size>64*1024*1024)throw new Error('診断バックアップは64MB以内にしてください。');const value=JSON.parse(await file.text());if(value.format!=='hitomon-diagnostics'||value.version!==2||value.qualificationId!==qualification.id||!Array.isArray(value.runs)||value.runs.length>100)throw new Error('この資格の診断バックアップではありません。');const candidates=value.runs.map(r=>validate('diagnostic',decodeResource('diagnostic',r)));if(new Set(candidates.map(r=>r.id)).size!==candidates.length)throw new Error('診断IDが重複しています。');for(const run of candidates)if(row(run.id)&&JSON.stringify(row(run.id).payload)!==JSON.stringify(run))throw new Error('同じIDの異なる診断があります。既存の診断は変更していません。');if(!confirm(`${candidates.length}件の診断を追加します。既存の学習記録は変更しません。取り込みますか？`))return true;for(const run of candidates)if(!row(run.id))await write('diagnostic',run.id,run,0);onNotice('診断を取り込みました。');}catch(error){onNotice(error.message);}finally{el.value='';}return true;
  }
  return false;
 }
 async function submit(form){
  if(!['exam-form','phase-form'].includes(form.id)&&!['week','milestone','context'].includes(form.dataset.planningForm))return false;
  if(busy)return true;setBusy(true);
  try{const fields=new FormData(form),next=structuredClone(plan());
   if(form.id==='exam-form')next.examDates=examPartsFor(qualification).map(p=>({examPartId:p.id,date:String(fields.get('exam-'+p.id)||'')})).filter(d=>d.date);
   else if(form.dataset.planningForm==='context'){const context=Object.fromEntries(CONTEXT_FIELDS.map(([id])=>[id,String(fields.get(id)||'').trim()]).filter(([,v])=>v));const minutes=String(fields.get('weeklyMinutes')||'').trim();if(minutes!=='')context.weeklyMinutes=Number(minutes);if(Object.keys(context).length)context.updatedOn=dateInZone(new Date(),next.timeZone);next.context=context;}
   else if(form.dataset.planningForm==='week'){const phase=phaseIn(next,form.dataset.phase),week={id:form.dataset.id||'week-'+crypto.randomUUID(),start:String(fields.get('start')),end:String(fields.get('end')),goals:examPartsFor(qualification).map(p=>({examPartId:p.id,unit:goalUnit(qualification,p.id),target:Number(fields.get('goal-'+p.id))})).filter(g=>g.target>0)};phase.weeklyTargets=[...(phase.weeklyTargets||[]).filter(w=>w.id!==week.id),week].sort((a,b)=>a.start.localeCompare(b.start));}
   else if(form.dataset.planningForm==='milestone'){const phase=phaseIn(next,form.dataset.phase),old=phase.milestones?.find(m=>m.id===form.dataset.id),milestone={id:form.dataset.id||'milestone-'+crypto.randomUUID(),name:String(fields.get('name')).trim(),date:String(fields.get('date')),examPartId:String(fields.get('part')),completed:old?.completed||false};phase.milestones=[...(phase.milestones||[]).filter(m=>m.id!==milestone.id),milestone].sort((a,b)=>a.date.localeCompare(b.date));}
   else{const phase={...next.phases.find(p=>p.id===form.dataset.id),id:form.dataset.id||'phase-'+crypto.randomUUID(),name:String(fields.get('name')).trim(),start:String(fields.get('start')),end:String(fields.get('end')),examPartIds:examPartsFor(qualification).filter(p=>Number(fields.get('goal-'+p.id))>0).map(p=>p.id),goals:examPartsFor(qualification).map(p=>({examPartId:p.id,unit:goalUnit(qualification,p.id),target:Number(fields.get('goal-'+p.id))})).filter(g=>g.target>0),focusTopicIds:fields.getAll('topic').map(String)};next.phases=[...next.phases.filter(p=>p.id!==phase.id),phase].sort((a,b)=>a.start.localeCompare(b.start));}
   await write('planning','planning',next,Number(form.dataset.revision),{clearForm:drafts.key(form)});editingPhaseId=null;editingWeek=null;editingMilestone=null;onUpdate();onNotice(form.id==='exam-form'?'受験日を保存しました。':form.dataset.planningForm==='context'?'計画の前提を保存しました。':form.dataset.planningForm==='week'?'週別目標を保存しました。':form.dataset.planningForm==='milestone'?'予定を保存しました。':'フェーズを保存しました。');
  }catch(error){onNotice(error.message);}finally{setBusy(false);}return true;
 }
 async function importGuest(uid,deviceId){
  const guest=createWorkspaceStore({owner:`guest:${deviceId}`,deviceId,qualificationId:qualification.id,rootPath,validate});
  try{const rows=await guest.read();if(!rows.length)return;if(!confirm(`ログイン前の受験日・計画と診断・模試${rows.filter(r=>['diagnostic','mock'].includes(r.kind)).length}件を追加します。元の記録は残します。取り込みますか？`))return;
   const value={format:'hitomon-workspace-backup',version:2,qualificationId:qualification.id,plan:rows.find(r=>r.kind==='planning')?.payload||null,runs:rows.filter(r=>['diagnostic','mock'].includes(r.kind)).map(r=>r.payload),planRevisions:rows.filter(r=>r.kind==='planRevision').map(r=>r.payload)};
   const result=await restoreBackup(value);
   if(result.plan==='retained')onNotice('アカウントの計画を維持し、ゲストの履歴を追加しました。ゲスト計画は元の保存領域に残っています。');
  }finally{await guest.close();}
 }
 const backup=()=>({format:'hitomon-workspace-backup',version:2,qualificationId:qualification.id,plan:row('planning')?.payload||null,runs:documents.filter(r=>['diagnostic','mock'].includes(r.kind)).map(r=>r.payload),planRevisions:documents.filter(r=>r.kind==='planRevision').map(r=>r.payload)});
 function validateBackup(value){if(value===undefined)return;if(!value||value.format!=='hitomon-workspace-backup'||value.version!==2||value.qualificationId!==qualification.id||!Array.isArray(value.runs)||value.runs.length>1000)throw new Error('受験日・計画・診断・模試のバックアップを確認できません。記録は変更していません。');const check=(kind,payload)=>{validate(kind,payload);if(new TextEncoder().encode(JSON.stringify(payload)).length>MAX_WORKSPACE_BYTES)throw new Error('計画・診断・模試の記録が大きすぎます。取り込み前の記録は変更していません。');};if(value.plan)check('planning',value.plan);if(value.planRevisions!==undefined&&(!Array.isArray(value.planRevisions)||value.planRevisions.length>10000))throw new Error('計画履歴は10000件以内にしてください。');const ids=new Set();for(const r of value.planRevisions||[]){check('planRevision',r);if(ids.has(r.id))throw new Error('計画履歴IDが重複しています。');ids.add(r.id);if(row(r.id)&&canonical(row(r.id).payload)!==canonical(r))throw new Error('同じIDの異なる計画履歴があります。既存の記録は変更していません。');}for(const run of value.runs){check(run.mode==='mock'?'mock':'diagnostic',run);if(ids.has(run.id))throw new Error('診断IDが重複しています。');ids.add(run.id);if(row(run.id)&&JSON.stringify(row(run.id).payload)!==JSON.stringify(run))throw new Error('同じIDの異なる診断があります。既存の記録は変更していません。');}}
 async function restoreBackup(value){if(!value)return {plan:'absent',diagnosticsAdded:0,diagnosticsRetained:0};validateBackup(value);const token=generation,target=workspace;if(!target)throw new Error('計画・診断・模試の保存先を開けません。');const result=await target.restoreBackup(value);if(token!==generation)throw new Error('保存先が変わりました。取り込み結果を確認してください。');documents=await target.read();onChanged();onUpdate();return result;}
 async function clearDiagnostics(){await workspace.clearDiagnostics();documents=await workspace.read();onUpdate();}
 // Sync-only updates must not capture forms or consume the draft-clear barrier.
 function showStatus(kind,error){status=kind;setSyncStatus('planning',kind,error);const markup=workspaceStatusHTML(kind);document.querySelectorAll('.workspace-status').forEach(el=>el.outerHTML=markup);}
 return {isBusy:()=>busy,hasDraft:()=>{drafts.capture();return hasPlanningDraft();},bind,views,restoreDrafts:drafts.restore,plan:()=>row('planning')?.payload||null,latestDiagnosis:()=>documents.filter(r=>r.kind==='diagnostic'&&r.payload.status!=='in_progress').sort((a,b)=>b.payload.completedAt.localeCompare(a.payload.completedAt)||b.id.localeCompare(a.id)).map(r=>diagnosticResult(r.payload,qualification))[0]||null,toggle:el=>{if(el.id==='plan-editor')editorOpen=el.open;if(el.id==='plan-ai')aiOpen=el.open;},allAttempts,action,input,change,submit,summary,importGuest,backup,validateBackup,restoreBackup,clearDiagnostics,store:()=>workspace,run:id=>row(id)?.payload,derivedRun:id=>documents.find(r=>['diagnostic','mock'].includes(r.kind)&&r.payload.slots.some(s=>s.id===id))?.id,onDocuments:rows=>{if(rows.some(r=>r.owner!==workspace.identity().owner))return;const changed=JSON.stringify(rows.map(r=>[r.id,r.localRevision,r.payload,r.conflict]))!==JSON.stringify(documents.map(r=>[r.id,r.localRevision,r.payload,r.conflict]));const planChanged=canonical(rows.filter(r=>r.id==='planning').map(r=>[r.localRevision,r.payload,r.conflict]))!==canonical(documents.filter(r=>r.id==='planning').map(r=>[r.localRevision,r.payload,r.conflict])),hasDraft=hasPlanningDraft(),protectDraft=getState().view==='planning'&&hasDraft;if(planChanged&&hasDraft)stale=true;documents=rows;if(protectDraft){const overview=document.getElementById('plan-overview');if(overview)overview.outerHTML=views().overviewHTML();const history=document.getElementById('plan-history');if(history)history.outerHTML=views().historyHTML();const conflicts=document.getElementById('workspace-conflicts');if(conflicts)conflicts.innerHTML=views().conflictsHTML();if(changed){const summaryElement=document.querySelector('.summary-preview');if(summaryElement){const open=summaryElement.open;summaryElement.outerHTML=views().summaryHTML();document.querySelector('.summary-preview').open=open;}const staleNotice=document.getElementById('planning-stale');if(staleNotice&&planChanged)staleNotice.hidden=false;}onUpdate({preserveForm:true});}else if(changed)onUpdate();},onStatus:showStatus,refresh:()=>onUpdate()};
}
