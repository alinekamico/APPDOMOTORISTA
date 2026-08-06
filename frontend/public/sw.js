const CACHE_NAME = "kami-romaneios-v2";
const OFFLINE_URLS = ["/manifest.webmanifest", "/icons/icon-192.png", "/icons/icon-512.png"];

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

// Chamadas de API (mutáveis, sensíveis a estado) sempre vão pra rede, sem cache.
// Navegação/HTML: network-first — nunca serve uma página velha enquanto online (ela referencia
// nomes de arquivo _next/static/ que mudam a cada deploy e deixam de existir). Cache é só fallback offline.
// Assets estáticos com hash no nome (_next/static/...): cache-first é seguro, pois o nome só muda
// quando o conteúdo muda.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isApiCall = url.pathname.startsWith("/api");
  if (event.request.method !== "GET" || isApiCall) {
    return;
  }

  const isNavigation = event.request.mode === "navigate" || event.request.destination === "document";
  const isHashedStaticAsset = url.pathname.startsWith("/_next/static/");

  if (isHashedStaticAsset) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request).then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        });
      })
    );
    return;
  }

  if (isNavigation) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
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
