// Images needed to solve a question. Supplemental original scans are online references.
export function requiredQuestionAssets(q){
 return [...new Set([...(q.stem?[]:q.sourceImages||[]),q.image,...(q.choicePresentation==='codes'?[]:(q.choices||[]).map(c=>c.image))].filter(Boolean))];
}
export const requiredCaseAssets=c=>[...new Set((c.bodyFigures||[]).map(f=>f.image))];
