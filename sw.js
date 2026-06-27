// 灵感收集器 Service Worker
// v3：HTML 改为「网络优先」，避免页面更新后被旧缓存挡住
const CACHE = 'insp-v3';
const CORE = [
  './',
  './index.html',
  './style.css',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', function(e) {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(function(c) {
      return c.addAll(CORE).catch(function() {});
    })
  );
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(keys.map(function(k) {
        if (k !== CACHE) return caches.delete(k);
      }));
    }).then(function() { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(e) {
  var url = e.request.url;
  // 接口请求不缓存，始终走网络
  if (url.includes('api.github.com') || url.includes('api.deepseek.com')) return;

  // HTML / 导航请求：网络优先，离线再用缓存（保证总是拿到最新页面）
  if (e.request.mode === 'navigate' || url.endsWith('/') || url.endsWith('index.html')) {
    e.respondWith(
      fetch(e.request).then(function(res) {
        var copy = res.clone();
        caches.open(CACHE).then(function(c) { c.put(e.request, copy); });
        return res;
      }).catch(function() {
        return caches.match(e.request).then(function(r) {
          return r || caches.match('./index.html');
        });
      })
    );
    return;
  }

  // 其它静态资源：缓存优先，网络兜底
  e.respondWith(
    caches.match(e.request).then(function(cached) {
      return cached || fetch(e.request).then(function(res) {
        var copy = res.clone();
        caches.open(CACHE).then(function(c) { c.put(e.request, copy); });
        return res;
      });
    })
  );
});
