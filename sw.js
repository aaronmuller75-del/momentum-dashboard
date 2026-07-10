// Momentum Dashboard — Service Worker
// Caches the shell (HTML + data files) for offline access.
// On reload, serves cached version instantly then updates in background.

const CACHE = 'momentum-dash-v1';
const SHELL = [
  '/',
  '/dashboard.html',
  '/data/listings.js',
  '/data/calendar.js',
  '/data/goals.js',
  '/data/market_pulse.js',
  '/data/fub_tasks.js',
  '/data/scheduled_tasks.js',
  '/data/business_plan.js',
  '/data/weekly_actions.js',
  '/data/competitors.js',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  // Always hit network for API calls (live data)
  if (e.request.url.includes('/api/')) return;

  e.respondWith(
    caches.match(e.request).then(cached => {
      const net = fetch(e.request).then(r => {
        if (r.ok) {
          const clone = r.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return r;
      }).catch(() => cached);
      // Return cached immediately, update in background
      return cached || net;
    })
  );
});
