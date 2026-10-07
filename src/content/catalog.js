export const appRoot = new URL('../../', import.meta.url);
export const contentCacheName = `hitomon-${appRoot.pathname}content`;

async function readJSON(url, sha256) {
  const key = new URL(url); key.search = '';
  let response, cachedFallback=false;
  try { response = await fetch(url, {cache: 'no-cache'}); }
  catch (error) {
    response = await globalThis.caches?.match(key.href);cachedFallback=true;
    if (!response) throw error;
  }
  if (!response.ok) throw new Error('教材を読み込めませんでした。');
  const text = await response.text();
  if (sha256) {
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))].map(n=>n.toString(16).padStart(2,'0')).join('');
    if (hash !== sha256) throw new Error('教材の確認に失敗しました。オンラインで開き直してください。');
  }
  const value = JSON.parse(text);
  // The first visit may load before the SW controls the page. Save public content
  // here too so a first question can be resumed offline without an extra reload.
  try {
    const cache = await globalThis.caches?.open(contentCacheName);
    await cache?.put(key.href, new Response(text, {headers:{'Content-Type':'application/json'}}));
  } catch { /* Cache quota does not turn a successful read into a failure. */ }
  return {value, online: !cachedFallback && navigator.onLine && response.headers.get('X-Hitomon-Offline') !== '1'};
}

function assets(q) {
  const resolve = path => {
    if (!path) return path;
    const url = new URL(path, appRoot);
    if (!['http:', 'https:'].includes(url.protocol)) throw new Error('教材の画像URLが正しくありません。');
    return url.href;
  };
  return {...q, sourceImages:q.sourceImages.map(resolve), image:resolve(q.image), choices:q.choices.map(c=>({...c,image:resolve(c.image)}))};
}

export async function loadCatalog(requestedId) {
  const listing = await readJSON(new URL('data/qualifications/catalog.json', appRoot));
  const qualifications = listing.value.qualifications;
  if (!Array.isArray(qualifications) || !qualifications.length) throw new Error('資格一覧を読み込めませんでした。');
  if (!requestedId && qualifications.length > 1) return {choose:true, qualifications};
  const entry = qualifications.find(q=>q.id === (requestedId || qualifications[0].id));
  if (!entry) throw new Error('この資格はまだ公開されていません。');
  const manifestURL = new URL(entry.url, new URL('data/qualifications/', appRoot));
  const loaded = await readJSON(manifestURL);
  const manifest = loaded.value;
  if (manifest.id !== entry.id) throw new Error('資格の教材が一致しません。');
  const indexURL = new URL(manifest.index.url, manifestURL);
  const index = await readJSON(indexURL, manifest.index.sha256);
  const questions = index.value.map(assets), byId = new Map(questions.map(q=>[q.id,q]));
  if (questions.length !== manifest.count || byId.size !== questions.length) throw new Error('教材一覧の件数が一致しません。');
  const packs = new Map(manifest.packs.map(pack=>[pack.id,{...pack,url:new URL(pack.url,manifestURL).href}]));
  const loading = new Map();
  let diagnosticsPromise;
  const learningPromises=new Map();
  function loadLearningTool(key){
    const entry=manifest[key];if(!entry)return Promise.resolve(null);
    if(!learningPromises.has(key))learningPromises.set(key,readJSON(new URL(entry.url,manifestURL),entry.sha256).then(({value})=>{
      const records=value[key==='studyContext'?'items':'cards'];
      if(value.qualificationId!==manifest.id||value.version!==1||!Array.isArray(records)||records.length!==entry.count)throw new Error('移動中の学習教材を確認できません。通常学習は利用できます。');
      if(key==='studyContext'&&(value.format!=='hitomon-study-context'||new Set(records.map(r=>r.questionId)).size!==records.length||records.some(r=>!byId.has(r.questionId)||!['paperless','desk'].includes(r.mode)||typeof r.reason!=='string')))throw new Error('問題の分類を確認できません。');
      return value;
    }).catch(error=>{learningPromises.delete(key);throw error;}));
    return learningPromises.get(key);
  }
  function loadDiagnostics(){
    const entry=manifest.diagnostic;
    if(!entry)return Promise.resolve([]);
    if(!diagnosticsPromise)diagnosticsPromise=readJSON(new URL(entry.url,manifestURL),entry.sha256).then(({value})=>{
      if(!Array.isArray(value)||value.length!==entry.count||entry.reviewed!==entry.count||new Set(value.map(q=>q.id)).size!==value.length||value.some(q=>!q.diagnosticOnly||byId.has(q.id)||!byId.has(q.parentQuestionId)||q.qualificationId!==manifest.id||q.enrichment!=='reviewed'))throw new Error('診断専用教材の確認に失敗しました。通常学習は利用できます。');
      return value.map(assets);
    }).catch(error=>{diagnosticsPromise=null;throw error;});
    return diagnosticsPromise;
  }
  async function ensure(id) {
    const question = byId.get(id);
    if (!question) throw new Error('この問題は現在の教材一覧にありません。');
    if (question.hints) return question;
    const pack = packs.get(question.packId);
    if (!pack) throw new Error('この問題の教材が見つかりません。');
    if (!loading.has(pack.id)) {
      const promise = readJSON(pack.url,pack.sha256).then(({value})=>{
        if (!Array.isArray(value) || value.length !== pack.count || new Set(value.map(q=>q.id)).size !== value.length) throw new Error('教材パックの件数が一致しません。');
        for (const q of value) if (q.qualificationId !== manifest.id || q.packId !== pack.id || byId.get(q.id)?.packId !== pack.id) throw new Error('教材パックの問題が一致しません。');
        for (const q of value) Object.assign(byId.get(q.id),assets(q));
      }).catch(error=>{loading.delete(pack.id);throw error;});
      loading.set(pack.id,promise);
    }
    await loading.get(pack.id);
    return question;
  }
  return {manifest, qualifications, questions, packs, ensure, loadDiagnostics, online:loaded.online && index.online,
    loadStudyContext:()=>loadLearningTool('studyContext'),loadFlashcards:()=>loadLearningTool('flashcards'),
    loadAll:()=>Promise.all([...packs.keys()].map(id=>ensure(questions.find(q=>q.packId===id).id)))};
}
