import {esc} from '../utils.js';

const attrs=values=>Object.entries(values).filter(([,v])=>v!==undefined&&v!==null).map(([k,v])=>`${k}="${esc(String(v))}"`).join(' ');
export function studyEntryButton({label,primary=false,field=false,attributes={},disabled=false,title,cue=''}){
 return `<button class="button ${field?'study-field-entry':'study-entrance'} ${primary?'primary':'secondary'}" ${attrs(attributes)} ${disabled?'disabled':''} ${title?`title="${esc(title)}"`:''}><span>${esc(label)}</span><span class="entry-cue">${esc(cue)}<span aria-hidden="true">→</span></span></button>`;
}
export function studyBackButton({action,view,label='中断',home=false}){
 const icon=home?'<svg class="study-back-icon" viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M2.5 9 10 3l7.5 6M5 7v10h4v-5h2v5h4V7"/></svg>':'<svg class="study-back-icon" viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><rect x="4" y="3" width="4" height="14" rx="1" fill="currentColor"/><rect x="12" y="3" width="4" height="14" rx="1" fill="currentColor"/></svg>';
 return `<button class="button study-back-button" ${attrs({'data-action':action,'data-view':view})}>${icon}${esc(label)}</button>`;
}
export function aiQuestionButton({action,attributes={}}){
 return `<button class="button" type="button" ${attrs({'data-action':action,...attributes})}><svg width="19" height="19" viewBox="0 0 20 20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 3h12v10H8l-4 4V3Z"/><path d="M7 7h6M7 10h4"/></svg>AIに聞く</button>`;
}
