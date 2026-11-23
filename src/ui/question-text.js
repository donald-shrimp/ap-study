import katex from '../../assets/vendor/katex/katex.mjs';
import {esc} from '../utils.js';
import {inlineTextHTML} from './inline-text.js';

// A deliberately small, HTML-free format shared by question bodies and choices.
// No links, arbitrary tags, Markdown images, or executable LaTeX commands.
function math(expression, displayMode=false) {
  try {
    if(expression.length>4000)throw new Error('数式が長すぎます');
    return katex.renderToString(expression,{displayMode,throwOnError:true,trust:false,strict:'ignore',maxExpand:1000,output:'htmlAndMathml'});
  } catch {
    return `<span class="math-error" role="note">${esc(displayMode?'$$'+expression+'$$':'$'+expression+'$')}</span>`;
  }
}

function inline(text) {
  return inlineTextHTML(text,{renderMath:math});
}
export {inline as questionInlineHTML};

const cells = line => line.trim().replace(/^\|/,'').replace(/\|$/,'').split('|').map(c=>c.trim());
const tableSeparator = line => /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line.trim());

export function questionTextHTML(value='', {lists=false}={}) {
  const lines=String(value).replace(/\r\n?/g,'\n').split('\n');
  const listItem=line=>lists&&line.match(/^\s*(-|\d+\.) (.+)$/);
  let html='';
  for(let i=0;i<lines.length;) {
    if(!lines[i].trim()){i++;continue;}
    if(lines[i].trim().startsWith('```')) {
      const body=[];i++;
      while(i<lines.length&&!lines[i].trim().startsWith('```'))body.push(lines[i++]);
      if(i<lines.length)i++;
      html+=`<pre class="question-code"><code>${esc(body.join('\n'))}</code></pre>`;continue;
    }
    if(lines[i].trim().startsWith('$$')) {
      const body=lines[i].trim().slice(2);i++;
      if(body.endsWith('$$'))html+=`<div class="question-math">${math(body.slice(0,-2).trim(),true)}</div>`;
      else {
        const parts=[body];
        while(i<lines.length&&!lines[i].includes('$$'))parts.push(lines[i++]);
        if(i<lines.length)parts.push(lines[i++].split('$$')[0]);
        html+=`<div class="question-math">${math(parts.join('\n').trim(),true)}</div>`;
      }
      continue;
    }
    if(i+1<lines.length&&lines[i].includes('|')&&tableSeparator(lines[i+1])) {
      const header=cells(lines[i]);i+=2;const rows=[];
      while(i<lines.length&&lines[i].trim()&&lines[i].includes('|'))rows.push(cells(lines[i++]));
      html+=`<div class="question-table-scroll" tabindex="0" role="region" aria-label="問題の表"><table class="question-table"><thead><tr>${header.map(c=>`<th scope="col">${inline(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(c=>`<td>${inline(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;continue;
    }
    const first=listItem(lines[i]);
    if(first) {
      const ordered=first[1]!=='-', tag=ordered?'ol':'ul', items=[];
      for(let item=first;item&&(item[1]!=='-')===ordered;item=listItem(lines[++i]||'')) {
        items.push(`<li>${inline(item[2])}</li>`);
      }
      html+=`<${tag}${ordered?` start="${esc(first[1].slice(0,-1))}"`:''}>${items.join('')}</${tag}>`;
      continue;
    }
    const paragraph=[lines[i++]];
    while(i<lines.length&&lines[i].trim()&&!listItem(lines[i])&&!lines[i].trim().startsWith('$$')&&!lines[i].trim().startsWith('```')&&!(i+1<lines.length&&tableSeparator(lines[i+1])))paragraph.push(lines[i++]);
    html+=`<p>${inline(paragraph.join('\n'))}</p>`;
  }
  return html;
}
