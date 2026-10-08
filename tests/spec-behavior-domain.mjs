import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createAttempt,selectAnswer,finalizeAttempt} from '../src/domain/study.js';
import {blankPlan,summarize,phaseProgress} from '../src/domain/planning.js';
import {learningFields} from '../src/domain/analytics.js';
const qualification=JSON.parse(readFileSync(new URL('../content/ap/qualification.json',import.meta.url)));
const questions=JSON.parse(readFileSync(new URL('../data/questions.json',import.meta.url)));
test('時計を戻した後の未来記録は保持し、グラフ・AI・期間・週の実績へまだ数えない',()=>{
 const a=createAttempt(questions[0],{at:'2026-10-08T09:00:00.000Z'});selectAnswer(a,a.questionSnapshot.answer);finalizeAttempt(a,'correct','2026-10-08T10:00:00.000Z');
 const plan=blankPlan(qualification);plan.phases=[{id:'one',name:'検証',start:'2026-10-08',end:'2026-10-09',examPartIds:['objective'],targets:{completedAttempts:10},focusTopicIds:[],weeklyTargets:[{id:'week',start:'2026-10-08',end:'2026-10-09',completedAttempts:10}]}];
 const before=JSON.stringify(a);
 for(const at of ['2026-10-08T08:00:00.000Z','2026-10-08T10:00:00.000Z']){
  const expected=at<a.completedAt?0:1;
  assert.equal(learningFields({qualification,questions,attempts:[a],plan,at}).rows.reduce((sum,r)=>sum+r.total,0),expected);
  assert.equal(summarize([a],qualification,plan.timeZone,at).todayCounts.completedAttempts,expected);
  assert.equal(phaseProgress(plan,[a],qualification,at)[0].actual,expected);
  assert.equal(phaseProgress(plan,[a],qualification,at)[0].weeklyProgress[0].actual,expected);
 }
 assert.equal(JSON.stringify(a),before);
});
