// Decimal values are compared as strings: no rounding or unit conversion.
export function decimalValue(input){
 if(typeof input!=='string'||input.length>100)return null;
 const text=input.replace(/[０-９＋－．，]/g,c=>String.fromCharCode(c.charCodeAt(0)-0xfee0)).trim();
 if(!/^[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/.test(text))return null;
 const plain=text.replaceAll(',',''),negative=plain.startsWith('-');
 let [whole,fraction='']=plain.replace(/^[+-]/,'').split('.');
 whole=whole.replace(/^0+(?=\d)/,'');fraction=fraction.replace(/0+$/,'');
 return (negative&&(whole!=='0'||fraction)?'-':'')+whole+(fraction?'.'+fraction:'');
}
export const ROUNDING=Object.freeze({none:'丸めなし',halfUp:'四捨五入',floor:'切り下げ',ceil:'切り上げ',truncate:'切り捨て（0方向）'});
export function validNumericField(field){
 const n=field.numeric;
 return field.type==='numeric'&&field.grading?.method==='exactDecimal'&&Object.keys(field.grading).length===1&&
  !!n&&Object.keys(n).every(k=>['unit','decimalPlaces','rounding'].includes(k))&&
  typeof n.unit==='string'&&n.unit.length>0&&n.unit.length<=30&&
  Number.isInteger(n.decimalPlaces)&&n.decimalPlaces>=0&&n.decimalPlaces<=12&&Object.hasOwn(ROUNDING,n.rounding)&&
  Number.isInteger(field.maxLength)&&field.maxLength>=1&&field.maxLength<=100&&
  Array.isArray(field.referenceAnswers)&&field.referenceAnswers.length>0&&field.referenceAnswers.every(v=>
   typeof v==='string'&&v.length<=field.maxLength&&/^-?(?:0|[1-9]\d*)(?:\.\d+)?$/.test(v)&&decimalValue(v)!==null&&(v.split('.')[1]?.length||0)<=n.decimalPlaces);
}
export function numericInstruction(field){
 const n=field.numeric,precision=n.decimalPlaces===0?'整数':`小数第${n.decimalPlaces}位まで`;return n.rounding==='none'?precision:`${precision} · ${ROUNDING[n.rounding]}`;
}
