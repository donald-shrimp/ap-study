const date=v=>typeof v==='string'&&/^\d{4}-\d\d-\d\d$/.test(v)&&Number.isFinite(Date.parse(v+'T00:00:00Z'))&&new Date(v+'T00:00:00Z').toISOString().slice(0,10)===v;
const url=v=>typeof v==='string'&&v.length<=2000&&/^https?:\/\/[^\s]+$/.test(v);
const hash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
export function validateLegalContext(material,{required=false}={}){
 const s=material.sourceRecord,r=material.legalReview,fail=()=>{throw Error('法令基準日・出典の形式を確認できません。');};
 if(s===undefined&&r===undefined){if(required)fail();return material;}
 if(!s||!r||Object.keys(s).some(k=>!['publisher','publishedAt','legalAsOf','questionUrl','questionSha256','answerUrl','answerSha256','modifiedFromOriginal','modificationNote'].includes(k))||
  typeof s.publisher!=='string'||!s.publisher.trim()||s.publisher.length>200||!(s.publishedAt===null||date(s.publishedAt))||!(s.legalAsOf===null||date(s.legalAsOf))||
  !url(s.questionUrl)||!url(s.answerUrl)||!hash(s.questionSha256)||!hash(s.answerSha256)||typeof s.modifiedFromOriginal!=='boolean'||typeof s.modificationNote!=='string'||s.modificationNote.length>2000||s.modifiedFromOriginal&&!s.modificationNote.trim())fail();
 if(Object.keys(r).some(k=>!['status','checkedAt','sourceRefs','note'].includes(k))||!['unverified','current','outdated'].includes(r.status)||!Array.isArray(r.sourceRefs)||r.sourceRefs.length>20||!r.sourceRefs.every(url)||new Set(r.sourceRefs).size!==r.sourceRefs.length||typeof r.note!=='string'||r.note.length>4000)fail();
 if(r.status==='unverified'){if(r.checkedAt!==null)fail();}
 else if(!date(r.checkedAt)||!r.sourceRefs.length||!r.note.trim()||(r.status==='current'&&s.legalAsOf===null))fail();
 return material;
}
export function legalContextLines(material){
 if(!material.sourceRecord)return [];
 const s=material.sourceRecord,r=material.legalReview;
 return [...(s.legalAsOf?[`法令基準日：${s.legalAsOf}`]:[]),...(r.status==='outdated'?['法令改正あり（学習非推奨）']:[])];
}
// Existing review metadata is the source of truth: an unchecked item is not
// evidence of a law change. Keep review dates internal and preserve snapshots.
export const hasLawChange=material=>material?.legalReview?.status==='outdated';
export const legalStudyAllowed=(material,{excludeOutdated=true}={})=>!excludeOutdated||!hasLawChange(material);
export function legalAIPrompt(material){
 if(!material.sourceRecord)return '';
 const s=material.sourceRecord,r=material.legalReview;
 return ['【出典・法令基準】',`公表元：${s.publisher} · 公表日：${s.publishedAt||'不明'}`,...legalContextLines(material),...(!s.legalAsOf?['法令基準日：不明']:[]),`最終法令チェック：${r.checkedAt||'未実施'} · 法令改正フラグ：${hasLawChange(material)?'あり':r.status==='current'?'なし':'未判定'}`,`原本：${s.questionUrl}\n原本SHA256：${s.questionSha256}`,`公式解答：${s.answerUrl}\n解答SHA256：${s.answerSha256}`,`加工：${s.modifiedFromOriginal?s.modificationNote:'なし'}`,r.note,...r.sourceRefs,'出題当時の公式正答と現行法令を区別し、未確認の現行法令を断定しないでください。'].filter(Boolean).join('\n');
}
