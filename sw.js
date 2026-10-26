// Bump the release and the matching URLs in index.html/app.js when changing the shell.
const RELEASE = '20261026-fp2-202501';
const ROOT = new URL(self.registration.scope);
const PREFIX = `hitomon-${ROOT.pathname}`;
const SHELL_CACHE = `${PREFIX}shell-${RELEASE}`;
const IMAGE_CACHE = `${PREFIX}images`;
const CONTENT_CACHE = `${PREFIX}content`;
const CORE = [
  'src/domain/decimal-answer.js','src/domain/legal-context.js','src/ui/legal-context.js',
  'src/domain/study-queue.js','src/domain/offline-assets.js','src/features/offline.js','src/features/offline-store.js',
  'src/storage/sync-cursor.js',
  'src/v2/records.js', 'src/v2/resources.js', 'src/domain/case-study.js', 'src/features/written.js',
  'src/domain/sync-status.js', 'src/ui/sync-status.js', 'src/domain/guest-import.js', 'src/ui/plan-conflict.js', 'src/content/errors.js',
  'src/ui/qualification-navigation.js', 'src/domain/study-target.js', 'src/domain/qualification-features.js',
  'index.html', `app.js?v=${RELEASE}`, `styles.css?v=${RELEASE}`, 'pwa.js',
  'data/qualifications/catalog.json', `manifest.webmanifest?v=${RELEASE}`,
  "src/domain/plan-history.js", "src/ui/plan-history.js", "src/ui/learning-trend.js", "src/domain/mock.js", "src/domain/content-policy.js", "src/domain/assessment-policy.js", "src/domain/assessment-sampling.js", "src/domain/assessment.js", "src/ui/mocks.js", "src/domain/personal.js", "src/features/personal.js", "src/app.js?v=20261026-fp2-202501", "src/domain/learning-state.js", "src/features/learning.js", "src/features/ai-handoff.js", "src/utils.js", "src/ui/views.js", "src/ui/image-zoom.js", "src/domain/study.js", "src/domain/question-format.js", "src/domain/review.js", "src/domain/planning.js", "src/domain/analytics.js", "src/domain/study-context.js", "src/domain/flashcards.js", "src/domain/card-sync.js", "src/features/cards.js", "src/storage/cards.js", "src/domain/next-action.js", "src/domain/practice.js", "src/ui/field-progress.js", "src/domain/diagnostic.js", "src/ui/planning.js", "src/ui/plan-targets.js", "src/ui/plan-context.js", "src/ui/planning-drafts.js", "src/features/planning.js", "src/storage/workspace.js", "src/sync/workspace.js", "schemas/study-plan.v2.json", "src/storage/local.js", "src/storage/validate.js", "src/content/catalog.js", "src/sync/account.js", "src/sync/engine.js", "src/sync/firebase.js", "src/sync/config.js", "assets/vendor/firebase.js",
  'src/ui/case-body.js','src/ui/study-controls.js','src/ui/inline-text.js', 'src/ui/question-text.js', 'assets/vendor/katex/katex.mjs', 'assets/vendor/katex/katex.min.css', 'assets/vendor/katex/fonts/KaTeX_AMS-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Caligraphic-Bold.woff2', 'assets/vendor/katex/fonts/KaTeX_Caligraphic-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Fraktur-Bold.woff2', 'assets/vendor/katex/fonts/KaTeX_Fraktur-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Main-Bold.woff2', 'assets/vendor/katex/fonts/KaTeX_Main-BoldItalic.woff2', 'assets/vendor/katex/fonts/KaTeX_Main-Italic.woff2', 'assets/vendor/katex/fonts/KaTeX_Main-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Math-BoldItalic.woff2', 'assets/vendor/katex/fonts/KaTeX_Math-Italic.woff2', 'assets/vendor/katex/fonts/KaTeX_SansSerif-Bold.woff2', 'assets/vendor/katex/fonts/KaTeX_SansSerif-Italic.woff2', 'assets/vendor/katex/fonts/KaTeX_SansSerif-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Script-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Size1-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Size2-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Size3-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Size4-Regular.woff2', 'assets/vendor/katex/fonts/KaTeX_Typewriter-Regular.woff2',
  'assets/icons/icon-192.png', 'assets/icons/icon-512.png', 'assets/icons/apple-touch-icon.png'
];
const CORE_URLS = new Map(CORE.map(path => {
  const url = new URL(path, ROOT);
  return [url.pathname, url.href];
}));
const indexURL = new URL('index.html', ROOT).href;

self.addEventListener('install', event => {
  // Installation is atomic: a failed download leaves the existing worker in place.
  event.waitUntil((async()=>{
    const cache=await caches.open(SHELL_CACHE);
    await cache.addAll(CORE.map(path => new Request(new URL(path, ROOT), {cache:'reload'})));
    // A first direct visit to a qualification happens before SW control. Save
    // that entry too; the root shell cannot supply another qualification's ID.
    const pages=await self.clients.matchAll({type:'window',includeUncontrolled:true});
    const entries=new Set();
    // Keep every qualification entry in the same release as its JS/CSS, even
    // when the worker was installed from the shared qualification chooser.
    const listing=await (await cache.match(new URL('data/qualifications/catalog.json',ROOT))).json();
    for(const q of listing.qualifications||[]){
      if(/^[a-zA-Z0-9_-]+$/.test(q.id))entries.add(new URL(q.id+'/index.html',ROOT).href);
    }
    for(const page of pages){
      const url=new URL(page.url),relative=url.pathname.slice(ROOT.pathname.length);
      if(url.origin===ROOT.origin&&url.pathname.startsWith(ROOT.pathname)&&/^[a-zA-Z0-9_-]+\/(?:index\.html)?$/.test(relative))entries.add(new URL(relative.endsWith('/')?relative+'index.html':relative,ROOT).href);
    }
    await cache.addAll([...entries].map(url=>new Request(url,{cache:'reload'})));
  })());
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith(`${PREFIX}shell-`) && key !== SHELL_CACHE)
      .map(key => caches.delete(key)));
    // Keep already-opened question images across releases.
    await self.clients.claim();
  })());
});
self.addEventListener('message', event => {
  if(event.data?.type==='OFFLINE_READY')event.ports[0]?.postMessage({offlineProtocol:1});
  if (event.data?.type === 'ACTIVATE_UPDATE') self.skipWaiting();
});

async function networkFirst(request, cacheName, cacheKey, event) {
  const cache = await caches.open(cacheName);
  const signal = online => {
    const clientId = event.clientId || event.resultingClientId;
    if (clientId) event.waitUntil(self.clients.get(clientId).then(client =>
      client?.postMessage({type: 'NETWORK_STATUS', online})).catch(() => {}));
  };
  const offlineResponse = saved => {
    const headers = new Headers(saved.headers);
    headers.set('X-Hitomon-Offline', '1');
    return new Response(saved.body, {status: saved.status, statusText: saved.statusText, headers});
  };
  try {
    const response = await fetch(request, {cache: 'no-cache'});
    signal(true);
    if (response.ok && response.type !== 'opaque') {
      // Cache writes must not turn a successful page load into a failure (e.g. quota full).
      event.waitUntil(cache.put(cacheKey, response.clone()).catch(() => {}));
      return response;
    }
    return await cache.match(cacheKey) || response;
  } catch (error) {
    signal(false);
    const saved = await cache.match(cacheKey);
    if (saved) return offlineResponse(saved);
    throw error;
  }
}

async function cacheFirst(request, cacheName, cacheKey, event) {
  const cache=await caches.open(cacheName);
  return await cache.match(cacheKey) || networkFirst(request,cacheName,cacheKey,event);
}

async function imageWithFallback(request, cacheKey, event) {
  const saved=await (await caches.open(IMAGE_CACHE)).match(cacheKey);
  // Explicit downloads must receive fresh bytes for the inventory's SHA check.
  if(!saved||request.cache==='reload')return networkFirst(request,IMAGE_CACHE,cacheKey,event);
  const refresh=networkFirst(request,IMAGE_CACHE,cacheKey,event);
  event.waitUntil(refresh.catch(()=>{}));
  let timer;
  try {
    // Prefer a quick fresh response; a weak connection must not hide a saved diagram.
    return await Promise.race([refresh,new Promise(resolve=>{timer=setTimeout(()=>resolve(saved),300);})]);
  } finally {clearTimeout(timer);}
}

async function refreshInBackground(request, cacheKey, event) {
  const cache=await caches.open(CONTENT_CACHE);
  let saved=await cache.match(cacheKey);
  // The chooser's initial listing is part of the atomically installed shell.
  if(!saved&&cacheKey===new URL('data/qualifications/catalog.json',ROOT).href)
    saved=await (await caches.open(SHELL_CACHE)).match(cacheKey);
  const refresh=networkFirst(request,CONTENT_CACHE,cacheKey,event);
  if(!saved)return refresh;
  event.waitUntil(refresh.catch(()=>{}));
  const headers=new Headers(saved.headers);
  headers.set('X-Hitomon-Cache','1');
  return new Response(saved.body,{status:saved.status,statusText:saved.statusText,headers});
}

self.addEventListener('fetch', event => {
  const request = event.request, url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== ROOT.origin || !url.pathname.startsWith(ROOT.pathname)) return;
  const isHome = url.pathname === ROOT.pathname || url.pathname === new URL('index.html', ROOT).pathname;
  const route = url.pathname.slice(ROOT.pathname.length);
  const isQualification = /^[a-zA-Z0-9_-]+\/(index\.html)?$/.test(route);
  if (request.mode === 'navigate' && (isHome || isQualification)) {
    const key = isHome ? indexURL : new URL(route.endsWith('/') ? route+'index.html' : route, ROOT).href;
    event.respondWith(cacheFirst(request, SHELL_CACHE, key, event));
  } else if (url.pathname.startsWith(new URL('data/qualifications/', ROOT).pathname)) {
    url.search = '';
    const immutable=/\.[a-f0-9]{16}\.json$/.test(url.pathname);
    event.respondWith(request.cache==='reload'
      ?networkFirst(request,CONTENT_CACHE,url.href,event)
      :immutable?cacheFirst(request,CONTENT_CACHE,url.href,event)
      :refreshInBackground(request,url.href,event));
  } else if (CORE_URLS.has(url.pathname)) {
    // Serve a complete release. A waiting worker replaces it only on activation.
    event.respondWith(cacheFirst(request, SHELL_CACHE, CORE_URLS.get(url.pathname), event));
  } else if (url.pathname.startsWith(new URL('assets/', ROOT).pathname)) {
    url.search = '';
    event.respondWith(imageWithFallback(request, url.href, event));
  }
});
