import {goalsText} from '../domain/planning.js';
import {esc} from '../utils.js';
import {contextHTML} from './plan-context.js';
export function planConflictPreview(plan,qualification){
 const part=id=>qualification.examParts?.find(p=>p.id===id)?.label||id;
 const phases=plan.phases.map(p=>`<article><h4>${esc(p.name)}</h4><p>${esc(p.start)}〜${esc(p.end)} · 目標${esc(goalsText(p.goals,qualification))}</p><p class="small">${esc(p.examPartIds.map(part).join('・'))}${p.focusTopicIds.length?' · '+esc(p.focusTopicIds.map(id=>qualification.topics.find(t=>t.id===id)?.name||id).join('・')):''}</p>${p.weeklyTargets?.length?`<ul>${p.weeklyTargets.map(w=>`<li>${esc(w.start)}〜${esc(w.end)}：${esc(goalsText(w.goals,qualification))}</li>`).join('')}</ul>`:''}${p.milestones?.length?`<ul>${p.milestones.map(m=>`<li>${esc(m.date)} · ${esc(m.name)} · ${m.completed?'完了':'未完了'}</li>`).join('')}</ul>`:''}</article>`).join('');
 return `${plan.examDates.length?`<ul>${plan.examDates.map(d=>`<li>${esc(part(d.examPartId))}：${esc(d.date)}</li>`).join('')}</ul>`:''}${phases}${contextHTML(plan.context)}<details><summary>すべてのデータを見る</summary><pre>${esc(JSON.stringify(plan,null,2))}</pre></details>`;
}
