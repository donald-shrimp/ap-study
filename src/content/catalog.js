import {contentError} from './errors.js';
import {canUseQuestion,validQuestionPolicy,questionOrigin} from '../domain/content-policy.js';
import {studyTargets,resolveStudyTarget} from '../domain/study-target.js';
export const appRoot = new URL('../../', import.meta.url);
export const contentCacheName = `hitomon-${appRoot.pathname}content`;

async function readJSON(url, sha256, {refresh=false}={}) {
  const key = new URL(url); key.search = '';
  let cache;
  try{cache=await globalThis.caches?.open(contentCacheName);}catch{}
  const decode=async response=>{
    if (!response.ok) throw contentError('教材を読み込めませんでした。','教材');
    const text=await response.text();
    if(sha256){
      const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(n=>n.toString(16).padStart(2,'0')).join('');
      if(hash!==sha256)throw contentError('教材の確認に失敗しました。オンラインで開き直してください。','教材');
    }
    let value;try{value=JSON.parse(text);}catch(error){throw contentError('Invalid content JSON: '+key.pathname,'教材',error);}
    return {value,text};
  };
  let reload=refresh;
  // A bank is reusable only if it matches the currently selected manifest's
  // full SHA. This also works before the first SW has taken control.
  if(sha256&&cache&&!refresh){
    try{
      const saved=await cache.match(key.href);
      if(saved){
        try{const {value}=await decode(saved);return {value,online:navigator.onLine};}
        catch{reload=true;await cache.delete(key.href);}
      }
    }catch{}
  }
  let response,cachedFallback=false;
  try { response = await fetch(url, {cache: reload?'reload':'no-cache'}); }
  catch (error) {
    try{response=await cache?.match(key.href);}catch{}
    cachedFallback=true;
    if (!response) throw contentError('Network and cache unavailable: '+key.pathname,'教材',error);
  }
  const {value,text}=await decode(response);
  // The first visit may load before the SW controls the page. Save public content
  // here too so a first question can be resumed offline without an extra reload.
  try {
    // A SW may already be refreshing this mutable manifest in the background.
    // Writing its old response back would race with and undo the refresh.
    if(response.headers.get('X-Hitomon-Cache')!=='1')
      await cache?.put(key.href, new Response(text, {headers:{'Content-Type':'application/json'}}));
  } catch { /* Cache quota does not turn a successful read into a failure. */ }
  return {value, online: !cachedFallback && navigator.onLine && response.headers.get('X-Hitomon-Offline') !== '1'};
}

function assets(q) {
  const resolve = path => {
    if (!path) return path;
    const url = new URL(path, appRoot);
    if (!['http:', 'https:'].includes(url.protocol)) throw contentError('教材の画像URLが正しくありません。','教材');
    return url.href;
  };
  return {...q, sourceImages:q.sourceImages.map(resolve), image:resolve(q.image), choices:q.choices.map(c=>({...c,image:resolve(c.image)}))};
}

export async function loadCatalog(requestedId,{preferredId=null,choose=false,requestedPartId=null}={}) {
  const listingURL=new URL('data/qualifications/catalog.json', appRoot);
  // Older public caches may contain the qualification-only index. Only in that
  // case fetch lightweight manifests; the chooser never loads question packs.
  async function qualificationsFrom(listing){
   const qualifications=listing.value.qualifications;
   if (!Array.isArray(qualifications) || !qualifications.length) throw contentError('資格一覧を読み込めませんでした。','資格一覧');
   return Promise.all(qualifications.map(async q=>{
    if(Array.isArray(q.studyTargets))return q;
    try{
      const {value}=await readJSON(new URL(q.url,new URL('data/qualifications/',appRoot)));
      return {...q,defaultExamPartId:value.defaultExamPartId,studyTargets:studyTargets(value)};
    }catch(error){if(navigator.onLine)throw error;return {...q,studyTargets:[]};}
   }));
  }
  let qualifications=await qualificationsFrom(await readJSON(listingURL));
  const wanted=requestedId||preferredId,listed=qualifications.find(q=>q.id===wanted);
  // A stale SW listing may predate a published qualification or subject. Retry
  // once through networkFirst before treating an explicit destination as absent.
  if(wanted&&(!listed||requestedPartId!==null&&!studyTargets(listed).some(p=>p.examPartId===requestedPartId)))
    qualifications=await qualificationsFrom(await readJSON(listingURL,undefined,{refresh:true}));
  if(choose)return {choose:true,qualifications};
  if(!requestedId&&qualifications.some(q=>q.id===preferredId))requestedId=preferredId;
  if (!requestedId && qualifications.length > 1) return {choose:true, qualifications};
  const entry = qualifications.find(q=>q.id === (requestedId || qualifications[0].id));
  if (!entry) throw new Error('この資格はまだ公開されていません。');
  const manifestURL = new URL(entry.url, new URL('data/qualifications/', appRoot));
  let loaded = await readJSON(manifestURL);
  let manifest = loaded.value;
  // The listing and each manifest refresh independently; either may be one
  // publication behind. A cached manifest must not reject a newly added part.
  if(manifest.id===entry.id&&resolveStudyTarget(manifest,{requestedPartId})===null){
    loaded=await readJSON(manifestURL,undefined,{refresh:true});manifest=loaded.value;
  }
  // Old mutable manifests can have the case bank but no session catalog.
  // Refresh once through the SW; offline fallback still keeps saved cases usable.
  if(manifest.id===entry.id&&manifest.cases?.count>0&&!Array.isArray(manifest.cases.index)){
    loaded=await readJSON(manifestURL,undefined,{refresh:true});manifest=loaded.value;
  }
  if (manifest.id !== entry.id) throw contentError('資格の教材が一致しません。','教材');
  if(resolveStudyTarget(manifest,{requestedPartId})===null)return {choose:true,qualifications,invalidTarget:true};
  const indexURL = new URL(manifest.index.url, manifestURL);
  const index = await readJSON(indexURL, manifest.index.sha256);
  const questions = index.value.map(assets), byId = new Map(questions.map(q=>[q.id,q]));
  if (questions.length !== manifest.count || byId.size !== questions.length) throw contentError('教材一覧の件数が一致しません。','教材');
  const packs = new Map(manifest.packs.map(pack=>[pack.id,{...pack,url:new URL(pack.url,manifestURL).href}]));
  const loading = new Map();
  let diagnosticsPromise;
  const learningPromises=new Map();
  function loadLearningTool(key){
    const entry=manifest[key];if(!entry)return Promise.resolve(null);
    if(!learningPromises.has(key))learningPromises.set(key,readJSON(new URL(entry.url,manifestURL),entry.sha256).then(({value})=>{
      const records=value[key==='studyContext'?'items':'cards'];
      if(value.qualificationId!==manifest.id||value.version!==1||!Array.isArray(records)||records.length!==entry.count)throw contentError('移動中の学習教材を確認できません。通常学習は利用できます。','教材');
      if(key==='studyContext'&&(value.format!=='hitomon-study-context'||new Set(records.map(r=>r.questionId)).size!==records.length||records.some(r=>!byId.has(r.questionId)||!['paperless','desk'].includes(r.mode)||typeof r.reason!=='string')))throw contentError('問題の分類を確認できません。','紙ペンの分類');
      return value;
    }).catch(error=>{learningPromises.delete(key);throw error;}));
    return learningPromises.get(key);
  }
  function loadAssessments(){
    const entry=manifest.assessment;
    if(!entry)return Promise.resolve([]);
    if(!diagnosticsPromise)diagnosticsPromise=readJSON(new URL(entry.url,manifestURL),entry.sha256).then(({value})=>{
      if(!Array.isArray(value))throw contentError('受験専用教材の形式を確認できません。','受験の教材');
      const all=new Map([...questions,...value].map(q=>[q.id,q]));
      if(!Array.isArray(value)||value.length!==entry.count||entry.reviewed!==entry.count||new Set(value.map(q=>q.id)).size!==value.length||value.some(q=>canUseQuestion(q,'practice')||!validQuestionPolicy(q)||byId.has(q.id)||questionOrigin(q)==='derived'&&!all.has(q.parentQuestionId)||q.qualificationId!==manifest.id||q.enrichment!=='reviewed'))throw contentError('受験専用教材の確認に失敗しました。通常学習は利用できます。','受験の教材');
      return value.map(assets);
    }).catch(error=>{diagnosticsPromise=null;throw error;});
    return diagnosticsPromise;
  }
  async function loadMockSets(){
    const entry=manifest.mockSets;if(!entry)return [];
    const {value}=await readJSON(new URL(entry.url,manifestURL),entry.sha256);
    if(value.format!=='hitomon-mock-sets'||value.version!==1||value.qualificationId!==manifest.id||!Array.isArray(value.sets)||value.sets.length!==entry.count)throw contentError('模試の教材を確認できません。','模試の教材');
    return value.sets;
  }
  async function ensure(id) {
    const question = byId.get(id);
    if (!question) throw new Error('この問題は現在の教材一覧にありません。');
    if (question.hints) return question;
    const pack = packs.get(question.packId);
    if (!pack) throw contentError('この問題の教材が見つかりません。','教材');
    if (!loading.has(pack.id)) {
      const promise = readJSON(pack.url,pack.sha256).then(({value})=>{
        if (!Array.isArray(value) || value.length !== pack.count || new Set(value.map(q=>q.id)).size !== value.length) throw contentError('教材パックの件数が一致しません。','教材');
        for (const q of value) if (q.qualificationId !== manifest.id || q.packId !== pack.id || byId.get(q.id)?.packId !== pack.id) throw contentError('教材パックの問題が一致しません。','教材');
        for (const q of value) Object.assign(byId.get(q.id),assets(q));
      }).catch(error=>{loading.delete(pack.id);throw error;});
      loading.set(pack.id,promise);
    }
    await loading.get(pack.id);
    return question;
  }
  return {manifest, qualifications, questions, packs, ensure, loadAssessments, loadMockSets, loadCases:async()=>{if(!manifest.cases)return [];const {value}=await readJSON(new URL(manifest.cases.url,manifestURL),manifest.cases.sha256);if(value.format!=='hitomon-case-bank'||value.version!==2||value.qualificationId!==manifest.id||value.cases.length!==manifest.cases.count)throw contentError('記述教材を確認できません。','教材');return value.cases;}, online:loaded.online && index.online,
    loadStudyContext:()=>loadLearningTool('studyContext'),loadFlashcards:()=>loadLearningTool('flashcards'),
    loadOffline:async()=>{if(!manifest.offline)throw contentError('Offline inventory not available','保存用の教材一覧');return (await readJSON(new URL(manifest.offline.url,manifestURL),manifest.offline.sha256)).value;},
    loadAll:()=>Promise.all([...packs.keys()].map(id=>ensure(questions.find(q=>q.packId===id).id)))};
}
