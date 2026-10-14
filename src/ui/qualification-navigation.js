import {esc} from '../utils.js';
import {studyTargets,rememberedPart,resolveStudyTarget,targetLabel,targetCount,targetURL,withRuntimeNavigation} from '../domain/study-target.js';

const preferenceKey=root=>`hitomon-${root.pathname}last-qualification`;
export function preferredQualification(root) {
 try { return localStorage.getItem(preferenceKey(root)); } catch { return null; }
}
export function rememberQualification(root,id) {
 try { localStorage.setItem(preferenceKey(root),id); } catch { /* Navigation still works without preferences. */ }
}
export function qualificationChooserHTML(qualifications,root,previous,{from=new URL(location.href),selectedQualificationId=previous,selectedPartId=null}={}) {
 return `<section class="panel qualification-chooser"><h1>資格・科目を選ぶ</h1><div class="qualification-list">${qualifications.map(q=>{
  const targets=studyTargets(q),selected=selectedPartId??resolveStudyTarget(q,{rememberedPartId:rememberedPart(root,q.id)});
  return targets.length?`<section class="qualification-group" aria-label="${esc(q.name)}">${targets.length>1?`<h2>${esc(q.name)}</h2>`:''}<div class="qualification-targets">${targets.map(p=>`<a class="button secondary qualification-option" data-qualification-id="${esc(q.id)}" data-part-id="${esc(p.examPartId)}" href="${esc(targetURL(root,q.id,p.examPartId,{home:true,from}).href)}" ${q.id===selectedQualificationId&&p.examPartId===selected?'aria-current="true"':''}><span><strong>${esc(targetLabel(q,p.examPartId,{short:targets.length>1,separator:'－'}))}</strong>${targetCount(p)?`<span class="small muted">${esc(targetCount(p))}</span>`:''}</span><span aria-hidden="true">→</span></a>`).join('')}</div></section>`:'';
 }).join('')}</div></section>`;
}
export function installQualificationSwitch({qualification,partId,root,beforeLeave,onError}) {
 const link=document.createElement('a');link.id='qualification-switch';link.className='qualification-switch';
 const url=withRuntimeNavigation(new URL('?qualifications',root),new URL(location.href));url.searchParams.set('qualification',qualification.id);url.searchParams.set('part',partId);
 link.href=url.href;link.dataset.partId=partId;link.setAttribute('aria-label',`資格・科目を選ぶ（${targetLabel(qualification,partId)}）`);
 const part=studyTargets(qualification).find(p=>p.examPartId===partId);
 link.innerHTML=`<span class="qualification-label"><span class="qualification-name">${esc(qualification.shortName||qualification.name)}</span>${studyTargets(qualification).length>1?`<span class="qualification-part">・${esc(part.label)}</span>`:''}</span><span aria-hidden="true">▼</span>`;
 const brand=document.querySelector('.brand');brand.after(link);brand.href=link.href;
 let leaving=false;
 for(const anchor of [link,brand])anchor.addEventListener('click',async event=>{
  // Opening a separate tab leaves the current editor and its drafts intact.
  if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  event.preventDefault();if(leaving)return;leaving=true;anchor.setAttribute('aria-busy','true');
  try { if(await beforeLeave())location.assign(anchor.href); }
  catch(error){onError(error.message||'保存を確認できません。もう一度お試しください。');}
  finally {leaving=false;anchor.removeAttribute('aria-busy');}
 });
}
