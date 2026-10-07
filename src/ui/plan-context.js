import {esc} from '../utils.js';
import {CONTEXT_FIELDS} from '../domain/planning.js';

export function contextHTML(context={}){
 const rows=CONTEXT_FIELDS.filter(([id])=>context[id]).map(([id,label])=>`<div><dt>${esc(label)}</dt><dd>${esc(context[id])}</dd></div>`);
 if(context.weeklyMinutes!==undefined)rows.splice(2,0,`<div><dt>1週間に使える時間</dt><dd>${context.weeklyMinutes}分</dd></div>`);
 return rows.length?`<dl class="context-list">${rows.join('')}</dl>${context.updatedOn?`<p class="small muted">前提の更新日：${esc(context.updatedOn)}</p>`:''}`:'<p class="small muted">計画の前提は未登録です。</p>';
}
export function contextFormHTML(plan,revision){
 const c=plan.context||{};
 return `<section class="panel"><h2>計画の前提</h2><p class="small">教材・使える時間・計画の理由を残せます。未登録でも学習できます。</p>${contextHTML(c)}<details><summary>前提を登録・編集する（任意）</summary><form id="context-form" data-planning-form="context" data-revision="${revision}">${CONTEXT_FIELDS.map(([id,label])=>`<label class="editor-field"><span>${esc(label)}</span><textarea name="${id}" rows="2" maxlength="2000">${esc(c[id]||'')}</textarea></label>`).join('')}<label class="editor-field"><span>1週間に使える時間（分・任意）</span><input name="weeklyMinutes" type="number" min="0" max="10080" step="1" value="${c.weeklyMinutes??''}" placeholder="例：180"></label><p class="small muted">ここに記入した内容は、AI相談用のJSONとプロンプトにも含まれます。</p><button class="button secondary" type="submit">前提を保存</button></form></details></section>`;
}
export function summaryPreviewHTML(summary,examParts=[]){
 const parts=summary.examDates.map(d=>`<li>${esc(examParts.find(p=>p.id===d.examPartId)?.label||d.examPartId)}：${esc(d.date)}（${d.daysUntil>=0?`あと${d.daysUntil}日`:`${-d.daysUntil}日前`}）</li>`).join('');
 const at=new Intl.DateTimeFormat('ja-JP',{timeZone:summary.timeZone,dateStyle:'medium',timeStyle:'short'}).format(new Date(summary.exportedAt));
 return `<details class="summary-preview"><summary>AIへ渡す内容を確認</summary><div><p class="small">資格・受験日・計画の前提・学習実績・診断結果・現在の計画を含みます。アプリからAIへの自動送信はありません。アカウントのメール・UID・問題本文は含みませんが、前提に書いた文章は含みます。</p><p><strong>${esc(summary.qualificationName)}</strong> · ${esc(at)} 時点</p>${parts?`<ul>${parts}</ul>`:'<p class="small">受験日は未登録です。</p>'}${contextHTML(summary.context)}<p>累計${summary.learning.all.completedAttempts}回 · 直近7日${summary.learning.last7Days.completedAttempts}回 · 復習候補${summary.reviewCount}件</p><p class="small">診断${summary.diagnostics.length}回。分野別の母数・出題構成と、現在の計画・実績も渡します。</p><details><summary>出力するJSONをすべて見る</summary><pre>${esc(JSON.stringify(summary,null,2))}</pre></details></div></details>`;
}
