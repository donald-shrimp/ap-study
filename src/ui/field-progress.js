import {esc} from '../utils.js';
export function compactFieldProgress(row){
 if(!row.total)return '<span class="field-measure small muted">未確認</span>';
 return `<span class="field-measure"><span class="field-score">自力正解 ${row.correct} / ${row.total}問</span><span class="field-mini-bar" role="img" aria-label="自力正解 ${Math.round(row.rate*100)}%"><span style="width:${row.rate*100}%"></span></span>${row.smallSample?'<span class="small muted">記録少なめ</span>':''}</span>`;
}
export function fieldBar(row,{diagnostic=false}={}){
 if(!row.total)return `<p class="small muted field-empty">${diagnostic?'この診断では未回答':'この期間の記録なし'} · 未確認</p>`;
 const label=diagnostic?`正解 ${row.correct} / ${row.total}問`:`自力正解 ${Math.round(row.rate*100)}% · ${row.correct} / ${row.total}問`;
 const breakdown=diagnostic?`不正解 ${row.incorrect}`:`ヒント付き ${row.assisted} · 不正解 ${row.incorrect} · 解答閲覧 ${row.revealed}`;
 return `<p class="field-score">${esc(label)} ${row.smallSample?'<span class="badge">記録少なめ</span>':''}</p><div class="field-bar" role="img" aria-label="${esc(label+'。'+breakdown)}">${['correct','assisted','incorrect','revealed'].map(k=>`<span class="field-${k}" style="width:${row[k]/row.total*100}%"></span>`).join('')}</div><p class="small muted field-breakdown">${esc(breakdown)}</p>`;
}
export function fieldLegend(diagnostic=false){return `<div class="field-legend">${(diagnostic?[['correct','正解'],['incorrect','不正解']]:[['correct','自力正解'],['assisted','ヒント付き正解'],['incorrect','不正解'],['revealed','解答閲覧']]).map(([k,label])=>`<span><i class="field-${k}" aria-hidden="true"></i>${label}</span>`).join('')}</div>`;}
