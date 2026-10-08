// Bump the release and the matching URLs in index.html/app.js when changing the shell.
const RELEASE = '20261008-spec-fixes1';
const ROOT = new URL(self.registration.scope);
const PREFIX = `hitomon-${ROOT.pathname}`;
const SHELL_CACHE = `${PREFIX}shell-${RELEASE}`;
const IMAGE_CACHE = `${PREFIX}images`;
const CONTENT_CACHE = `${PREFIX}content`;
const CORE = [
  'index.html', `app.js?v=${RELEASE}`, `styles.css?v=${RELEASE}`, 'pwa.js',
  'data/qualifications/catalog.json', `manifest.webmanifest?v=${RELEASE}`,
  "src/app.js?v=20261008-spec-fixes1", "src/utils.js", "src/ui/views.js", "src/domain/study.js", "src/domain/review.js", "src/domain/planning.js", "src/domain/analytics.js", "src/domain/study-context.js", "src/domain/flashcards.js", "src/features/cards.js", "src/storage/cards.js", "src/domain/next-action.js", "src/domain/practice.js", "src/ui/field-progress.js", "src/domain/diagnostic.js", "src/ui/planning.js", "src/ui/plan-targets.js", "src/ui/plan-context.js", "src/ui/planning-drafts.js", "src/features/planning.js", "src/storage/workspace.js", "src/sync/workspace.js", "schemas/study-plan.v1.json", "src/storage/local.js", "src/storage/validate.js", "src/content/catalog.js", "src/sync/account.js", "src/sync/engine.js", "src/sync/firebase.js", "src/sync/config.js", "assets/vendor/firebase.js",
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
self.addEventListener('fetch', event => {
  const request = event.request, url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== ROOT.origin || !url.pathname.startsWith(ROOT.pathname)) return;
  const isHome = url.pathname === ROOT.pathname || url.pathname === new URL('index.html', ROOT).pathname;
  const route = url.pathname.slice(ROOT.pathname.length);
  const isQualification = /^[a-zA-Z0-9_-]+\/(index\.html)?$/.test(route);
  if (request.mode === 'navigate' && (isHome || isQualification)) {
    const key = isHome ? indexURL : new URL(route.endsWith('/') ? route+'index.html' : route, ROOT).href;
    event.respondWith(networkFirst(request, SHELL_CACHE, key, event));
  } else if (CORE_URLS.has(url.pathname)) {
    // Keep one current copy per module, including imports with an older URL revision.
    event.respondWith(networkFirst(request, SHELL_CACHE, CORE_URLS.get(url.pathname), event));
  } else if (url.pathname.startsWith(new URL('data/qualifications/', ROOT).pathname)) {
    url.search = '';
    event.respondWith(networkFirst(request, CONTENT_CACHE, url.href, event));
  } else if (url.pathname.startsWith(new URL('assets/', ROOT).pathname)) {
    url.search = '';
    event.respondWith(networkFirst(request, IMAGE_CACHE, url.href, event));
  }
});
