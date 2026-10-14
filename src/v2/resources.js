import {toRecord,fromRecord} from './records.js';
const assessment=kind=>['diagnostic','mock'].includes(kind);
export function encodeResource(kind,p){
 if(!assessment(kind))return structuredClone(p);
 const {slots,currentChoiceId,responses,...rest}=p;
 return {...rest,format:'hitomon-assessment',version:2,currentResponse:{choiceIds:currentChoiceId===null?[]:Array.isArray(currentChoiceId)?[...currentChoiceId]:[currentChoiceId]},responses:Object.fromEntries(Object.entries(responses).map(([key,value])=>[key,value===null?null:{choiceIds:Array.isArray(value)?[...value]:[value]}])),slots:slots.map(({attempt,...slot})=>({...slot,record:toRecord(attempt)}))};
}
export function decodeResource(kind,p){
 if(!assessment(kind))return structuredClone(p);
 if(p?.format!=='hitomon-assessment'||p.version!==2||!Array.isArray(p.slots)||!Array.isArray(p.currentResponse?.choiceIds)||p.currentResponse.choiceIds.length>20||!p.responses||Array.isArray(p.responses))throw Error('新形式の受験記録ではありません。');
 const {format,slots,currentResponse,responses,...rest}=p,decoded=slots.map(({record,...slot})=>({...slot,attempt:fromRecord(record)})),byId=new Map(decoded.map(s=>[s.id,s]));
 const response=(value,slot)=>{if(value===null)return null;if(!slot||!Array.isArray(value.choiceIds)||Object.keys(value).some(k=>k!=='choiceIds'))throw Error('受験回答の形式を確認できません。');if(slot.attempt.questionSnapshot.type==='multipleChoice')return [...value.choiceIds];if(value.choiceIds.length!==1)throw Error('単一選択の回答を確認できません。');return value.choiceIds[0];};
 const selected=currentResponse.choiceIds;
 return {...rest,currentChoiceId:selected.length?decoded[rest.currentIndex]?.attempt.questionSnapshot.type==='multipleChoice'?[...selected]:selected.length===1?selected[0]:null:null,responses:Object.fromEntries(Object.entries(responses).map(([key,value])=>[key,response(value,byId.get(key))])),slots:decoded};
}
export function encodeResourceRow(row){if(!row?.kind||!row.payload)return row;return {...row,payload:encodeResource(row.kind,row.payload),...(row.conflict?{conflict:{...row.conflict,payload:encodeResource(row.kind,row.conflict.payload)}}:{})};}
export function decodeResourceRow(row){if(Array.isArray(row))return row.map(decodeResourceRow);if(!row?.kind||!row.payload)return row;return {...row,payload:decodeResource(row.kind,row.payload),...(row.conflict?{conflict:{...row.conflict,payload:decodeResource(row.kind,row.conflict.payload)}}:{})};}
export function encodeWorkspaceBackup(value){if(!value)return value;return {...value,runs:value.runs.map(r=>encodeResource(r.mode==='mock'?'mock':'diagnostic',r))};}
export function decodeWorkspaceBackup(value){if(!value)return value;if(value.version!==2)throw Error('旧形式の計画・受験記録は変換ツールで変換してください。');return {...value,runs:value.runs.map(r=>decodeResource(r.mode==='mock'?'mock':'diagnostic',r))};}
