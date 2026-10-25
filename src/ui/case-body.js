import {esc} from '../utils.js';
import {questionTextHTML} from './question-text.js';

export function caseBodyHTML(c,baseURL){
 let body=c.body,html='';
 for(const f of c.bodyFigures||[]){
  const pos=body.indexOf(f.anchor);if(pos<0)continue;
  html+=questionTextHTML(body.slice(0,pos))+`<figure class="question-figure"><a href="${esc(new URL(f.image,baseURL))}" target="_blank" rel="noopener" aria-label="図を拡大する"><img src="${esc(new URL(f.image,baseURL))}" alt="${esc(f.alt)}" loading="lazy"></a><figcaption>${esc(f.caption)}</figcaption></figure>`;
  body=body.slice(pos+f.anchor.length);
 }
 return addBodyReferences(html+questionTextHTML(body),c.bodyRefs);
}

// Reference markers belong to rendered text or figure elements, never attributes.
export function addBodyReferences(html,refs={}){
 const template=document.createElement('template');template.innerHTML=html;
 const root=template.content;
 const mark=(element,id)=>{
  if(!element.id){element.id=id;element.tabIndex=-1;}
  else if(element.id!==id){const alias=document.createElement('span');alias.id=id;alias.tabIndex=-1;element.prepend(alias);}
 };
 for(const [key,ref] of Object.entries(refs||{})){
  const text=ref.text||ref.anchor;if(typeof text!=='string'||!text)continue;
  const id='written-ref-'+key;
  const figure=[...root.querySelectorAll('figure')].find(f=>f.querySelector('figcaption')?.textContent.trim()===text.trim());
  if(figure){mark(figure,id);continue;}
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let node,found=false;
  while((node=walker.nextNode())){
   if(node.parentElement?.closest('script,style,annotation,.katex-mathml'))continue;
   const offset=node.data.indexOf(text);if(offset<0)continue;
   const figure=node.parentElement?.closest('figcaption')?.closest('figure');
   if(figure)mark(figure,id);
   else {const target=node.splitText(offset);target.splitText(text.length);const span=document.createElement('span');span.id=id;span.tabIndex=-1;target.replaceWith(span);span.append(target);}
   found=true;break;
  }
  if(!found){
   // Inline emphasis may split a phrase over multiple text nodes. Mark the
   // smallest containing text block without flattening its formatting.
   const block=[...root.querySelectorAll('p,li,td,th,caption,figcaption')].filter(e=>e.textContent.includes(text)).sort((a,b)=>a.textContent.length-b.textContent.length)[0];
   if(block)mark(block.closest('figcaption')?.closest('figure')||block,id);
  }
 }
 return template.innerHTML;
}
