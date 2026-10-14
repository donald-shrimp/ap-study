// A case is one learning record with several responses. Completion requires
// every field to be submitted and assessed; unsure is an explicit self rating.
export const SELF_OUTCOMES=Object.freeze({meets:'要点を満たした',partial:'一部足りない',notYet:'解けなかった',unsure:'判断に迷う'});
const copy=v=>structuredClone(v),stamp=()=>new Date().toISOString();
export const fieldKey=(item,field)=>item.id+'--'+field.id;
export const caseFields=c=>c.items.flatMap(item=>item.fields.map(field=>({item,field,key:fieldKey(item,field)})));
const normalize=s=>s.normalize('NFKC').trim();
export function createCaseRun(c,{mode='learning',at=stamp(),id='case--'+crypto.randomUUID()}={}){
 if(!['learning','exam'].includes(mode)||c.status!=='reviewed')throw Error('確認済みの大問を指定してください。');
 return {format:'hitomon-learning-record',version:2,kind:'case',id,qualificationId:c.qualificationId,examPartId:c.examPartId,caseId:c.id,caseVersion:c.version,material:copy(c),mode,responses:{},assistance:{firstAnswerViewedAt:null,viewedFields:[]},progress:{status:'in_progress',currentItemId:c.items[0].id,bodyScroll:0,pane:'questions'},startedAt:at,updatedAt:at,completedAt:null};
}
export function updateCaseStatus(run,at=stamp()){
 const fields=caseFields(run.material),submitted=fields.filter(x=>run.responses[x.key]?.submittedAt),evaluated=submitted.filter(x=>run.responses[x.key].evaluation);
 run.progress.status=submitted.length===fields.length?(evaluated.length===fields.length?'completed':'awaiting_evaluation'):run.progress.status==='partially_completed'?'partially_completed':'in_progress';
 run.completedAt=run.progress.status==='completed'?run.completedAt||at:null;run.updatedAt=at;return run;
}
export function setCaseResponse(run,key,value,at=stamp()){
 const slot=caseFields(run.material).find(x=>x.key===key);if(!slot||run.responses[key]?.submittedAt||run.progress.status==='completed')throw Error('確定した回答は変更できません。新しく解き直してください。');
 if(typeof value!=='string'||(slot.field.type==='singleChoice'?!slot.field.choices.some(c=>c.id===value):[...value].length>(slot.field.maxLength||2000)))throw Error('回答の形式・字数を確認してください。');
 run.responses[key]={value,submittedAt:null,evaluation:null};run.updatedAt=at;
}
export function submitCaseField(run,key,at=stamp()){
 const slot=caseFields(run.material).find(x=>x.key===key),response=run.responses[key];if(!slot||!response?.value.trim()||response.submittedAt)throw Error('回答を入力してください。');
 const f=slot.field;response.submittedAt=at;const value=f.type==='singleChoice'?f.choices.find(c=>c.id===response.value).label:normalize(response.value),correct=f.referenceAnswers.some(v=>normalize(v)===value);
 // Unrecognized short-text answers need human evaluation, not a guessed fail.
 if(f.type==='singleChoice'||f.grading.method==='exactText'&&correct)response.evaluation={source:'automatic',outcome:correct?'correct':'incorrect',at,assisted:!!run.assistance.firstAnswerViewedAt};
 updateCaseStatus(run,at);return response;
}
export function mayViewAnswer(run,key){return !!run.responses[key]?.submittedAt&&(run.mode==='learning'||caseFields(run.material).every(x=>run.responses[x.key]?.submittedAt)||run.progress.status==='partially_completed');}
export function viewCaseAnswer(run,key,at=stamp()){
 if(!mayViewAnswer(run,key))throw Error('先に回答を確定してください。');
 if(!run.assistance.viewedFields.includes(key)){run.assistance.viewedFields.push(key);run.assistance.firstAnswerViewedAt??=at;run.updatedAt=at;}
}
export function rateCaseField(run,key,outcome,at=stamp()){
 if(!Object.hasOwn(SELF_OUTCOMES,outcome)||!mayViewAnswer(run,key)||!run.assistance.viewedFields.includes(key)||run.responses[key].evaluation)throw Error('解答例を確認してから自己評価してください。');
 run.responses[key].evaluation={source:'self',outcome,at,assisted:run.assistance.firstAnswerViewedAt<run.responses[key].submittedAt};updateCaseStatus(run,at);
}
export function caseResult(run){
 const slots=caseFields(run.material),automatic=slots.map(x=>run.responses[x.key]).filter(r=>r?.evaluation?.source==='automatic'),self=slots.map(x=>run.responses[x.key]).filter(r=>r?.evaluation?.source==='self');
 return {total:slots.length,submitted:slots.filter(x=>run.responses[x.key]?.submittedAt).length,evaluated:automatic.length+self.length,automatic:{count:automatic.length,correct:automatic.filter(r=>r.evaluation.outcome==='correct').length},self:Object.fromEntries(Object.keys(SELF_OUTCOMES).map(k=>[k,self.filter(r=>r.evaluation.outcome===k).length]))};
}
export function validateCaseRun(run,qualification){
 const fail=()=>{throw Error('大問の学習記録を確認できません。');},allowed=['format','version','kind','id','qualificationId','examPartId','caseId','caseVersion','material','mode','responses','assistance','progress','startedAt','updatedAt','completedAt'];
 if(!run||Object.keys(run).some(k=>!allowed.includes(k))||run.format!=='hitomon-learning-record'||run.version!==2||run.kind!=='case'||!/^case--[\w-]{1,90}$/.test(run.id)||run.qualificationId!==qualification.id||!qualification.examParts.some(p=>p.id===run.examPartId&&p.unit==='cases')||run.material?.id!==run.caseId||run.material?.version!==run.caseVersion||run.material.qualificationId!==run.qualificationId||run.material.examPartId!==run.examPartId||run.material.status!=='reviewed'||!['learning','exam'].includes(run.mode)||!run.responses||Array.isArray(run.responses)||!run.assistance||!Array.isArray(run.assistance.viewedFields)||!run.progress||!['in_progress','partially_completed','awaiting_evaluation','completed'].includes(run.progress.status)||!run.material.items.some(i=>i.id===run.progress.currentItemId)||!Number.isFinite(run.progress.bodyScroll)||run.progress.bodyScroll<0||run.progress.bodyScroll>10000000||!['questions','body'].includes(run.progress.pane))fail();
 const slots=caseFields(run.material),known=new Map(slots.map(x=>[x.key,x.field]));if(new Set(run.assistance.viewedFields).size!==run.assistance.viewedFields.length||run.assistance.viewedFields.some(k=>!known.has(k)))fail();
 const date=v=>typeof v==='string'&&/^\d{4}-\d\d-\d\dT.*Z$/.test(v)&&Number.isFinite(Date.parse(v));if(!date(run.startedAt)||!date(run.updatedAt)||Date.parse(run.updatedAt)<Date.parse(run.startedAt)||run.completedAt!==null&&!date(run.completedAt)||run.assistance.firstAnswerViewedAt!==null&&!date(run.assistance.firstAnswerViewedAt))fail();
 for(const [key,r] of Object.entries(run.responses)){const f=known.get(key);if(!f||Object.keys(r).some(k=>!['value','submittedAt','evaluation'].includes(k))||typeof r.value!=='string'||(f.type==='singleChoice'?!f.choices.some(c=>c.id===r.value):[...r.value].length>(f.maxLength||2000))||r.submittedAt!==null&&(!date(r.submittedAt)||!r.value.trim())||r.evaluation&&!r.submittedAt)fail();if(r.evaluation){const e=r.evaluation;if(Object.keys(e).some(k=>!['source','outcome','at','assisted'].includes(k))||!date(e.at)||typeof e.assisted!=='boolean'||!(e.source==='self'&&Object.hasOwn(SELF_OUTCOMES,e.outcome)||e.source==='automatic'&&['correct','incorrect'].includes(e.outcome)))fail();if(e.source==='automatic'){const value=f.type==='singleChoice'?f.choices.find(c=>c.id===r.value).label:normalize(r.value),right=f.referenceAnswers.some(v=>normalize(v)===value);if(f.grading.method!=='exactText'||(e.outcome==='correct')!==right||f.type!=='singleChoice'&&!right)fail();}}}
 if(run.assistance.viewedFields.some(k=>!run.responses[k]?.submittedAt)||Boolean(run.assistance.firstAnswerViewedAt)!==Boolean(run.assistance.viewedFields.length))fail();
 const result=caseResult(run);if((run.progress.status==='completed')!==(result.evaluated===slots.length)||Boolean(run.completedAt)!==(run.progress.status==='completed')||run.progress.status==='awaiting_evaluation'&&(result.submitted!==slots.length||result.evaluated===slots.length))fail();return run;
}
export function buildWrittenAIPrompt({question:c,attempt,detail='',baseURL}){
 const slot=caseFields(c).find(x=>x.key===attempt.fieldKey);if(!slot||!attempt.response?.submittedAt)throw Error('回答を確定した小問だけAIに渡せます。');
 return ['科目Bのこの設問を、日本語で噛み砕いて説明してください。本文の根拠、因果関係、解答の組み立て方を示してください。自己評価を公式点数や合格可能性へ読み替えないでください。',c.source+' · '+slot.item.label,'【共通本文】\n'+c.body,'【設問】\n'+slot.item.prompt,'【解答欄】\n'+slot.field.label+'\n'+(slot.field.constraints||[]).join('\n'),slot.field.choices?'【選択肢】\n'+slot.field.choices.map(x=>x.label+'：'+x.text).join('\n'):'','【私の回答】\n'+(slot.field.choices?.find(x=>x.id===attempt.response.value)?.text||attempt.response.value),'【公式解答例】\n'+slot.field.referenceAnswers.join('\n'),'【解説】\n'+slot.field.explanation,'【確認ポイント】\n'+slot.field.rubric.join('\n'),'【特に聞きたいこと】\n'+(detail.trim()||'基本からお願いします。'),'【原本・図】\n'+[...c.sourceImages,...c.bodyFigures.map(f=>f.image)].map(p=>new URL(p,baseURL).href).join('\n'),'画像URLを見られない場合は推測せず画像の添付を依頼してください。'].filter(Boolean).join('\n\n');
}
