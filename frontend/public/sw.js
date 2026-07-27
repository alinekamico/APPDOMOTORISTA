const CACHE_NAME = "kami-romaneios-v1";
const OFFLINE_URLS = ["/", "/manifest.webmanifest", "/icons/icon-192.png", "/icons/icon-512.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_URLS)).catch(() => undefined)
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

// Cache-first apenas para assets estáticos; chamadas de API (mutáveis, sensíveis a estado) sempre vão pra rede.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isApiCall = url.pathname.startsWith("/api");
  if (event.request.method !== "GET" || isApiCall) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).catch(
        () => cached ?? new Response("", { status: 503, statusText: "Offline" })
      );
    })
  );
});
