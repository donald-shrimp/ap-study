export function contentError(detail,subject='教材',cause){
 const error=new Error(`${subject}を読み込めません。接続後にもう一度お試しください。`,cause?{cause}:undefined);
 error.name='ContentLoadError';error.detail=detail;
 console.warn('Content load failed',detail,cause?.message||'');
 return error;
}
