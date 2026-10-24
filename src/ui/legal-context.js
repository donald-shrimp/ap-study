import {legalContextLines} from '../domain/legal-context.js';
import {esc} from '../utils.js';
export function legalContextHTML(material){
 const lines=legalContextLines(material);return lines.length?`<p class="small legal-context">${lines.map(esc).join(' · ')}</p>`:'';
}
