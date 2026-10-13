// Guest data remains separate until explicitly adopted. Existing account
// records, including card tombstones, do not become import candidates again.
export function hasGuestImport({guest,current,prefix,guestCards=[],cardRows=[],guestLearning=[],learningRows=[],guestWorkspace=[],workspaceRows=[],personalRows=[]}){
 const imported=new Set(current.attempts.map(a=>a.importedFrom));
 if(guest.attempts.some(a=>!imported.has(prefix+a.id)))return true;
 const cardIds=new Set(cardRows.filter(r=>r.kind==='rating').map(r=>r.payload.id));
 if(guestCards.some(e=>!cardIds.has(e.id)))return true;
 const noteIds=new Set(personalRows.filter(r=>r.kind==='note').map(r=>r.payload.topicId));
 if(Object.entries(guest.readingNotes).some(([id,text])=>text&&!noteIds.has(id)&&!current.readingNotes[id]))return true;
 const learningIds=new Set(learningRows.map(r=>r.id));
 if(guestLearning.some(r=>r.kind!=='context'&&!learningIds.has(r.id)&&r.payload.value))return true;
 if(guest.settings.deskQuestionIds.some(id=>!learningIds.has('desk--'+id)))return true;
 if(guest.attempts.some(a=>a.deferred&&!learningIds.has('deferred--'+a.questionId)))return true;
 const workspaceIds=new Set(workspaceRows.map(r=>r.id));
 return guestWorkspace.some(r=>!workspaceIds.has(r.id));
}
