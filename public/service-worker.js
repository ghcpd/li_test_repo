self.addEventListener('install', (e) => {
  e.waitUntil(caches.open('eventhub-v1').then(cache => cache.addAll(['/','/styles.css','/client.js','/admin.js'])));
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.pathname === '/api/events') {
    e.respondWith(fetch(e.request).then(res => {
      const clone = res.clone();
      caches.open('eventhub-data').then(cache => cache.put(e.request, clone));
      return res;
    }).catch(() => caches.match(e.request)));
  }
});
