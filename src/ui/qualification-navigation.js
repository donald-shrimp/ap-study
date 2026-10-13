import {esc} from '../utils.js';

const preferenceKey=root=>`hitomon-${root.pathname}last-qualification`;
export function preferredQualification(root) {
 try { return localStorage.getItem(preferenceKey(root)); } catch { return null; }
}
export function rememberQualification(root,id) {
 try { localStorage.setItem(preferenceKey(root),id); } catch { /* Navigation still works without preferences. */ }
}
export function qualificationChooserHTML(qualifications,root,previous) {
 return `<section class="panel qualification-chooser"><h1>資格を選ぶ</h1><div class="qualification-list">${qualifications.map(q=>`<a class="button secondary qualification-option" href="${new URL(q.id+'/',root).href}" ${q.id===previous?'aria-current="true"':''}><span><strong>${esc(q.name)}</strong><span class="small muted">${q.count}問${q.id===previous?' · 前回の資格':''}</span></span><span aria-hidden="true">→</span></a>`).join('')}</div></section>`;
}
export function installQualificationSwitch({qualifications,qualification,root,beforeLeave,onError}) {
 const link=document.createElement('a');link.id='qualification-switch';link.className='qualification-switch';
 link.href=new URL('?qualifications',root).href;link.setAttribute('aria-label',`資格を選ぶ（${qualification.name}）`);
 link.innerHTML=`<span>${esc(qualification.shortName||qualification.name)}</span><span aria-hidden="true">▼</span>`;
 document.querySelector('.brand').after(link);
 let leaving=false;
 link.addEventListener('click',async event=>{
  // Opening a separate tab leaves the current editor and its drafts intact.
  if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  event.preventDefault();if(leaving)return;leaving=true;link.setAttribute('aria-busy','true');
  try { if(await beforeLeave())location.assign(link.href); }
  catch(error){onError(error.message||'保存を確認できません。もう一度お試しください。');}
  finally {leaving=false;link.removeAttribute('aria-busy');}
 });
}
