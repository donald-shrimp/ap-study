export const $ = (selector, root=document) => root.querySelector(selector);
export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const now = () => new Date().toISOString();
export const day = value => { const d = new Date(value); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
export const dateText = value => new Date(value).toLocaleDateString('ja-JP', {month:'long', day:'numeric'});
export const timeText = value => new Date(value).toLocaleString('ja-JP', {month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});

/**
 * Render only **bold** markers in authored explanation text.
 * Escape each segment before adding our own strong element; never interpret HTML,
 * links, arbitrary Markdown, or unmatched asterisks.
 */
export function answerTextHTML(value='') {
  const source=String(value??'');
  const marker=/\*\*([^*\r\n]+)\*\*/g;
  let html='',offset=0;
  for(const m of source.matchAll(marker)){
    html+=esc(source.slice(offset,m.index));
    html+=`<strong class="answer-emphasis">${esc(m[1])}</strong>`;
    offset=m.index+m[0].length;
  }
  return html+esc(source.slice(offset));
}
