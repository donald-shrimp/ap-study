// In-memory, owner-bound drafts. Preserve the form's original revision so a
// rerender cannot turn a stale edit into permission to overwrite a newer plan.
export function createPlanningDrafts(isPlanning) {
 const forms=new Map(),skip=new Set();let skipAll=false;
 const key=form=>[form.id||form.dataset.planningForm,form.dataset.phase||'',form.dataset.id||''].join('|');
 const controls=form=>[...form.elements].filter(el=>el.name&&!['button','submit','file','hidden'].includes(el.type));
 const dirty=el=>el.tagName==='SELECT'?[...el.options].some(o=>o.selected!==o.defaultSelected):['checkbox','radio'].includes(el.type)?el.checked!==el.defaultChecked:el.value!==el.defaultValue;
 function capture(){
  if(!isPlanning())return;
  for(const form of document.querySelectorAll('#main #exam-form, #main #phase-form, #main form[data-planning-form]')){
   const id=key(form);if(skipAll||skip.has(id))continue;
   const fields=controls(form);
   if(fields.some(dirty))forms.set(id,{revision:form.dataset.revision,fields:fields.map(el=>({name:el.name,type:el.type,value:el.value,checked:el.checked}))});
   else forms.delete(id);
  }
  skip.clear();skipAll=false;
 }
 function restore(){
  if(!isPlanning())return;
  for(const form of document.querySelectorAll('#main form')){
   const draft=forms.get(key(form));if(!draft)continue;
   if(draft.revision!==undefined)form.dataset.revision=draft.revision;
   const fields=controls(form);draft.fields.forEach((saved,i)=>{const el=fields[i];if(!el||el.name!==saved.name||el.type!==saved.type)return;if(['checkbox','radio'].includes(el.type))el.checked=saved.checked;else el.value=saved.value;});
   for(let el=form.parentElement;el;el=el.parentElement)if(el.tagName==='DETAILS')el.open=true;
  }
 }
 function clear(form){if(!form)return;const id=typeof form==='string'?form:key(form);forms.delete(id);skip.add(id);}
 function advance(from,to){
  for(const draft of forms.values())if(Number(draft.revision)===from)draft.revision=String(to);
  if(isPlanning())for(const form of document.querySelectorAll('#main form[data-revision]'))if(Number(form.dataset.revision)===from)form.dataset.revision=String(to);
 }
 return {key,capture,restore,clear,advance,has:()=>forms.size>0,reset:()=>{forms.clear();skip.clear();skipAll=true;}};
}
