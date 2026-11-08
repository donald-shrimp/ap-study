// Local editorial preview only; no app routes, learning records, or publication.
import {readFile,writeFile} from 'node:fs/promises';
import {questionTextHTML} from '../../../../src/ui/question-text.js';
import {inlineTextHTML} from '../../../../src/ui/inline-text.js';
import {esc} from '../../../../src/utils.js';

const cases=[
 {id:'ap-r07h-pm1',label:'問1 セキュリティ'},
 {id:'ap-r07h-pm2',label:'問2 経営戦略'},
 {id:'ap-r07h-pm3',label:'問3 アルゴリズム'},
 {id:'ap-r07h-pm4',label:'問4 システム構成'},
 {id:'ap-r07h-pm5',label:'問5 ネットワーク'},
 {id:'ap-r07h-pm6',label:'問6 データベース'},
 {id:'ap-r07h-pm7',label:'問7 組込みシステム'},
 {id:'ap-r07h-pm8',label:'問8 ソフトウェア開発'},
 {id:'ap-r07h-pm9',label:'問9 プロジェクト管理'},
 {id:'ap-r07h-pm10',label:'問10 サービス管理'},
 {id:'ap-r07h-pm11',label:'問11 システム監査'},
];
const bank=JSON.parse(await readFile(new URL('../../../../content/ap/written-cases.json',import.meta.url),'utf8'));
const mappings=JSON.parse(await readFile(new URL('explanation-links.json',import.meta.url),'utf8'));

function questionLink(c,t){
 const [label,description]=t.heading.split('｜');
 return `<a class="preview-question-link" href="#${c.id}--${t.id}"><span class="preview-question-label">${esc(label)}</span><span>${esc(description)} →</span></a>`;
}
function sourceQuestion(c,t){
 const item=c.material.items.find(i=>i.id===t.itemId);
 return `<div class="preview-question-context"><p class="small muted">この解説の対象：${esc(t.heading.split('｜')[0])}</p><details class="preview-source-question"><summary>${esc(item.label)}の設問文を確認</summary><div class="preview-detail">${questionTextHTML(item.prompt)}<p class="small">対応する回答欄：${t.fieldIds.map(id=>esc(item.fields.find(f=>f.id===id).label)).join('・')}</p></div></details></div>`;
}
function headingHTML(c,heading,level){
 const t=c.targets.find(t=>t.heading===heading);
 if(!t)return `<h${level}>${inlineTextHTML(heading)}</h${level}>`;
 return `<h${level} class="preview-explanation-target" id="${c.id}--${t.id}" tabindex="-1">${inlineTextHTML(heading)}</h${level}>${sourceQuestion(c,t)}`;
}

// Lists and editorial headings surround the app's existing rich text renderer.
// This intentionally does not accept arbitrary Markdown links or raw HTML.
function blocks(source,c){
 const lines=source.trim().split('\n');let html='',pending=[];
 const flush=()=>{if(pending.length){html+=questionTextHTML(pending.join('\n'));pending=[];}};
 for(let i=0;i<lines.length;){
  const line=lines[i];
  if(line.startsWith('```')){
   flush();const code=[line];i++;
   while(i<lines.length){code.push(lines[i]);if(lines[i++].startsWith('```'))break;}
   html+=questionTextHTML(code.join('\n'));continue;
  }
  const heading=line.match(/^### (.+)$/);
  if(heading){flush();html+=headingHTML(c,heading[1],3);i++;continue;}
  if(/^(- |\d+\. )/.test(line)){
   flush();const ordered=/^\d+\. /.test(line),pattern=ordered?/^\d+\. /:/^- /,items=[];
   while(i<lines.length&&pattern.test(lines[i]))items.push(lines[i++].replace(pattern,''));
   const tag=ordered?'ol':'ul';html+=`<${tag}>${items.map(v=>`<li>${questionTextHTML(v)}</li>`).join('')}</${tag}>`;continue;
  }
  pending.push(line);i++;
 }
 flush();return html;
}

const articles=[];
for(const c of cases){
 const md=await readFile(new URL(c.id+'.md',import.meta.url),'utf8');
 c.material=bank.find(item=>item.id===c.id);c.targets=mappings[c.id];
 const headings=[...md.matchAll(/^#{2,3} (.+)$/gm)].map(m=>m[1]);
 const covered=new Set();
 for(const t of c.targets){
  const item=c.material.items.find(i=>i.id===t.itemId);
  if(!/^[a-z0-9-]+$/.test(t.id)||!item||headings.filter(h=>h===t.heading).length!==1||!t.heading.startsWith(item.label)||!t.fieldIds.length)throw Error('Invalid explanation target: '+c.id+' '+t.id);
  for(const fieldId of t.fieldIds){
   const key=t.itemId+'--'+fieldId;
   if(!item.fields.some(f=>f.id===fieldId)||covered.has(key))throw Error('Invalid or duplicate field link: '+key);
   covered.add(key);
  }
 }
 if(new Set(c.targets.map(t=>t.id)).size!==c.targets.length||covered.size!==c.material.items.flatMap(i=>i.fields).length)throw Error('Incomplete explanation links: '+c.id);
 const index=`<nav class="preview-question-index" aria-label="小問と解説の対応"><h2 id="${c.id}--questions" tabindex="-1">小問と解説の対応</h2>${c.targets.map(t=>questionLink(c,t)).join('')}</nav>`;
 const title=md.match(/^# (.+)/)[1],sections=md.split(/^## /m).slice(1);
 const body=sections.map((section,i)=>{
  const boundary=section.indexOf('\n'),heading=section.slice(0,boundary),content=blocks(section.slice(boundary+1),c),target=c.targets.find(t=>t.heading===heading);
  const back=`<a class="preview-return" href="#${c.id}--questions">小問と解説の対応に戻る ↑</a>`;
  const sectionHTML=i<2?`<section class="preview-section">${headingHTML(c,heading,2)}${content}${back}</section>`:`<details class="preview-section"><summary${target?` class="preview-explanation-target" id="${c.id}--${target.id}"`:''}>${esc(heading)}</summary><div class="preview-detail">${target?sourceQuestion(c,target):''}${content}${back}</div></details>`;
  return sectionHTML+(i===0?index:'');
 }).join('');
 articles.push(`<article class="panel preview-case" id="${c.id}" aria-labelledby="${c.id}-title"><div class="question-meta"><span>応用情報 · 2025年春期</span><span class="badge">大問全体の解説</span></div><h1 id="${c.id}-title" tabindex="-1">${esc(title)}</h1><div class="rich-question explanation">${body}</div></article>`);
}

await writeFile(new URL('preview.html',import.meta.url),`<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>初学者向け・大問全体の解説 ${cases.length}題</title>
<link rel="stylesheet" href="../../../../styles.css"><style>
.preview-main{width:min(100%,960px);margin:auto;padding:24px 20px 48px;min-width:0}
.preview-header{margin-bottom:18px}.preview-header p{margin-bottom:10px}
.preview-nav{display:flex;flex-wrap:wrap;gap:8px}.preview-nav a[aria-current=page]{background:var(--blue);border-color:#a8b9cd;color:var(--navy)}
.preview-case[hidden]{display:none}.preview-case h1{margin:12px 0 28px}.preview-section{border-top:1px solid var(--line);padding:22px 0 4px}
.preview-section summary{font-weight:700;min-height:44px;cursor:pointer;padding:3px 0;font-size:1.1em}
.preview-detail{padding-top:16px}.preview-section h3{margin-top:24px}.preview-section li{margin-bottom:10px}.preview-section li p{margin:0}
.preview-section code{font-family:ui-monospace,monospace}.preview-section pre{white-space:pre;max-width:100%;overflow:auto}
.preview-section .question-table{min-width:540px}.preview-section .question-table-scroll{max-width:100%;overflow:auto}
.preview-tools{margin:0 0 14px}.preview-case h1:focus{outline:none}
.preview-question-index{border-top:1px solid var(--line);padding:20px 0}.preview-question-index h2{font-size:1.1em}
.preview-question-link{display:grid;grid-template-columns:minmax(110px,.3fr) minmax(0,1fr);gap:8px;align-items:center;min-height:48px;padding:10px 4px;border-bottom:1px solid var(--line);text-decoration:none;color:var(--text);font-size:.9em}
.preview-question-label{font-weight:700;color:var(--navy)}.preview-question-link[aria-current=location]{background:var(--blue)}
.preview-explanation-target{scroll-margin-top:18px}.preview-explanation-target:target{background:var(--blue)}
.preview-question-index h2:focus,h3.preview-explanation-target:focus,h2.preview-explanation-target:focus{outline:none}
.preview-question-context{margin:8px 0 18px;border-left:3px solid var(--line);padding-left:12px}.preview-question-context p{margin-bottom:4px}
.preview-source-question summary{font-weight:500;font-size:.875rem}.preview-source-question .preview-detail{padding-top:10px}
.preview-return{display:inline-flex;align-items:center;min-height:44px;font-size:.875rem;margin-top:12px}
@media(max-width:480px){.preview-main{padding:16px 12px 36px}.preview-case{padding:20px 16px}.preview-nav .button{flex:1 1 120px;font-size:.85rem;padding:9px}.preview-case h1{font-size:1.35rem}.preview-section{padding-top:18px}.preview-section h2{font-size:1.13em}}
@media print{.preview-nav,.preview-tools{display:none}.preview-case[hidden]{display:block}.preview-case{break-before:page}.preview-main{width:100%}}
</style></head><body><main class="preview-main">
<header class="preview-header"><p class="small muted">ひと問 · 大問全体の解説の試作</p><p>大問の見取り図から読み進めることも、「小問と解説の対応」から必要な説明へ進むこともできます。</p>
<nav class="preview-nav" aria-label="大問の選択">${cases.map(c=>`<a class="button secondary" href="#${c.id}">${esc(c.label)}</a>`).join('')}</nav></header>
<div class="preview-tools"><button type="button" class="button quiet" id="expand">この大問の詳しい解説をすべて開く</button></div>
${articles.join('\n')}
<footer><p class="small muted">内容検討用の草稿です。学習アプリへの組込み・公開はしていません。</p></footer></main>
<script>
const articles=[...document.querySelectorAll('.preview-case')],links=[...document.querySelectorAll('.preview-nav a')];
function activate(focus=false){
 const target=document.getElementById(location.hash.slice(1)),article=target?.closest('.preview-case')||articles[0];
 for(const a of articles)a.hidden=a!==article;
 for(const a of links){if(a.hash==='#'+article.id)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}
 for(const a of document.querySelectorAll('.preview-question-link')){if(a.hash===location.hash)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');}
 const destination=target||document.getElementById(article.id+'-title');
 for(let node=destination;node;node=node.parentElement)if(node.tagName==='DETAILS')node.open=true;
 if(focus)requestAnimationFrame(()=>{const node=destination.tagName==='ARTICLE'?destination.querySelector('h1'):destination;node.focus({preventScroll:true});node.scrollIntoView({block:'start'});});
}
addEventListener('hashchange',()=>activate(true));activate(!!location.hash);
document.addEventListener('click',event=>{const link=event.target.closest('a[href^="#"]');if(link&&link.hash===location.hash){event.preventDefault();activate(true);}});
document.getElementById('expand').addEventListener('click',()=>{for(const d of document.querySelector('.preview-case:not([hidden])').querySelectorAll('details'))d.open=true;});
</script></body></html>\n`);
console.log('Built local preview for '+cases.length+' draft explanations.');
