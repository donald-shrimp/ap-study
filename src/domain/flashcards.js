const id=v=>typeof v==='string'&&/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$/.test(v);
export function validateDeck(deck,qualification,questions){
 const byId=new Map(questions.map(q=>[q.id,q]));
 if(!deck||deck.format!=='hitomon-flashcards'||deck.version!==1||deck.qualificationId!==qualification.id||!Array.isArray(deck.cards)||deck.cards.length>10000)throw new Error('単語帳の形式が正しくありません。');
 const seen=new Set();for(const c of deck.cards){
  if(!c||typeof c!=='object'||!id(c.id)||seen.has(c.id)||!Number.isInteger(c.version)||c.version<1||!qualification.topics.some(t=>t.id===c.topicId)||!['front','back','sourceNote'].every(k=>typeof c[k]==='string'&&c[k].length>0&&c[k].length<=(k==='back'?1000:k==='front'?200:500))||!Array.isArray(c.relatedQuestionIds)||!c.relatedQuestionIds.length||c.relatedQuestionIds.length>10||new Set(c.relatedQuestionIds).size!==c.relatedQuestionIds.length||c.relatedQuestionIds.some(ref=>!byId.has(ref)||byId.get(ref).topicId!==c.topicId))throw new Error('単語帳の内容を確認できません。');
  seen.add(c.id);
 }return deck;
}
export function validateCardEvents(events){
 if(!Array.isArray(events)||events.length>20000)throw new Error('単語帳の記録は2万件以内で指定してください。');
 const ids=new Set();for(const e of events){if(!e||Object.keys(e).some(k=>!['id','cardId','cardVersion','outcome','at'].includes(k))||!id(e.id)||ids.has(e.id)||!id(e.cardId)||!Number.isInteger(e.cardVersion)||e.cardVersion<1||!['recalled','again'].includes(e.outcome)||typeof e.at!=='string'||Number.isNaN(new Date(e.at).valueOf())||new Date(e.at).toISOString()!==e.at)throw new Error('単語帳の記録の形式が正しくありません。');ids.add(e.id);}return events;
}
export function cardProgress(cards,events){
 const latest=new Map();for(const e of events){const old=latest.get(e.cardId);if(!old||e.at>old.at||e.at===old.at&&e.id>old.id)latest.set(e.cardId,e);}
 const current=cards.map(c=>latest.get(c.id)).filter((e,i)=>e&&e.cardVersion===cards[i].version);
 return {latest,seen:current.length,again:current.filter(e=>e.outcome==='again').length};
}
export function nextCard(cards,events,checkpoint={seen:[]}){
 const eligible=cards.filter(c=>!checkpoint.topicId||c.topicId===checkpoint.topicId);if(!eligible.length)return null;
 const progress=cardProgress(eligible,events),ids=new Set(eligible.map(c=>c.id));
 const recent=(checkpoint.recent||events.slice().sort((a,b)=>a.at.localeCompare(b.at)||a.id.localeCompare(b.id)).slice(-10).map(e=>e.cardId)).filter(id=>ids.has(id)).slice(-10);
 let seen=(checkpoint.seen||[]).filter(id=>ids.has(id));if(seen.length===eligible.length)seen=[];
 const cooling=new Set(recent.slice(-3));if(checkpoint.cardId)cooling.add(checkpoint.cardId);
 let pool=eligible.filter(c=>!cooling.has(c.id));
 // Small decks shorten the gap, but still avoid the immediate previous card.
 if(!pool.length)pool=eligible.filter(c=>c.id!==checkpoint.cardId);if(!pool.length)pool=eligible;
 const category=c=>{const e=progress.latest.get(c.id);return !e||e.cardVersion!==c.version?1:e.outcome==='again'?0:2;};
 pool.sort((a,b)=>category(a)-category(b)||Number(seen.includes(a.id))-Number(seen.includes(b.id))||String(progress.latest.get(a.id)?.at||'').localeCompare(String(progress.latest.get(b.id)?.at||''))||a.id.localeCompare(b.id));
 return {cardId:pool[0].id,cardVersion:pool[0].version,flipped:false,seen,recent,topicId:checkpoint.topicId||null};
}
