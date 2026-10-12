// AI explanation handoff. Copy and same-tab navigation are separate gestures.
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

export function createAIHandoff({getAttempt,getQuestion,getQualification,getBaseURL,beforeNavigate=()=>true}){
 const dialog=document.getElementById('ai-handoff-dialog');
 const $=id=>dialog.querySelector('#'+id);
 const buttons=[...dialog.querySelectorAll('[data-ai-provider]')];
 let provider='chatgpt',snapshot=null,operation=0,working=false,copiedText=null;
 const controls=[...buttons,$('ai-handoff-detail'),$('ai-handoff-open'),$('ai-handoff-copy-only'),$('ai-handoff-select')];
 function busy(value){working=value;for(const control of controls)control.disabled=value;$('ai-handoff-fallback').setAttribute('aria-disabled',String(value));}
 function cancel(){operation++;snapshot=null;copiedText=null;busy(false);}
 async function navigate(dest,token){
  showStatus('学習記録の保存を確認しています。');
  const saved=await beforeNavigate();
  if(token!==operation||!dialog.open)return;
  if(!saved)throw Error('学習記録を保存できなかったため、移動を止めました。問題画面の「表示・データ」から記録を書き出してください。');
  window.location.assign(dest.url);
 }
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
  $('ai-handoff-open').textContent=copiedText!==null?DESTINATIONS[name].name+'を開く ↗':'質問文をコピー';
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
  operation++;copiedText=null;busy(false);
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
 $('ai-handoff-detail').addEventListener('input',()=>{
  copiedText=null;refresh();setProvider(provider);
  $('ai-handoff-status').hidden=true;$('ai-handoff-manual').hidden=true;
 });
 $('ai-handoff-open').addEventListener('click',async()=>{
  if(working)return;
  if(copiedText!==prompt()){await copy();return;}
  const token=++operation,dest=DESTINATIONS[provider];
  busy(true);$('ai-handoff-manual').hidden=true;$('ai-handoff-status').hidden=true;
  try{
   await navigate(dest,token);
  }catch(error){
   if(token===operation&&dialog.open)showManual('質問文はコピー済みです。移動を止めました。 '+(error?.message||String(error)));
  }finally{if(token===operation)busy(false);}
 });
 $('ai-handoff-fallback').addEventListener('click',async event=>{
  event.preventDefault();if(working)return;
  const token=++operation,dest=DESTINATIONS[provider];busy(true);
  try{await navigate(dest,token);}
  catch(error){if(token===operation&&dialog.open)showManual('自動移動を止めました。'+(error?.message||String(error)));}
  finally{if(token===operation)busy(false);}
 });
 async function copy(){
  if(working)return;
  const token=++operation,text=prompt();copiedText=null;busy(true);$('ai-handoff-status').hidden=true;$('ai-handoff-manual').hidden=true;
  try{
   if(!navigator.clipboard?.writeText)throw Error('このブラウザでは自動コピーが利用できません。');
   await navigator.clipboard.writeText(text);
   if(token!==operation||!dialog.open)return;
   copiedText=text;setProvider(provider);
   showStatus('質問文をコピーしました。「'+DESTINATIONS[provider].name+'を開く」を押して、AIに貼り付けてください。');
  }catch(error){if(token===operation&&dialog.open)showManual('コピーできませんでした。下の質問文を選択してコピーしてください。（'+(error?.name||'Error')+'）');}
  finally{if(token===operation)busy(false);}
 }
 $('ai-handoff-copy-only').addEventListener('click',copy);
 $('ai-handoff-select').addEventListener('click',()=>{$('ai-handoff-manual-text').focus();$('ai-handoff-manual-text').select();});
 return {open};
}
