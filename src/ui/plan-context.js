import {esc} from '../utils.js';
import {CONTEXT_FIELDS} from '../domain/planning.js';

export function contextHTML(context={}){
 const rows=CONTEXT_FIELDS.filter(([id])=>context[id]).map(([id,label])=>`<div><dt>${esc(label)}</dt><dd>${esc(context[id])}</dd></div>`);
 if(context.weeklyMinutes!==undefined)rows.splice(2,0,`<div><dt>1週間に使える時間</dt><dd>${context.weeklyMinutes}分</dd></div>`);
 return rows.length?`<dl class="context-list">${rows.join('')}</dl>`:'';
}
export function contextFormHTML(plan,{contextOpen,contextExtrasOpen}){
 const c=plan.context||{};
 const field=([id,label])=>`<label class="editor-field"><span>${esc(label)}</span><textarea name="${id}" rows="2" maxlength="2000">${esc(c[id]||'')}</textarea></label>`;
 const main=CONTEXT_FIELDS.find(([id])=>id==='materials'),extra=CONTEXT_FIELDS.filter(field=>field!==main);
 return `<details class="plan-context" id="plan-context" ${contextOpen?'open':''}><summary>学習に使える時間・教材</summary><label class="editor-field"><span>1週間に使える時間（分）</span><input name="weeklyMinutes" type="number" min="0" max="10080" step="1" value="${c.weeklyMinutes??''}"></label>${field(main)}<details id="plan-context-extras" ${contextExtrasOpen?'open':''}><summary>条件を詳しく入力</summary>${extra.map(field).join('')}</details><p class="small muted">記入内容はAIへの学習相談に含まれます。</p></details>`;
}
export function summaryPreviewHTML(summary,examParts=[]){
 const parts=summary.examDates.map(d=>`<li>${esc(examParts.find(p=>p.id===d.examPartId)?.label||d.examPartId)}：${esc(d.date)}（${d.daysUntil>=0?`あと${d.daysUntil}日`:`${-d.daysUntil}日前`}）</li>`).join('');
 const at=new Intl.DateTimeFormat('ja-JP',{timeZone:summary.timeZone,dateStyle:'medium',timeStyle:'short'}).format(new Date(summary.exportedAt));
 return `<details class="summary-preview"><summary>AIへ渡す内容を確認</summary><div><p class="small">資格・受験日・計画の前提・学習実績・診断結果・現在の計画を含みます。アプリからAIへの自動送信はありません。アカウントのメール・UID・問題本文は含みませんが、前提に書いた文章は含みます。</p><p><strong>${esc(summary.qualificationName)}</strong> · ${esc(at)} 時点</p>${parts?`<ul>${parts}</ul>`:'<p class="small">受験日は未登録です。</p>'}${contextHTML(summary.context)}<p>${summary.learningByPart.map(p=>`${esc(examParts.find(x=>x.id===p.examPartId)?.label||p.examPartId)}：${p.unit==='cases'?`${p.completedCases}題完了`:`累計${p.all.completedAttempts}問 · 直近7日${p.last7Days.completedAttempts}問`}`).join(' ／ ')}</p><p class="small">診断${summary.diagnostics.length}回。分野別の母数・出題構成と、現在の計画・実績も渡します。</p><details><summary>出力するJSONをすべて見る</summary><pre>${esc(JSON.stringify(summary,null,2))}</pre></details></div></details>`;
}
