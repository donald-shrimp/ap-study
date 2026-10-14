const partKey=(root,id)=>`hitomon-v2:${root.pathname}:${id}:target`;

export function studyTargets(qualification){
 if(Array.isArray(qualification.studyTargets))return qualification.studyTargets;
 const parts=(qualification.examParts||[]).filter(p=>p.practiceAvailable),questions=parts.filter(p=>p.unit!=='cases');
 return parts.filter(p=>p.unit!=='cases'||qualification.cases?.count>0).map(p=>({examPartId:p.id,label:p.label,unit:p.unit||'questionAttempts',count:p.unit==='cases'?qualification.cases.count:questions.length===1?qualification.count:undefined}));
}
export function rememberedPart(root,id){try{return localStorage.getItem(partKey(root,id));}catch{return null;}}
export function rememberPart(root,id,part){try{localStorage.setItem(partKey(root,id),part);}catch{/* Explicit URLs still select a target. */}}
export function resolveStudyTarget(qualification,{requestedPartId=null,rememberedPartId=null}={}){
 const targets=studyTargets(qualification),valid=id=>targets.some(p=>p.examPartId===id);
 if(requestedPartId!==null)return valid(requestedPartId)?requestedPartId:null;
 return valid(rememberedPartId)?rememberedPartId:valid(qualification.defaultExamPartId)?qualification.defaultExamPartId:targets[0]?.examPartId||null;
}
export function targetLabel(qualification,partId,{short=false,separator=short?'・':'－'}={}){
 const name=short?qualification.shortName||qualification.name:qualification.name;
 return studyTargets(qualification).length>1?`${name}${separator}${studyTargets(qualification).find(p=>p.examPartId===partId)?.label||''}`:name;
}
export function targetCount(target){return Number.isInteger(target.count)?target.unit==='cases'?`大問${target.count}題`:`${target.count}問`:'';}
export function withRuntimeNavigation(url,from){
 if(['localhost','127.0.0.1'].includes(from.hostname)&&from.searchParams.get('firebase-emulator')==='1')url.searchParams.set('firebase-emulator','1');
 return url;
}
export function targetURL(root,qualificationId,partId,{home=false,from=root}={}){
 const url=new URL(qualificationId+'/',root);url.searchParams.set('part',partId);if(home)url.searchParams.set('entry','home');return withRuntimeNavigation(url,from);
}
