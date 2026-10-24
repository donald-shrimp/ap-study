import {esc,dateText} from '../utils.js';
import {mockLabel,mockResult} from '../domain/mock.js';
export function createMockViews({qualification,documents,currentSetId,excludeOutdated=true}){
 const sets=qualification.mockSets?.sets||[],runs=documents.filter(r=>r.kind==='mock').sort((a,b)=>b.payload.startedAt.localeCompare(a.payload.startedAt)||b.id.localeCompare(a.id));
 const savedSets=new Map();for(const r of runs){const s=r.payload.mockSet;if(!sets.some(set=>set.id===s.id)&&!savedSets.has(s.id))savedSets.set(s.id,{...s,size:r.payload.size,retired:true});}
 const blocked=set=>excludeOutdated&&set.hasLawChange;
 const forSet=id=>runs.filter(r=>r.payload.mockSet.id===id);
 const previous=id=>forSet(id).filter(r=>r.payload.status!=='in_progress').sort((a,b)=>b.payload.completedAt.localeCompare(a.payload.completedAt)||b.id.localeCompare(a.id))[0];
 const score=r=>{const result=mockResult(r.payload,qualification);return `${Math.round(result.scoreRate*100)}% · ${result.correct} / ${result.size}問正解`;};
 const lastHTML=id=>{const r=previous(id);return r?`<p class="mock-previous">前回${r.payload.status==='ended_early'?'（途中終了）':''}：${score(r)}</p>`:'';};
 function cardHTML(set,records){
  const active=forSet(set.id).find(r=>r.payload.status==='in_progress');
  let actionHTML;
  if(records){
   actionHTML=`<button class="button secondary" data-action="mock-records" data-set="${esc(set.id)}">記録を見る <span aria-hidden="true">→</span></button>`;
  }else{
   const resumeHTML=active?`<p class="small">中断中 · ${Object.keys(active.payload.responses).length} / ${active.payload.size}問</p><button class="button primary" data-action="resume-diagnostic" data-id="${esc(active.id)}">続きから</button>`:'';
   actionHTML=set.retired?active?resumeHTML:`<button class="button secondary" data-action="resume-diagnostic" data-id="${esc(previous(set.id).id)}">結果を見る</button>`:`${resumeHTML}<button class="button ${active?'secondary':'primary'}" data-action="start-mock" data-set="${esc(set.id)}" ${blocked(set)?'disabled':''}>${active?'新しく受ける':'この模試を受ける'}</button>`;
  }
  return `<article class="panel mock-set" data-mock-set="${esc(set.id)}"><h2>${esc(mockLabel(set.label))}</h2><p class="small muted">固定${set.size}問</p>${lastHTML(set.id)}${blocked(set)?'<p class="small muted">法令改正のある問題を含むため除外中</p>':''}${actionHTML}</article>`;
 }
 const cards=records=>[...sets,...savedSets.values()].map(set=>cardHTML(set,records)).join('');
 function selectionHTML(){return `<div class="page-heading"><h1>模試を選ぶ</h1><button class="button study-back-button" data-view="home"><span aria-hidden="true">⌂</span> ホーム</button></div><p class="small muted">ヒントなし。終了後に採点。中断できます。</p><div class="mock-set-grid">${cards(false)}</div>${!sets.length&&!savedSets.size?'<p class="empty">受けられる模試はまだありません。</p>':''}`;}
 function recordsHTML(){return `<div class="mock-set-grid">${cards(true)}</div>${!sets.length&&!savedSets.size?'<p class="empty">模試はまだ登録されていません。</p>':''}`;}
 function detailHTML(){
  const selected=sets.find(s=>s.id===currentSetId),rows=forSet(currentSetId),label=selected?mockLabel(selected.label):rows[0]?.payload.mockSet.label||'模試';
  return `<div class="page-heading"><h1>${esc(label)}の記録</h1><button class="button secondary" data-action="mock-history">模試結果の一覧へ</button></div><section class="panel mock-history">${rows.length?rows.map(r=>`<div class="row"><div><p class="row-title">${dateText(r.payload.startedAt)}</p>${r.payload.status==='in_progress'?`<p>中断中 · ${Object.keys(r.payload.responses).length} / ${r.payload.size}問</p>`:`<p class="mock-score">${score(r)}</p>${r.payload.status==='ended_early'?'<p class="small muted">途中終了</p>':''}`}</div><button class="button secondary" data-action="resume-diagnostic" data-id="${esc(r.id)}">${r.payload.status==='in_progress'?'続きから':'結果を見る'}</button></div>`).join(''):'<p class="empty">まだ受けていません。</p>'}</section>${selected?`<button class="button primary" data-action="start-mock" data-set="${esc(selected.id)}" ${blocked(selected)?'disabled':''}>${rows.length?'もう一度受ける':'この模試を受ける'}</button>`:''}`;
 }
 return {selectionHTML,recordsHTML,detailHTML};
}
