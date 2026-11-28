import {esc} from '../utils.js';

export function writtenTextGrid({value,limit,locked,attributes}){
 return `<span class="written-grid-wrap"><textarea class="written-text-grid" style="--answer-limit:${limit}" rows="${Math.ceil(limit/20)}" maxlength="${limit}" ${locked?'readonly':`placeholder="${limit}字以内"`} ${attributes}>
${esc(value)}</textarea></span>`;
}
