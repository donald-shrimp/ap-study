// Synthetic contract fixtures, never actual FP exam material.
export const sourceRecord={publisher:'合成テスト',publishedAt:'2026-05-01',legalAsOf:'2026-04-01',questionUrl:'https://example.com/question.pdf',questionSha256:'a'.repeat(64),answerUrl:'https://example.com/answer.pdf',answerSha256:'b'.repeat(64),modifiedFromOriginal:false,modificationNote:''};
export const legalReview={status:'unverified',checkedAt:null,sourceRefs:[],note:''};
export function numericField(id='amount',answer='1490000',unit='円',decimalPlaces=0){return {id,label:id,type:'numeric',maxLength:100,numeric:{unit,decimalPlaces,rounding:'none'},grading:{method:'exactDecimal'},referenceAnswers:[answer],explanation:'合成データの照合確認。',rubric:['登録値と単位を確認する。']};}
export function fixtureCase(part='jafp-practical',id='synthetic-case'){
 return {id,qualificationId:'fp2',examPartId:part,topicId:'financial-assets',version:1,status:'reviewed',title:'合成形式テスト',source:'実問題ではない',body:'合成の共通本文。',sourceImages:[],bodyFigures:[],sourceRecord:structuredClone(sourceRecord),legalReview:structuredClone(legalReview),items:[{id:'q1',label:'問1',prompt:'形式を確認する。',fields:[numericField()]}]};
}
