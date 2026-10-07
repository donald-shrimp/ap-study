import {labels, complete} from '../domain/study.js';

const text = (v,max=20000) => typeof v==='string' && v.length<=max;
const date = v => typeof v==='string' && !Number.isNaN(new Date(v).valueOf());
const id = v => text(v,100) && /^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(v);
const materialFields = ['hints','summary','explanation','takeaway','revision','enrichment','hintStatus','choiceReasons'];
const questionFields = ['id','version','number','title','topic','topicId','concept','topicDescription','field','related','source','page','year','season','questionUrl','answerUrl','stem','sourceImages','imageSizes','choices','answer','image','imageAlt','adaptation','enrichment','hintStatus','qualificationId','examPartId','packId','packLabel','type','correctChoiceId','hintCount','diagnosticOnly','parentQuestionId'];
const safeURL = value => {
  if (value===undefined || value===null || value==='') return true;
  if (!text(value,4000) || /[<>"'\r\n]/.test(value)) return false;
  try { return ['http:','https:'].includes(new URL(value, 'https://example.invalid/').protocol); } catch { return false; }
};

function material(m, choices, diagnosticOnly=false) {
  return m && Object.keys(m).every(k=>materialFields.includes(k))
    && (m.enrichment===undefined||['reviewed','topic-guide','personal'].includes(m.enrichment))
    && (m.hintStatus===undefined||['individual','topic-guide'].includes(m.hintStatus))
    && (m.choiceReasons===undefined||Array.isArray(m.choiceReasons)&&[0,choices].includes(m.choiceReasons.length)&&m.choiceReasons.every(r=>text(r)))
    && Array.isArray(m.hints) && m.hints.length>=(diagnosticOnly?0:1) && m.hints.length<=20
    && m.hints.every(h=>h && Object.keys(h).every(k=>['title','text','revealsAnswer'].includes(k)) && text(h.title,100) && text(h.text,10000) && typeof h.revealsAnswer==='boolean')
    && ['summary','explanation','takeaway'].every(k=>text(m[k]));
}

function questionSnapshot(q, qualificationId) {
  return q && Object.keys(q).every(k=>questionFields.includes(k)) && id(q.id)
    && (q.diagnosticOnly===undefined&&q.parentQuestionId===undefined||q.diagnosticOnly===true&&id(q.parentQuestionId)&&q.parentQuestionId!==q.id)
    && q.qualificationId===qualificationId && q.type==='singleChoice'
    && Number.isInteger(q.version) && text(q.title) && text(q.topic)
    && Array.isArray(q.choices) && q.choices.length>=2 && q.choices.length<=20
    && new Set(q.choices.map(c=>c.id)).size===q.choices.length
    && q.choices.every(c=>c && Object.keys(c).every(k=>['id','label','text','image'].includes(k)) && id(c.id) && text(c.label,100) && (c.text===undefined||text(c.text)) && safeURL(c.image))
    && Number.isInteger(q.answer) && q.answer>=0 && q.answer<q.choices.length && q.choices[q.answer].id===q.correctChoiceId
    && Array.isArray(q.sourceImages) && q.sourceImages.every(safeURL)
    && Array.isArray(q.imageSizes) && q.imageSizes.length===q.sourceImages.length
    && q.imageSizes.every(s=>s && Number.isFinite(s.width) && s.width>0 && Number.isFinite(s.height) && s.height>0)
    && Array.isArray(q.related) && q.related.every(id)
    && ['image','questionUrl','answerUrl'].every(k=>safeURL(q[k]))
    && ['stem','source','adaptation'].every(k=>text(q[k]));
}

export function createStateValidator({getQuestions,getTopics,getQualification,allowDiagnosticOnly=false}) {
  return function validateState(s) {
    const base=getQuestions(), topics=getTopics(), qualification=getQualification();
    const fail=()=>{throw new Error('この資格の有効な学習記録ファイルではありません。現在の記録は変更していません。');};
    if(!s||s.version!==1||!Array.isArray(s.attempts)||s.attempts.length>20000||!['home','study','review','history','materials','topics','planning','diagnostics','diagnostic'].includes(s.view)||!s.settings||typeof s.settings.largeText!=='boolean'||!s.session||!Array.isArray(s.session.attemptIds)||!s.overrides||Array.isArray(s.overrides)||typeof s.overrides!=='object')fail();
    s.currentRunId??=null;if(s.currentRunId!==null&&!id(s.currentRunId))fail();s.readingNotes??={};s.session.topic??=null;delete s.settings.sessionSize;delete s.session.goal;
    if(s.session.examPartId!==undefined&&s.session.examPartId!==null&&!(qualification?.examParts||[{id:qualification?.defaultExamPartId||'objective'}]).some(p=>p.id===s.session.examPartId))fail();
    if(!s.readingNotes||Array.isArray(s.readingNotes)||typeof s.readingNotes!=='object'||!(s.session.topic===null||text(s.session.topic,200))||(s.session.topicId!==undefined&&s.session.topicId!==null&&!id(s.session.topicId)))fail();
    for(const [topic,note] of Object.entries(s.readingNotes))if(!text(topic,100)||topic==='__proto__'||!text(note,200))fail();
    const ids=new Set(), byId=new Map(base.map(q=>[q.id,q]));
    for(const a of s.attempts) {
      if(!a||!id(a.id)||ids.has(a.id)||!id(a.questionId)||!Object.hasOwn(labels,a.status))fail();
      if(a.continuationOf!==undefined&&(!id(a.continuationOf)||a.continuationOf===a.id||!date(a.continuedAt)))fail();
      if(a.importedFrom!==undefined&&!text(a.importedFrom,201))fail();
      if(a.qualificationId!==undefined&&a.qualificationId!==qualification.id)fail();
      if(a.questionSnapshot && (!questionSnapshot(a.questionSnapshot,qualification.id)||a.questionSnapshot.id!==a.questionId))fail();
      const q=a.questionSnapshot||byId.get(a.questionId);
      if(!q || q.diagnosticOnly&&!allowDiagnosticOnly || !material(a.materialSnapshot,q.choices.length,Boolean(q.diagnosticOnly)))fail();
      if(!(a.topic===undefined||a.topic===null||a.topic===q.topic)||!(a.readingNote===undefined||text(a.readingNote,200)))fail();
      if(!date(a.startedAt)||!date(a.updatedAt)||!(a.selected===null||Number.isInteger(a.selected)&&a.selected>=0&&a.selected<q.choices.length)||!Number.isInteger(a.hintCount)||a.hintCount<0||a.hintCount>a.materialSnapshot.hints.length||typeof a.confidence!=='boolean'||typeof a.answerViewedBefore!=='boolean'||!Number.isFinite(a.scrollY)||a.scrollY<0||!text(a.contentRevision,100)||!Number.isInteger(a.questionVersion))fail();
      if(a.selectedChoiceId!==undefined && a.selectedChoiceId!==(a.selected===null?null:q.choices[a.selected].id))fail();
      if(complete(a)?!date(a.completedAt)||!Number.isInteger(a.hintsBeforeAnswer)||a.hintsBeforeAnswer<0||a.hintsBeforeAnswer>a.hintCount:a.completedAt!==null||a.hintsBeforeAnswer!==null)fail();
      if(!Array.isArray(a.hintEvents)||a.hintEvents.length!==a.hintCount||a.hintEvents.some((e,i)=>!e||e.step!==i+1||!date(e.at)||!['before','after'].includes(e.phase)))fail();
      if(a.status==='correct'&&(a.selected!==q.answer||a.hintsBeforeAnswer!==0||a.answerViewedBefore)||a.status==='assisted'&&(a.selected!==q.answer||a.hintsBeforeAnswer===0||a.answerViewedBefore)||a.status==='incorrect'&&(a.selected===null||a.selected===q.answer)||a.status==='revealed'&&!a.answerViewedBefore)fail();
      ids.add(a.id);
    }
    if(s.currentId!==null&&!ids.has(s.currentId)||s.session.attemptIds.some(id=>!ids.has(id))||new Set(s.session.attemptIds).size!==s.session.attemptIds.length)fail();
    if(s.session.topic&&s.session.attemptIds.some(id=>{const a=s.attempts.find(a=>a.id===id);const q=a.questionSnapshot||byId.get(a.questionId);return s.session.topicId?q.topicId!==s.session.topicId:q.topic!==s.session.topic;}))fail();
    if(s.session.examPartId&&s.session.attemptIds.some(id=>{const a=s.attempts.find(a=>a.id===id),q=a.questionSnapshot||byId.get(a.questionId);return (q.examPartId||qualification.defaultExamPartId)!==s.session.examPartId;}))fail();
    for(const [id,m] of Object.entries(s.overrides)){const q=byId.get(id)||s.attempts.find(a=>a.questionId===id&&a.questionSnapshot)?.questionSnapshot;if(!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(id)||!material(m,q?.choices.length||m.choiceReasons?.length||0)||!text(m.revision,100))fail();}
    return s;
  };
}
