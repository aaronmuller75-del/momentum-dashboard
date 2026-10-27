// Momentum Dashboard — Service Worker v3
// Network-first with graceful offline fallback (never returns null)

const CACHE = 'momentum-dash-v3';

self.addEventListener('install', e => {
  e.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const OFFLINE_HTML = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Momentum Dashboard — Server Offline</title>
<style>
  body { font-family: -apple-system, sans-serif; display: flex; align-items: center;
         justify-content: center; min-height: 100vh; margin: 0;
         background: #002072; color: white; text-align: center; padding: 20px; box-sizing: border-box; }
  h1 { font-size: 1.4rem; margin-bottom: 12px; }
  p  { font-size: .9rem; opacity: .8; margin-bottom: 20px; line-height: 1.5; }
  code { background: rgba(255,255,255,.15); padding: 8px 14px; border-radius: 8px;
         font-size: .85rem; display: block; margin: 10px auto; max-width: 400px; }
  button { background: #E05A2B; color: white; border: none; padding: 12px 28px;
           border-radius: 8px; font-size: .95rem; cursor: pointer; margin-top: 8px; }
</style></head>
<body>
  <div>
    <h1>⚠️ Dashboard Server Offline</h1>
    <p>The local server isn't running.<br>Open Terminal on your Mac and paste:</p>
    <code>python3 ~/Desktop/Claude/Dashboard/server.py &</code>
    <br>
    <button onclick="location.reload()">↻ Try Again</button>
  </div>
</body></html>`;

self.addEventListener('fetch', e => {
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok && e.request.method === 'GET' && !e.request.url.includes('/api/')) {
        caches.open(CACHE).then(c => c.put(e.request, r.clone()));
      }
      return r;
    }).catch(async () => {
      const cached = await caches.match(e.request);
      if (cached) return cached;
      // Return branded offline page instead of crashing
      return new Response(OFFLINE_HTML, {
        status: 503,
        headers: { 'Content-Type': 'text/html' }
      });
    })
  );
});
