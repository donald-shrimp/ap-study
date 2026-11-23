// Store the learner's ordered inputs together so the group is saved and graded atomically.
export const MAX_ANSWER_SET_INPUTS=20;
export const answerSetTextLimit=field=>field.answerSet.maxLength??200;

export function answerSetValues(value){
 if(typeof value!=='string'||!value||value.length>25000)return null;
 try{
  const entries=JSON.parse(value);
  return Array.isArray(entries)&&entries.length<=MAX_ANSWER_SET_INPUTS&&entries.every(entry=>typeof entry==='string')?entries:null;
 }catch{return null;}
}

export function validAnswerSetValue(field,value){
 const entries=answerSetValues(value),slots=field.answerSet.slots;
 if(!entries||slots&&slots.length!==entries.length)return false;
 if(field.choices)return entries.every(entry=>entry===''&&slots||field.choices.some(choice=>choice.id===entry))&&
  (Boolean(slots)||new Set(entries).size===entries.length);
 return entries.length>=1&&entries.every(entry=>[...entry].length<=answerSetTextLimit(field));
}

export function canSubmitAnswerSet(field,value){
 const entries=answerSetValues(value);
 return Boolean(entries?.length&&(field.answerSet.slots?entries.every(entry=>entry.trim()):entries.some(entry=>entry.trim())));
}

export function formatAnswerSet(field,value){
 return (answerSetValues(value)||[]).map(entry=>{
  const choice=field.choices?.find(option=>option.id===entry);
  return choice?[choice.label,choice.text].filter(Boolean).join(' '):entry;
 }).filter(entry=>entry.trim()).join('\n');
}

export function withAnswerSets(original,revision){
 if(!revision)return original;
 return {...original,version:revision.version,items:original.items.map(item=>{
  const change=revision.items[item.id];
  if(!change)return item;
  const replaced=new Map(change.groups.flatMap(group=>(group.answerSet.sourceFieldIds??[group.id]).map(id=>[id,group])));
  return {...item,prompt:change.prompt,fields:item.fields.flatMap(field=>{
   const group=replaced.get(field.id);
   return !group?[field]:group.id===field.id?[group]:[];
  })};
 })};
}

export function linkedCaseField(item,id){
 return item.fields.find(field=>field.id===id||field.answerSet?.sourceFieldIds?.includes(id));
}
