// NaBaB Service Worker — basic offline shell + install prompt support
const CACHE_NAME = "nabab-v1";
const SHELL_ASSETS = [
  "/",
  "/manifest.json",
  "/favicon.ico",
  "/icon-192.png",
  "/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Network-first for API; cache-first for static
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Never cache API
  if (url.pathname.startsWith("/api/")) {
    return;
  }

  // Stale-while-revalidate for navigation/static
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const networkFetch = fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone)).catch(() => {});
          }
          return response;
        })
        .catch(() => cached);
      return cached || networkFetch;
    })
  );
});
