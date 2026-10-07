export const paperModes=['all','paperless','desk'];
export function allowsQuestion(q,mode='all',classification=null,deskIds=[]){
 if(mode==='all')return true;
 if(mode==='desk')return deskIds.includes(q.id)||classification?.items.some(item=>item.questionId===q.id&&item.mode==='desk')===true;
 return mode==='paperless'&&!deskIds.includes(q.id)&&classification?.items.some(item=>item.questionId===q.id&&item.mode==='paperless')===true;
}
export function contextLabel(q,classification,deskIds=[]){
 if(deskIds.includes(q.id))return '自分で「机で解く」に指定';
 const item=classification?.items.find(item=>item.questionId===q.id);
 return item?item.mode==='paperless'?'紙・ペンなしの候補':'書いて考える問題':'取り組み方は未分類';
}

// The entrance is a local preference, independent of a question's classification.
export function attemptEntryMode(attempt,session){return paperModes.includes(attempt.entryMode)?attempt.entryMode:session?.attemptIds.includes(attempt.id)&&paperModes.includes(session.paperMode)?session.paperMode:'all';}
