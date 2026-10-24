import {diagnosticSize,validDiagnosticBlueprint} from './assessment-policy.js';
import {canUseQuestion,questionFamily} from './content-policy.js';
import {selectDiagnostic} from './diagnostic.js';
import {examPartsFor} from './planning.js';

// A blueprint opts a qualification into the configured question count
// diagnostic. A small initial question pack must still be usable for practice.
export function canStartDiagnostic(qualification,questions,studyAllowed=()=>true) {
 if(!validDiagnosticBlueprint(qualification))return false;
 const parts=new Set(examPartsFor(qualification).filter(p=>p.practiceAvailable).map(p=>p.id));
 const normal=questions.filter(q=>canUseQuestion(q,'practice')),extra=qualification.assessment?.index||[],pool=[...normal,...extra];
 if(new Set(pool.filter(q=>studyAllowed(q)&&canUseQuestion(q,'diagnostic')&&(!q.qualificationId||q.qualificationId===qualification.id)&&parts.has(q.examPartId||qualification.defaultExamPartId||'objective')).map(questionFamily)).size<diagnosticSize(qualification))return false;
 try{selectDiagnostic(normal,qualification,[],()=>.5,extra,studyAllowed);return true;}catch{return false;}
}
