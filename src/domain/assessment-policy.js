import {contentId} from './content-policy.js';
export const MAX_ASSESSMENT_SIZE=200;
export const MIN_DIAGNOSTIC_SIZE=30;
export const DEFAULT_DIAGNOSTIC_SIZE=30;
export const ASSESSMENT_PREFERENCE=Object.freeze(['unseen-assessment','unseen-practice','seen-assessment','seen-practice']);
export const validAssessmentSize=size=>Number.isInteger(size)&&size>=1&&size<=MAX_ASSESSMENT_SIZE;
export const diagnosticSize=qualification=>qualification.diagnosticBlueprint?.size;
export function diagnosticPolicy(qualification){
 const b=qualification.diagnosticBlueprint||{};
 return {sampling:b.sampling||'topic-round-robin',defaultVariantLimit:b.defaultVariantLimit??1,variantLimits:structuredClone(b.variantLimits||{}),weights:structuredClone(b.weights||{}),preference:[...ASSESSMENT_PREFERENCE]};
}
export function validSelectionPolicy(p,size){
 const record=v=>v&&typeof v==='object'&&!Array.isArray(v);
 if(!record(p)||Object.keys(p).some(k=>!['sampling','defaultVariantLimit','variantLimits','weights','preference'].includes(k))||!['topic-round-robin','topic-weighted'].includes(p.sampling)||!Number.isInteger(p.defaultVariantLimit)||p.defaultVariantLimit<0||p.defaultVariantLimit>size||!record(p.variantLimits)||Object.keys(p.variantLimits).length>100||Object.entries(p.variantLimits).some(([id,n])=>!contentId(id)||!Number.isInteger(n)||n<0||n>size)||!Array.isArray(p.preference))return false;
 const legacy=['unseen-derived','unseen-original','seen-derived','seen-original'];
 if(![ASSESSMENT_PREFERENCE,legacy].some(expected=>JSON.stringify(p.preference)===JSON.stringify(expected)))return false;
 const weights=p.weights||{};
 return record(weights)&&Object.keys(weights).length<=100&&Object.entries(weights).every(([id,n])=>contentId(id)&&Number.isInteger(n)&&n>0&&n<=100000)&&(p.sampling==='topic-weighted'?Object.keys(weights).length>0:Object.keys(weights).length===0);
}
export function validDiagnosticBlueprint(qualification){
 const size=diagnosticSize(qualification),topics=qualification.topics?.map(t=>t.id)||[];
 if(!validAssessmentSize(size)||size<MIN_DIAGNOSTIC_SIZE)return false;
 const p=diagnosticPolicy(qualification);
 return validSelectionPolicy(p,size)&&[...Object.keys(p.variantLimits),...Object.keys(p.weights)].every(id=>topics.includes(id));
}
