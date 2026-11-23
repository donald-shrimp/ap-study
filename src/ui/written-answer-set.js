import {answerSetValues,answerSetTextLimit,MAX_ANSWER_SET_INPUTS} from '../domain/case-answer-set.js';
import {caseCorrectChoiceIds} from '../domain/case-field.js';
import {questionTextHTML} from './question-text.js';
import {esc} from '../utils.js';

export function writtenAnswerSetHTML(field,response,key,shown){
 const {slots,maxLength}=field.answerSet;
 const locked=Boolean(response?.submittedAt),values=answerSetValues(response?.value)??(slots?slots.map(()=>''):['']);
 const data=`data-written-key="${esc(key)}"`;
 if(field.choices&&!slots){
  const correctIds=shown?caseCorrectChoiceIds(field):[];
  return `<fieldset class="written-choices choices written-set-options" data-answer-set ${locked?'disabled':''}><legend class="sr-only">${esc(field.label)}</legend>
    ${field.choices.map(choice=>{
     const selected=values.includes(choice.id),correct=correctIds.includes(choice.id);
     return `<label class="choice ${selected?'selected':''} ${correct?'correct-choice':shown&&selected?'wrong-choice':''}">
       <input type="checkbox" ${data} data-answer-set-choice value="${esc(choice.id)}" ${selected?'checked':''}>
       ${choice.text?`<span class="choice-code">${esc(choice.label)}</span><div class="choice-text">${questionTextHTML(choice.text)}</div>`:`<span class="choice-text">${esc(choice.label)}</span>`}
       ${correct?'<span class="sr-only">（正解）</span>':''}${shown&&selected?'<span class="sr-only">（あなたの回答）</span>':''}
     </label>`;
    }).join('')}
  </fieldset>`;
 }
 const rows=values.map((value,index)=>{
  const label=slots?.[index]||`回答 ${index+1}`;
  const control=field.choices?`<span class="written-set-select"><select ${data} data-answer-set-entry ${locked?'disabled':''}>
    <option value="">選択する</option>
    ${field.choices.map(choice=>`<option value="${esc(choice.id)}" ${value===choice.id?'selected':''}>${esc(choice.label+' '+choice.text)}</option>`).join('')}
  </select></span>`:`<input type="text" ${data} data-answer-set-entry autocomplete="off" maxlength="${answerSetTextLimit(field)}" value="${esc(value)}" ${locked?'readonly':''}>`;
  return `<div class="written-set-entry"><label class="written-set-label"><span class="written-set-name">${esc(label)}</span>${control}
    ${maxLength&&!locked?`<span class="written-set-limit small muted">${maxLength}字以内</span>`:''}</label>
    ${!slots&&!locked&&values.length>1?`<button class="button quiet" type="button" data-action="written-set-remove" ${data} data-index="${index}" aria-label="${esc(label)}を削除">削除</button>`:''}</div>`;
 }).join('');
 return `<div class="written-set-inputs ${slots?'written-set-fixed':''}" data-answer-set>${rows}
  ${!slots&&!locked&&values.length<MAX_ANSWER_SET_INPUTS?`<button class="button quiet" type="button" data-action="written-set-add" ${data}>＋ 回答欄を追加</button>`:''}
 </div>`;
}
