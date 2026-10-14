// Format is independent of purpose/provenance. Free text is draft-only for now.
export const QUESTION_TYPES=Object.freeze(['singleChoice','multipleChoice','freeText']);
export const isMultiple=q=>q?.type==='multipleChoice';
export const gradingMethod=q=>q?.grading?.method||(q?.type==='freeText'?'deferred':'exactChoiceSet');
export const correctIds=q=>isMultiple(q)?q.correctChoiceIds:[q.correctChoiceId??q.choices?.[q.answer]?.id??'choice-'+q.answer];
export const canonicalIds=(q,ids)=>q.choices.filter(c=>ids.includes(c.id)).map(c=>c.id);
export const sameChoices=(a,b)=>a.length===b.length&&a.every(id=>b.includes(id));
export const chosenIds=(a,q=a.questionSnapshot)=>isMultiple(q)?a.selectedChoiceIds||[]:a.selectedChoiceId?[a.selectedChoiceId]:a.selected===null?[]:[q?.choices?.[a.selected]?.id??'choice-'+a.selected];
export function validResponse(q,value,{empty=false}={}){
 if(value===null)return empty;
 if(!isMultiple(q))return typeof value==='string'&&q.choices.some(c=>c.id===value);
 return Array.isArray(value)&&value.length<=q.choices.length&&(empty||value.length>0)&&new Set(value).size===value.length&&value.every(id=>typeof id==='string'&&q.choices.some(c=>c.id===id))&&JSON.stringify(value)===JSON.stringify(canonicalIds(q,value));
}
export function canSubmitIds(q,ids){return ids.length>0&&(!isMultiple(q)||q.selection?.mode!=='exact'||ids.length===q.selection.count);}
export const canSubmit=(a,q=a.questionSnapshot)=>canSubmitIds(q,chosenIds(a,q));
export const answerLabels=(q,ids)=>q.choices.filter(c=>ids.includes(c.id)).map(c=>c.label).join('・')||'未回答';
export function selectionInstruction(q){return !isMultiple(q)?'答えを1つ選んでください':q.selection?.mode==='exact'?`答えを${q.selection.count}つ選んでください`:'当てはまるものをすべて選んでください';}
export function validChoiceFormat(q){
 if(!['singleChoice','multipleChoice'].includes(q.type)||gradingMethod(q)!=='exactChoiceSet'||q.grading!==undefined&&(!q.grading||Array.isArray(q.grading)||typeof q.grading!=='object'||Object.keys(q.grading).some(k=>k!=='method')))return false;
 if(!isMultiple(q))return q.correctChoiceIds===undefined&&q.selection===undefined&&Number.isInteger(q.answer)&&q.answer>=0&&q.answer<q.choices.length&&q.choices[q.answer].id===q.correctChoiceId;
 const ids=q.correctChoiceIds,s=q.selection;
 return q.correctChoiceId===undefined&&q.answer===null&&validResponse(q,ids)&&s&&Object.keys(s).every(k=>['mode','count'].includes(k))&&(['all'].includes(s.mode)&&s.count===undefined||s.mode==='exact'&&Number.isInteger(s.count)&&s.count===ids.length&&s.count>=1&&s.count<=q.choices.length);
}
