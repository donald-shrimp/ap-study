// Purpose, provenance, and optional links are separate from the answer format.
export const QUESTION_USES=Object.freeze(['practice','diagnostic','mock']);
export const SOURCE_KINDS=Object.freeze(['official','authored','derived']);
export const contentId=v=>typeof v==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(v);
export function questionUses(q){return q?.uses||(q?.diagnosticOnly?['diagnostic','mock']:['practice','diagnostic']);}
export const canUseQuestion=(q,use)=>questionUses(q).includes(use);
export const questionOrigin=q=>q.sourceKind||(q.parentQuestionId?'derived':'official');
export const questionFamily=q=>q.familyId||q.parentQuestionId||q.id;
export const questionKind=q=>questionOrigin(q)==='official'?'original':questionOrigin(q);
const record=v=>v&&typeof v==='object'&&!Array.isArray(v);
const language=v=>typeof v==='string'&&/^[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8})*$/.test(v);
const label=v=>typeof v==='string'&&v.length>0&&v.length<=300;
const calendarDate=v=>typeof v==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(v)&&!Number.isNaN(Date.parse(v))&&new Date(v).toISOString().slice(0,10)===v;
export function validQuestionPolicy(q){
 const uses=questionUses(q),origin=questionOrigin(q);
 return Array.isArray(uses)&&uses.length>0&&uses.length<=3&&new Set(uses).size===uses.length&&uses.every(u=>QUESTION_USES.includes(u))
  && SOURCE_KINDS.includes(origin)
  && (q.diagnosticOnly===undefined||q.diagnosticOnly===true&&!uses.includes('practice'))
  && (origin==='derived'?contentId(q.parentQuestionId)&&q.parentQuestionId!==q.id:q.parentQuestionId===undefined)
  && (q.familyId===undefined||contentId(q.familyId))
  && (q.syllabusId===undefined||contentId(q.syllabusId))
  && (q.language===undefined||language(q.language))
  && (q.syllabus===undefined||record(q.syllabus)&&Object.keys(q.syllabus).every(k=>['id','label','language','effectiveFrom','effectiveTo'].includes(k))&&q.syllabus.id===q.syllabusId&&label(q.syllabus.label)&&language(q.syllabus.language)&&['effectiveFrom','effectiveTo'].every(k=>q.syllabus[k]===undefined||calendarDate(q.syllabus[k]))&&(!q.syllabus.effectiveFrom||!q.syllabus.effectiveTo||q.syllabus.effectiveFrom<=q.syllabus.effectiveTo))
  && (q.objectiveIds===undefined||Array.isArray(q.objectiveIds)&&q.objectiveIds.length<=20&&new Set(q.objectiveIds).size===q.objectiveIds.length&&q.objectiveIds.every(contentId))
  && (q.objectivesSnapshot===undefined||Array.isArray(q.objectivesSnapshot)&&q.objectivesSnapshot.length===(q.objectiveIds?.length||0)&&q.objectivesSnapshot.every((o,i)=>record(o)&&Object.keys(o).every(k=>['id','label','topicId'].includes(k))&&o.id===q.objectiveIds[i]&&label(o.label)&&contentId(o.topicId)))
  && (q.sourceRefs===undefined||Array.isArray(q.sourceRefs)&&q.sourceRefs.length<=10&&q.sourceRefs.every(url=>{try{return typeof url==='string'&&url.length<=4000&&!/[<>"\x00-\x1f]/.test(url)&&['http:','https:'].includes(new URL(url).protocol);}catch{return false;}}));
}
