// Bump the release and the matching URLs in index.html/app.js when changing the shell.
const RELEASE = '20261006-choice-ui1';
const ROOT = new URL(self.registration.scope);
const PREFIX = `hitomon-${ROOT.pathname}`;
const SHELL_CACHE = `${PREFIX}shell-${RELEASE}`;
const IMAGE_CACHE = `${PREFIX}images`;
const CORE = [
  'index.html', `app.js?v=${RELEASE}`, `styles.css?v=${RELEASE}`, 'pwa.js',
  `data/questions.json?v=${RELEASE}`, `manifest.webmanifest?v=${RELEASE}`,
  'assets/icons/icon-192.png', 'assets/icons/icon-512.png', 'assets/icons/apple-touch-icon.png'
];
const CORE_PATHS = new Set(CORE.map(path => new URL(path, ROOT).pathname));
const indexURL = new URL('index.html', ROOT).href;

self.addEventListener('install', event => {
  // Installation is atomic: a failed download leaves the existing worker in place.
  event.waitUntil(caches.open(SHELL_CACHE).then(cache => cache.addAll(
    CORE.map(path => new Request(new URL(path, ROOT), {cache: 'reload'}))
  )));
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
  if (request.mode === 'navigate' && isHome) {
    event.respondWith(networkFirst(request, SHELL_CACHE, indexURL, event));
  } else if (CORE_PATHS.has(url.pathname)) {
    // Use a single current question bank regardless of its cache-busting query.
    const key = url.pathname === new URL('data/questions.json', ROOT).pathname
      ? new URL(`data/questions.json?v=${RELEASE}`, ROOT).href : request;
    event.respondWith(networkFirst(request, SHELL_CACHE, key, event));
  } else if (url.pathname.startsWith(new URL('assets/', ROOT).pathname)) {
    url.search = '';
    event.respondWith(networkFirst(request, IMAGE_CACHE, url.href, event));
  }
});
