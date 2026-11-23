import {linkedCaseField} from '../domain/case-answer-set.js';
import {esc} from '../utils.js';
import {questionTextHTML} from './question-text.js';

const textHTML=text=>questionTextHTML(text,{lists:true});

export function writtenReflectionHTML({run, explanation, state, loading, failed, finish}) {
  const title=explanation?.title||run.material.title;
  const sections=explanation?.sections||[];
  const itemLabels=new Map(run.material.items.map(item=>[item.id,item]));
  function referenceButtons(section) {
    const seen=new Set();
    const answers=section.links.flatMap(({itemId,fieldIds})=>{
      const item=itemLabels.get(itemId);
      return fieldIds.map(id=>{
        const field=linkedCaseField(item,id),key=itemId+'--'+field.id;
        if(seen.has(key))return '';
        seen.add(key);
        const label=item.fields.length===1?item.label:`${item.label} ${field.label}`;
        return `<button class="button quiet" data-action="written-reflection-answer" data-written-key="${esc(key)}">${esc(label)}の回答を見る</button>`;
      });
    }).join('');
    const refs=[...new Set(section.links.flatMap(link=>itemLabels.get(link.itemId).bodyRefs||[]))];
    const source=refs.length===1?`<button class="button quiet" data-action="written-reflection-study" data-pane="body" data-ref="${esc(refs[0])}">本文の該当箇所を見る</button>`:'';
    return answers+source;
  }
  const introduction=[];
  const body=[];
  const collapsible=[];
  for(const [i,section] of sections.entries()){
    const id=esc(section.id), tag=section.level===3?'h3':'h2', heading=esc(section.heading);
    const content=`<div class="explanation rich-question written-reflection-text">${textHTML(section.text)}</div>`;
    if(section.openByDefault){
      introduction.push(`<section class="written-reflection-section"><${tag}>${heading}</${tag}>${content}</section>`);
      continue;
    }
    if(!section.links.length&&section.level===2&&sections[i+1]?.level===3){
      body.push(`<div class="written-reflection-group"><h2>${heading}</h2>${content}</div>`);
      continue;
    }
    const references=referenceButtons(section);
    collapsible.push(section);
    body.push(`<details class="written-reflection-section" data-reflection-section="${id}" ${state.open.includes(section.id)?'open':''}><summary><${tag}>${heading}</${tag}></summary>${content}${references?`<div class="button-row written-reflection-refs">${references}</div>`:''}</details>`);
  }
  const toc=collapsible.map(section=>{
    const labels=[...new Set(section.links.map(link=>itemLabels.get(link.itemId).label))];
    const heading=section.heading.replace(/^設問[^｜]*｜/,'');
    return `<li><button class="button quiet written-reflection-jump" data-action="written-reflection-jump" data-id="${esc(section.id)}">${labels.length?`<span class="small muted">${esc(labels.join('・'))}</span>`:''}<span>${esc(heading)}</span><span aria-hidden="true">↓</span></button></li>`;
  }).join('');
  return `<div class="study-toolbar written-toolbar"><button class="button secondary" data-action="written-reflection-study" data-pane="questions">回答に戻る</button></div>
    <div class="page-heading written-reflection-heading"><p class="small muted">大問の振り返り</p><h1 id="written-reflection-title" tabindex="-1">${esc(title)}</h1></div>
    <article class="panel written-reflection" ${loading?'aria-busy="true"':''}>
      ${loading?'<p role="status">大問解説を読み込んでいます。</p>':''}
      ${failed?'<p role="status">大問解説を読み込めませんでした。</p><button class="button secondary" data-action="written-reflection-open">再試行</button>':''}
      ${explanation?`<div class="explanation rich-question written-reflection-text">${textHTML(explanation.introduction)}</div>${introduction.join('')}
        <nav aria-labelledby="written-reflection-toc" class="written-reflection-toc">
          <h2 id="written-reflection-toc" tabindex="-1">目次</h2><ul>${toc}</ul>
          <div class="button-row">${collapsible.length>=4?`<button class="button secondary" data-action="written-reflection-expand">${collapsible.every(s=>state.open.includes(s.id))?'すべて閉じる':'すべて開く'}</button>`:''}<button class="button quiet" data-action="written-reflection-study" data-pane="body">問題文を見る</button></div>
        </nav>${body.join('')}`:''}
      ${finish}
      ${collapsible.length?'<button class="button secondary reflection-back-to-toc" data-action="written-reflection-toc" hidden>目次へ ↑</button>':''}
    </article>`;
}
