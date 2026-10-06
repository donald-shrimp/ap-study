"""Real IndexedDB: durable mutable-document outbox, stale tabs and conflict resolution."""
import shutil
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=b.new_page();page.goto('http://127.0.0.1:4173/')
 result=page.evaluate('''async()=>{
  const {createWorkspaceStore}=await import('/src/storage/workspace.js'),{blankPlan,validatePlan}=await import('/src/domain/planning.js');
  const q=await (await fetch('/content/ap/qualification.json')).json(),assert=(ok,message)=>{if(!ok)throw new Error(message);};
  const make=(owner='uid:a',qualificationId='ap')=>createWorkspaceStore({owner,qualificationId,deviceId:'device-a',rootPath:'/workspace-test/',validate:(kind,payload)=>validatePlan(payload,{...q,id:qualificationId})});
  let store=make();const first=await store.write('planning','planning',blankPlan(q),0);assert(first.dirty,'outbox not committed');await store.close();store=make();assert((await store.read())[0].operationId===first.operationId,'outbox not durable');
  const plan={...blankPlan(q),examDates:[{examPartId:'objective',date:'2026-11-04'}]},second=await store.write('planning','planning',plan,1);
  await store.acknowledge('planning',first.operationId,{revision:1});let row=(await store.read())[0];assert(row.dirty&&row.payload.examDates.length===1&&row.remoteRevision===1,'late ACK erased newer work');
  await store.merge({id:'planning',kind:'planning',version:1,deviceId:'device-a',operationId:first.operationId,revision:1,payload:blankPlan(q)});row=(await store.read())[0];assert(row.dirty&&!row.conflict,'ancestor replay caused a false conflict');
  let rejected=false;try{await store.write('planning','planning',blankPlan(q),1);}catch{rejected=true;}assert(rejected&&(await store.read())[0].payload.examDates.length===1,'stale tab erased the plan');
  const remote={id:'planning',kind:'planning',version:1,deviceId:'device-b',operationId:'remote:2',revision:2,payload:{...blankPlan(q),examDates:[{examPartId:'objective',date:'2026-12-01'}]}};
  await store.merge(remote);row=(await store.read())[0];assert(row.conflict&&row.payload.examDates[0].date==='2026-11-04','remote silently overwrote pending work');
  await store.resolve('planning',true);row=(await store.read())[0];assert(row.dirty&&!row.conflict&&row.remoteRevision===2,'local choice not rebased');
  await store.merge({...remote,revision:3,operationId:'remote:3'});await store.resolve('planning',false);row=(await store.read())[0];assert(!row.dirty&&!row.conflict&&row.payload.examDates[0].date==='2026-12-01','remote choice not applied');
  const other=make('uid:b');assert((await other.read()).length===0,'UID namespaces mixed');await other.close();const qualification=make('uid:a','another');assert((await qualification.read()).length===0,'qualification namespaces mixed');await qualification.close();
  let invalid=false;try{await store.write('planning','planning',{...plan,qualificationId:'another'},row.localRevision);}catch{invalid=true;}assert(invalid&&(await store.read())[0].payload.examDates[0].date==='2026-12-01','invalid plan changed the record');await store.close();return true;
 }''');assert result;b.close()
print('PASS workspace atomic outbox / reload / late ACK / ancestor replay / stale tab / explicit conflict choices / UID and qualification isolation / invalid write unchanged')
