// AI explanation handoff. Clipboard success precedes same-tab navigation.
// No AI API, study-record mutation, or unverified OCR transcription.
const DESTINATIONS=Object.freeze({
 chatgpt:{name:'ChatGPT',url:'https://chatgpt.com/'},
 gemini:{name:'Gemini',url:'https://gemini.google.com/'},
 claude:{name:'Claude',url:'https://claude.ai/'}
});
export {DESTINATIONS};

function nonempty(value){return typeof value==='string'?value.trim():'';}
function urlFor(src,baseURL) {
 if(!src)return '';
 try{const url=new URL(src,baseURL);return ['http:','https:'].includes(url.protocol)?url.href:'';}catch{return '';}
}
function imageURLs(q,baseURL){return [...new Set([...(q.sourceImages||[]),q.image].map(src=>urlFor(src,baseURL)).filter(Boolean))];}
function formatChoice(choice,baseURL) {
 let body=nonempty(choice.text)||'（本文なし・画像や原本を確認）';
 const image=urlFor(choice.image,baseURL);
 if(image)body+=' [選択肢画像: '+image+']';
 return nonempty(choice.label)+'：'+body;
}

export function buildAIPrompt({question:q,attempt:a,qualification,detail='',baseURL}){
 if(!q||!a||!['correct','assisted','incorrect','revealed'].includes(a.status))throw Error('解答後の問題だけAIに渡せます。');
 const choices=Array.isArray(q.choices)?q.choices:[];
 if(!choices.length||!Number.isInteger(q.answer)||!choices[q.answer])throw Error('選択肢と正解の情報がありません。');
 const selected=Number.isInteger(a.selected)&&choices[a.selected]?formatChoice(choices[a.selected],baseURL):'回答せず、解答を確認';
 const images=imageURLs(q,baseURL).map((src,i)=>'原本・図 '+(i+1)+'：'+src);
 const prompt=[
  '資格試験のこの問題について、既存の解説を読んでも理解できませんでした。日本語で分かりやすく説明してください。何を問う問題か、必要な用語、解法を考える順番、計算や判断の根拠を省略せず、最後に確認問題を1つ出してください。',
  '【試験・問題】',
  nonempty(qualification?.name)||nonempty(qualification?.shortName)||'資格試験',
  [nonempty(q.packLabel),q.number!=null?'問'+q.number:'',nonempty(q.title)].filter(Boolean).join(' · '),
  '【問題文】',
  nonempty(q.stem)||'この問題は原本画像で掲載されています。原文の文字起こしは確認できていません。画像を見られない場合は推測せず、画像の添付を依頼してください。',
  '【選択肢】',
  choices.map(c=>formatChoice(c,baseURL)).join('\n'),
  '【正解】',
  formatChoice(choices[q.answer],baseURL),
  '【私の回答】',
  selected,
  '【採点結果】',
  ({correct:'自力正解',assisted:'ヒントを使って正解',incorrect:'不正解',revealed:'解答を閲覧'})[a.status],
  '【ひと問の解答解説】',
  nonempty(q.explanation)||nonempty(q.summary)||'解説なし',
  '【各選択肢の理由】',
  (Array.isArray(q.choiceReasons)?q.choiceReasons:[]).map((reason,i)=>nonempty(reason)?nonempty(choices[i]?.label||String(i+1))+'：'+reason:'').filter(Boolean).join('\n')||'記載なし',
  '【教材の段階ヒント（実際に閲覧した履歴とは別）】',
  (Array.isArray(q.hints)?q.hints:[]).map((hint,i)=>(i+1)+'. '+nonempty(hint.text)).join('\n')||'記載なし',
  '【特に聞きたいこと】',
  nonempty(detail)||'どこから考えればよいかを含め、基本からお願いします。'
 ];
 if(nonempty(q.questionUrl))prompt.push('【公式問題・出典】',urlFor(q.questionUrl,baseURL));
 if(images.length)prompt.push('【問題画像・図】',images.join('\n'),'※画像URLがAIから参照できない場合は、元の学習画面から画像を添付してください。');
 return prompt.join('\n\n');
}

export function createAIHandoff({getAttempt,getQuestion,getQualification,getBaseURL}){
 const dialog=document.getElementById('ai-handoff-dialog');
 const $=id=>dialog.querySelector('#'+id);
 const buttons=[...dialog.querySelectorAll('[data-ai-provider]')];
 let provider='chatgpt',snapshot=null,operation=0;
 const controls=[...buttons,$('ai-handoff-detail'),$('ai-handoff-open'),$('ai-handoff-copy-only'),$('ai-handoff-select')];
 function busy(value){for(const control of controls)control.disabled=value;}
 function cancel(){operation++;snapshot=null;busy(false);}
 function prompt(){
  if(!snapshot)throw Error('質問する問題を開き直してください。');
  return buildAIPrompt({...snapshot,detail:$('ai-handoff-detail').value});
 }
 function refresh(){
  const text=prompt();
  $('ai-handoff-preview').value=text;
  $('ai-handoff-manual-text').value=text;
 }
 function showStatus(message){$('ai-handoff-status').textContent=message;$('ai-handoff-status').hidden=false;}
 function setProvider(name){
  if(!Object.hasOwn(DESTINATIONS,name))return;
  provider=name;
  for(const b of buttons)b.setAttribute('aria-pressed',String(b.dataset.aiProvider===name));
  $('ai-handoff-open').textContent='質問文をコピーして'+DESTINATIONS[name].name+'を開く ↗';
  $('ai-handoff-fallback').textContent=DESTINATIONS[name].name+'を開く ↗';
  $('ai-handoff-fallback').href=DESTINATIONS[name].url;
 }
 function showManual(message){
  refresh();
  $('ai-handoff-manual').hidden=false;
  showStatus(message);
 }
 function open(){
  const attempt=getAttempt();
  if(!attempt||!['correct','assisted','incorrect','revealed'].includes(attempt.status))return false;
  const question=getQuestion(attempt);
  if(!question)return false;
  operation++;busy(false);
  snapshot=structuredClone({question,attempt,qualification:getQualification(),baseURL:getBaseURL()});
  $('ai-handoff-detail').value='';
  $('ai-handoff-status').hidden=true;
  $('ai-handoff-manual').hidden=true;
  $('ai-handoff-prompt-details').open=false;
  const links=$('ai-handoff-images');
  links.replaceChildren();
  const urls=imageURLs(question,snapshot.baseURL);
  for(const [i,src] of urls.entries()){
   const a=document.createElement('a');
   a.className='button secondary';
   a.textContent='問題画像・図 '+(i+1)+' を開く ↗';
   a.href=src;
   a.target='_blank';a.rel='noopener';
   links.append(a);
  }
  $('ai-handoff-image-info').hidden=urls.length===0;
  setProvider('chatgpt');
  refresh();
  dialog.showModal();
  return true;
 }
 for(const button of buttons)button.addEventListener('click',()=>{setProvider(button.dataset.aiProvider);$('ai-handoff-status').hidden=true;});
 $('ai-handoff-close').addEventListener('click',()=>{cancel();dialog.close();});
 dialog.addEventListener('cancel',cancel);
 dialog.addEventListener('close',()=>{if(!dialog.open)cancel();});
 $('ai-handoff-detail').addEventListener('input',refresh);
 $('ai-handoff-open').addEventListener('click',async()=>{
  const token=++operation,dest=DESTINATIONS[provider],text=prompt();
  let copied=false;
  busy(true);$('ai-handoff-manual').hidden=true;$('ai-handoff-status').hidden=true;
  try{
   if(!navigator.clipboard?.writeText)throw Error('このブラウザでは自動コピーが利用できません。');
   await navigator.clipboard.writeText(text);
   if(token!==operation||!dialog.open)return;
   copied=true;
   // Android Chrome/PWA: do not call window.open before copying; the tested
   // behavior navigates this tab only after clipboard success.
   window.location.assign(dest.url);
  }catch(error){
   if(token===operation&&dialog.open)showManual((copied?'コピーはできましたが、移動に失敗しました。':'自動コピーに失敗しました。')+' '+(error?.name||'Error')+'：'+(error?.message||String(error))+' 下の質問文を手動でコピーしてください。');
  }finally{if(token===operation)busy(false);}
 });
 $('ai-handoff-copy-only').addEventListener('click',async()=>{
  const token=++operation,text=prompt();busy(true);$('ai-handoff-status').hidden=true;
  try{
   if(!navigator.clipboard?.writeText)throw Error('自動コピー不可');
   await navigator.clipboard.writeText(text);
   if(token!==operation||!dialog.open)return;
   showStatus('質問文をコピーしました。AIに貼り付けてください。');
  }catch(error){if(token===operation&&dialog.open)showManual('コピーできませんでした。下の質問文を選択してコピーしてください。（'+(error?.name||'Error')+'）');}
  finally{if(token===operation)busy(false);}
 });
 $('ai-handoff-select').addEventListener('click',()=>{$('ai-handoff-manual-text').focus();$('ai-handoff-manual-text').select();});
 return {open};
}
