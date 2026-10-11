import {validatePlan,dateInZone,phaseProgress} from './planning.js';

export const PLAN_REVISION_KIND='planRevision';
const origins=['registered','edited','imported','baseline','resolved','restored'];
const idOK=v=>typeof v==='string'&&/^plan--[a-zA-Z0-9_-]{1,90}$/.test(v);
export function canonical(value){return JSON.stringify(sort(value));}
function sort(v){if(Array.isArray(v))return v.map(sort);if(v&&typeof v==='object')return Object.fromEntries(Object.keys(v).sort().map(k=>[k,sort(v[k])]));return v;}
export function createPlanRevision(plan,qualification,{previousId=null,origin='edited',at=new Date(),id='plan--'+crypto.randomUUID()}={}){
 return validatePlanRevision({format:'hitomon-plan-revision',version:1,id,qualificationId:qualification.id,savedAt:new Date(at).toISOString(),origin,previousId,plan:structuredClone(plan)},qualification);
}
export function validatePlanRevision(p,q){
 if(!p||Array.isArray(p)||Object.keys(p).some(k=>!['format','version','id','qualificationId','savedAt','origin','previousId','plan'].includes(k))||p.format!=='hitomon-plan-revision'||p.version!==1||!idOK(p.id)||p.qualificationId!==q.id||!origins.includes(p.origin)||p.previousId!==null&&(!idOK(p.previousId)||p.previousId===p.id)||typeof p.savedAt!=='string'||!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(p.savedAt)||!Number.isFinite(Date.parse(p.savedAt))||new Date(p.savedAt).toISOString()!==p.savedAt)throw new Error('計画履歴の形式を確認できません。');
 validatePlan(p.plan,q);return p;
}
export function planChanges(before,after,q){
 if(!before)return [{label:'登録',before:'',after:'計画を登録'}];
 const changes=[],add=(label,a,b)=>{if(canonical(a)!==canonical(b))changes.push({label,before:a,after:b});};
 const part=id=>q.examParts?.find(p=>p.id===id)?.label||id;
 add('受験日',before.examDates.map(d=>`${part(d.examPartId)} ${d.date}`).join('・')||'未登録',after.examDates.map(d=>`${part(d.examPartId)} ${d.date}`).join('・')||'未登録');
 add('タイムゾーン',before.timeZone,after.timeZone);
 const old=new Map(before.phases.map(p=>[p.id,p]));
 for(const p of after.phases){const a=old.get(p.id);old.delete(p.id);if(!a){changes.push({label:'期間を追加',before:'',after:`${p.name} · ${p.start}〜${p.end} · ${p.targets.completedAttempts}回`});continue;}
  const names=ids=>ids.map(id=>q.topics.find(t=>t.id===id)?.name||id).join('・')||'全分野';
  add('期間名',a.name,p.name);add(p.name+'の期間',`${a.start}〜${a.end}`,`${p.start}〜${p.end}`);add(p.name+'の目標',`${a.targets.completedAttempts}回`,`${p.targets.completedAttempts}回`);add('重点分野',names(a.focusTopicIds),names(p.focusTopicIds));add('対象パート',a.examPartIds.map(part).join('・'),p.examPartIds.map(part).join('・'));
  if(canonical(a.weeklyTargets||[])!==canonical(p.weeklyTargets||[]))changes.push({label:'週別目標',before:'',after:p.name+'の週別目標を変更'});
  if(canonical(a.milestones||[])!==canonical(p.milestones||[]))changes.push({label:'予定',before:'',after:p.name+'の予定・完了状態を変更'});
 }
 for(const p of old.values())changes.push({label:'期間を削除',before:`${p.name} · ${p.start}〜${p.end}`,after:'削除'});
 if(canonical(before.context||{})!==canonical(after.context||{}))changes.push({label:'計画の前提',before:'',after:'前提を変更'});
 return changes;
}
// Period totals follow the currently selected branch. Competing revisions stay
// in the change list, but cannot silently replace a past goal on this branch.
export function completedPlanPeriods({plan,revisions,attempts,qualification,at=new Date()}){
 const snapshots=revisions.filter(r=>Date.parse(r.savedAt)<=new Date(at).getTime()).sort((a,b)=>a.savedAt.localeCompare(b.savedAt)||a.id.localeCompare(b.id));
 const head=[...snapshots].reverse().find(r=>plan&&canonical(r.plan)===canonical(plan)),byId=new Map(snapshots.map(r=>[r.id,r])),chain=[],seen=new Set();
 let cursor=head;
 while(cursor&&!seen.has(cursor.id)){seen.add(cursor.id);chain.unshift(cursor);cursor=byId.get(cursor.previousId);}
 const timeline=[...chain,...(plan?[{plan,savedAt:new Date(at).toISOString(),origin:'current',id:'current'}]:[])],keys=new Set();
 for(const r of timeline)for(const p of r.plan.phases)if(p.end<dateInZone(at,r.plan.timeZone))keys.add(p.id+'|'+p.start);
 const output=[];
 for(const key of keys){
  const candidates=timeline.flatMap(r=>r.plan.phases.filter(p=>p.id+'|'+p.start===key).map(phase=>({r,phase})));
  // Find an end date which actually belonged to the saved plan at that date.
  let selected=null,baseline=false;
  for(const end of [...new Set(candidates.map(c=>c.phase.end))].sort()){
   if(end>=dateInZone(at,plan?.timeZone||'Asia/Tokyo'))continue;
   const beforeEnd=chain.filter(r=>dateInZone(r.savedAt,r.plan.timeZone)<=end).at(-1);
   if(beforeEnd){const phase=beforeEnd.plan.phases.find(p=>p.id+'|'+p.start===key);if(phase?.end===end){selected={r:beforeEnd,phase};break;}}
   else {const first=candidates[0];if(first.phase.end===end){selected=first;baseline=true;break;}}
  }
  if(!selected)continue;
  const scoped={...selected.r.plan,phases:[selected.phase]},result=phaseProgress(scoped,attempts,qualification,at)[0];
  output.push({...result,plan:scoped,revisionId:selected.r.id,baseline:baseline||selected.r.origin==='baseline'});
 }
 return output.sort((a,b)=>b.end.localeCompare(a.end)||b.start.localeCompare(a.start)||a.id.localeCompare(b.id));
}
