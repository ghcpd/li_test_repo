const CACHE_NAME = 'eventhub-cache-v1';
const CORE_ASSETS = [
  '/',
  '/index.html',
  '/style.css',
  '/app.js',
  '/admin.html',
  '/admin.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  // Cache-first for core assets
  if (CORE_ASSETS.some((asset) => new URL(request.url).pathname === asset)) {
    event.respondWith(
      caches.match(request).then((resp) => resp || fetch(request))
    );
    return;
  }

  // For API GET requests, try network then cache; cache successful responses
  if (new URL(request.url).pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((resp) => {
          const copy = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          return resp;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // Default: network first, fallback to cache
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});
