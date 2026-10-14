/** Offline one-time conversion. The application never imports this legacy reader. */
import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash,webcrypto} from 'node:crypto';
import {encodeState,decodeState,validateRecord} from '../src/v2/records.js';
import {encodeWorkspaceBackup} from '../src/v2/resources.js';
import {validatePlan,goalUnit} from '../src/domain/planning.js';
import {createStateValidator} from '../src/storage/validate.js';
import {validatePlanRevision} from '../src/domain/plan-history.js';
if(!globalThis.crypto)globalThis.crypto=webcrypto;
const clone=v=>structuredClone(v),hash=v=>createHash('sha256').update(v).digest('hex');
export function convertPlan(old,q){
 if(old?.format!=='hitomon-study-plan'||old.version!==1||old.qualificationId!==q.id)throw Error('変換対象の旧計画を確認できません。');
 const p=clone(old);p.version=2;
 for(const phase of p.phases){
  // Legacy AP has no completed B cases. An old pooled count must never become B cases.
  const parts=phase.examPartIds.filter(id=>goalUnit(q,id)==='questionAttempts');if(parts.length!==1)throw Error('旧計画の合算目標を科目へ自動分配できません。対象科目を確認してください。');
  const target=n=>[{examPartId:parts[0],unit:'questionAttempts',target:n}];phase.goals=target(phase.targets.completedAttempts);delete phase.targets;
  for(const w of phase.weeklyTargets||[]){w.goals=target(w.completedAttempts);delete w.completedAttempts;}
 }
 return validatePlan(p,q);
}
export function convertBackup(old,q,{questions=[]}={}){
 if(old?.version!==1)throw Error('旧version 1のバックアップを指定してください。変換済みを重ねて変換しません。');
 if(old.format==='hitomon-card-record'){if(old.qualificationId!==q.id||!Array.isArray(old.events))throw Error('単語帳の資格を確認してください。');return {...clone(old),version:2};}
 if(!Array.isArray(old.attempts))throw Error('学習記録のバックアップを指定してください。');
 const s=clone(old);s.version=2;
 for(const a of s.attempts){if(a.qualificationId!==q.id||!a.questionSnapshot||!a.materialSnapshot)throw Error('旧記録の資格・固定教材が不足しています。現在教材で補完せず確認を止めます。');a.questionSnapshot.examPartId??=q.defaultExamPartId;}
 const changeRun=r=>{if(r.version!==1||r.qualificationId!==q.id)throw Error('受験記録の資格・版を確認してください。');r.version=2;return r;};
 if(s.workspaceBackup){const w=s.workspaceBackup;if(w.format!=='hitomon-workspace-backup'||w.version!==1||w.qualificationId!==q.id)throw Error('計画バックアップの資格を確認してください。');w.version=2;if(w.plan)w.plan=convertPlan(w.plan,q);w.runs=w.runs.map(changeRun);for(const r of w.planRevisions||[]){if(r.version!==1)throw Error('計画履歴の版を確認してください。');r.version=2;r.plan=convertPlan(r.plan,q);validatePlanRevision(r,q);}}
 if(s.learningBackup){if(s.learningBackup.version!==1||s.learningBackup.qualificationId!==q.id)throw Error('学習設定の資格を確認してください。');s.learningBackup.version=2;}
 const byId=new Map([...questions,...s.attempts.map(a=>a.questionSnapshot)].map(v=>[v.id,v]));
 const validate=createStateValidator({getQuestions:()=>[...byId.values()],getTopics:()=>q.topics.map(t=>t.name),getQualification:()=>q});validate(s);
 const converted=encodeState(s);const roundtrip=decodeState(converted);validate(roundtrip);
 if(roundtrip.attempts.length!==old.attempts.length)throw Error('変換後の件数が一致しません。');
 for(const [i,a] of old.attempts.entries()){const next=roundtrip.attempts[i];for(const k of ['id','questionId','questionVersion','contentRevision','status','startedAt','updatedAt','completedAt','hintCount','hintsBeforeAnswer','answerViewedBefore','hintEvents','materialSnapshot','selectedChoiceId','selectedChoiceIds','confidence'])if(JSON.stringify(next[k])!==JSON.stringify(a[k]))throw Error(`変換照合が一致しません：${a.id} ${k}`);validateRecord(converted.records[i]);}
 return converted;
}
async function main(){
 const [input,output,qualificationId]=process.argv.slice(2);if(!input||!output||!qualificationId)throw Error('使い方: node tools/convert-study-backup.mjs 入力.json 出力-v2.json ap|ab730');if(resolve(input)===resolve(output))throw Error('原本と出力は別ファイルにしてください。');
 const root=new URL('../',import.meta.url),q=JSON.parse(await readFile(new URL(`data/qualifications/${qualificationId}/manifest.json`,root),'utf8'));
 const questions=(await Promise.all(q.packs.map(p=>readFile(new URL(`data/qualifications/${q.id}/${p.url}`,root),'utf8').then(JSON.parse)))).flat();
 const raw=await readFile(input,'utf8'),old=JSON.parse(raw),converted=convertBackup(old,q,{questions}),text=JSON.stringify(converted,null,2)+'\n';
 const report={format:'hitomon-conversion-report',version:2,qualificationId:q.id,convertedAt:new Date().toISOString(),inputSHA256:hash(raw),outputSHA256:hash(text),records:converted.records?.length||0,cardEvents:converted.events?.length||0,assessmentRuns:converted.workspaceBackup?.runs.length||0,planRevisions:converted.workspaceBackup?.planRevisions?.length||0,verification:'記録件数・ID・教材版・正誤・日時・全ヒント履歴・選択肢ID・自信・個別教材を照合。旧計画は科目Aの取り組み問数へ変換。科目Bの実績を作らない。本人DBへの取り込みは未実施。'};
 // Never overwrite an existing personal output/report; no files enter Git.
 await writeFile(output,text,{flag:'wx'});await writeFile(output+'.conversion-report.json',JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(`変換完了: 学習${report.records}件、受験${report.assessmentRuns}回、計画履歴${report.planRevisions}件、単語帳${report.cardEvents}件。原本は保持しました。`);
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href)main().catch(e=>{console.error(e.message);process.exitCode=1;});
