import {DIAGNOSTIC_SIZE} from './diagnostic.js';
import {examPartsFor} from './planning.js';

// A blueprint opts a qualification into the currently supported 30-question
// diagnostic. A small initial question pack must still be usable for practice.
export function canStartDiagnostic(qualification,questions) {
 if(qualification.diagnosticBlueprint?.size!==DIAGNOSTIC_SIZE)return false;
 const parts=new Set(examPartsFor(qualification).filter(p=>p.practiceAvailable).map(p=>p.id));
 return new Set(questions.filter(q=>!q.diagnosticOnly&&(!q.qualificationId||q.qualificationId===qualification.id)&&parts.has(q.examPartId||qualification.defaultExamPartId||'objective')).map(q=>q.id)).size>=DIAGNOSTIC_SIZE;
}
