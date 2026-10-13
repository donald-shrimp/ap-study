import {examPartsFor} from './planning.js';
import {canUseQuestion,questionFamily,questionOrigin,validQuestionPolicy} from './content-policy.js';
import {diagnosticPolicy,diagnosticSize,validDiagnosticBlueprint,MIN_DIAGNOSTIC_SIZE,DEFAULT_DIAGNOSTIC_SIZE} from './assessment-policy.js';
import {shuffle,weightedQuotas} from './assessment-sampling.js';
import {createAssessment,validateAssessment} from './assessment.js';
export {createAssessment,validateAssessment};
export {submitAssessment as submitDiagnostic,finishAssessment as finishDiagnostic,assessmentAttempts as diagnosticAttempts,assessmentExposure as diagnosticExposure,assessmentResult as diagnosticResult,assessmentSlots as diagnosticSlots} from './assessment.js';
export const DIAGNOSTIC_SIZE=DEFAULT_DIAGNOSTIC_SIZE;
export const DIAGNOSTIC_BLUEPRINT_VERSION=4;
export const diagnosticFamily=questionFamily;

export function diagnosticPool(questions,qualification,extras=[]){
 const parts=new Set(examPartsFor(qualification).filter(p=>p.practiceAvailable).map(p=>p.id));
 const all=new Map([...questions,...extras].map(q=>[q.id,q]));
 if(all.size!==questions.length+extras.length||extras.some(q=>canUseQuestion(q,'practice')||q.qualificationId&&q.qualificationId!==qualification.id||!validQuestionPolicy(q)))throw new Error('受験専用教材の用途・資格を確認できません。');
 for(const q of extras){if(questionOrigin(q)==='derived'){const parent=all.get(q.parentQuestionId);if(!parent||parent.topicId!==q.topicId||(parent.examPartId||qualification.defaultExamPartId||'objective')!==(q.examPartId||qualification.defaultExamPartId||'objective')||questionOrigin(parent)==='derived'||questionFamily(q)!==questionFamily(parent))throw new Error('派生教材の母問題・分野・パートを確認できません。');}}
 const scopes=new Map();for(const q of all.values()){const key=questionFamily(q),scope=[q.topicId,q.examPartId||qualification.defaultExamPartId||'objective'].join(':');if(scopes.has(key)&&scopes.get(key)!==scope)throw new Error('同じ内容の問題の分野・パートが一致しません。');scopes.set(key,scope);}
 return [...questions,...extras].filter(q=>q.enrichment!=='topic-guide'&&canUseQuestion(q,'diagnostic')&&(!q.qualificationId||q.qualificationId===qualification.id)&&parts.has(q.examPartId||qualification.defaultExamPartId||'objective'));
}
export function selectDiagnostic(questions,qualification,attempts=[],random=Math.random,extras=[]){
 // Direct domain callers may use the 30-question default; the UI requires an
 // explicit blueprint to enable diagnostics for a qualification.
 const configured=qualification.diagnosticBlueprint?qualification:{...qualification,diagnosticBlueprint:{size:DEFAULT_DIAGNOSTIC_SIZE}};
 const size=diagnosticSize(configured),policy=diagnosticPolicy(configured);
 if(!validDiagnosticBlueprint(configured))throw new Error('診断の出題設定を確認できません。');
 const eligible=diagnosticPool(questions,configured,extras),validTopics=new Set(configured.topics.map(t=>t.id));
 if(eligible.some(q=>!validTopics.has(q.topicId))||new Set(eligible.map(questionFamily)).size<size)throw new Error(`診断には内容が異なる${size}問以上必要です。通常学習は利用できます。`);
 const seen=new Set(attempts.map(a=>a.questionId)),priority=q=>(seen.has(q.id)?2:0)+(canUseQuestion(q,'practice')?1:0);
 const topics=shuffle(configured.topics.map(t=>t.id),random),groups=new Map(topics.map(id=>[id,shuffle(eligible.filter(q=>q.topicId===id),random).sort((a,b)=>priority(a)-priority(b))]));
 const result=[],families=new Set(),derivedCounts=new Map(),counts=new Map(),quotas=policy.sampling==='topic-weighted'?weightedQuotas(policy.weights,size):null;
 while(result.length<size){let added=false;for(const topic of topics){
  if(quotas&&(counts.get(topic)||0)>=(quotas.get(topic)||0))continue;
  const group=groups.get(topic),limit=Object.hasOwn(policy.variantLimits,topic)?policy.variantLimits[topic]:policy.defaultVariantLimit;
  const index=group.findIndex(q=>!families.has(questionFamily(q))&&(questionOrigin(q)!=='derived'||(derivedCounts.get(topic)||0)<limit));
  if(index!==-1){const [q]=group.splice(index,1);families.add(questionFamily(q));if(questionOrigin(q)==='derived')derivedCounts.set(topic,(derivedCounts.get(topic)||0)+1);counts.set(topic,(counts.get(topic)||0)+1);result.push(q);added=true;if(result.length===size)break;}
 }if(!added)throw new Error(`設定した配分で診断の${size}問を用意できません。通常学習は利用できます。`);}
 return shuffle(result,random);
}
export function createDiagnostic(questions,qualification,attempts=[],catalogRevision=''){
 const size=diagnosticSize(qualification)||DEFAULT_DIAGNOSTIC_SIZE;
 if(questions.length!==size||new Set(questions.map(q=>q.id)).size!==size||new Set(questions.map(questionFamily)).size!==size)throw new Error(`診断は内容が異なる${size}問で開始してください。`);
 return createAssessment(questions,qualification,attempts,catalogRevision);
}
export function validateDiagnostic(run,qualification,validateAttempt){
 if(!run||run.mode!==undefined||run.size<MIN_DIAGNOSTIC_SIZE)throw new Error('この診断の形式を確認できません。');
 return validateAssessment(run,qualification,validateAttempt,{size:run.size,diagnostic:true});
}
