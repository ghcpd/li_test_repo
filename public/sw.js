const CACHE_NAME = 'event-manager-v1';
const urlsToCache = [
    '/',
    '/css/styles.css',
    '/js/app.js',
    '/admin',
    '/admin/js/admin.js',
    '/admin/css/admin.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Install event - cache resources
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
            .catch(error => {
                console.error('Cache install failed:', error);
            })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch from network
                if (response) {
                    return response;
                }

                // For API requests, try network first, then fallback
                if (event.request.url.includes('/api/')) {
                    return fetch(event.request)
                        .catch(() => {
                            // Return cached events if available
                            if (event.request.url.includes('/api/events') && event.request.method === 'GET') {
                                return new Response(
                                    JSON.stringify([]),
                                    {
                                        headers: { 'Content-Type': 'application/json' },
                                        status: 200
                                    }
                                );
                            }
                            throw new Error('Network failed and no cache available');
                        });
                }

                return fetch(event.request);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});