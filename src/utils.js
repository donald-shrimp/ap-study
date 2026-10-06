export const $ = (selector, root=document) => root.querySelector(selector);
export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const now = () => new Date().toISOString();
export const day = value => { const d = new Date(value); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
export const dateText = value => new Date(value).toLocaleDateString('ja-JP', {month:'long', day:'numeric'});
export const timeText = value => new Date(value).toLocaleString('ja-JP', {month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
