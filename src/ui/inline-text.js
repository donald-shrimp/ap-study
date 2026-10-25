import {esc} from '../utils.js';

const emphasis=/\*\*(?<strong>[^*\r\n]+)\*\*/g;
const questionInline=/\$(?<math>[^$\n]+)\$|\*\*(?<strong>[^*\r\n]+)\*\*|\+\+(?<underline>[^+\n]+)\+\+/g;

// Explanations accept only emphasis. Rich question blocks opt into their existing
// math/underline syntax; raw content is always escaped before creating markup.
export function inlineTextHTML(value='',{renderMath}={}) {
  const text=String(value??''),pattern=renderMath?questionInline:emphasis;
  let html='',offset=0;
  for(const match of text.matchAll(pattern)) {
    html+=esc(text.slice(offset,match.index));
    const {math,strong,underline}=match.groups;
    html+=math!==undefined?renderMath(math):strong!==undefined?`<strong>${esc(strong)}</strong>`:`<u>${esc(underline)}</u>`;
    offset=match.index+match[0].length;
  }
  return html+esc(text.slice(offset));
}
