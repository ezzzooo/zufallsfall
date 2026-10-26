// Offline-Speicher: Seite zuerst aus dem Netz, Cover und Schriften zuerst aus dem Speicher
const SEITE = "zufallsfall-seite";
const BILDER = "zufallsfall-bilder";
const MAX_BILDER = 100;

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));

async function netzZuerst(req) {
  const cache = await caches.open(SEITE);
  try {
    const antwort = await fetch(req);
    if (antwort.ok) cache.put(req, antwort.clone());
    return antwort;
  } catch {
    return (await cache.match(req, { ignoreSearch: true })) || (await cache.match("./", { ignoreSearch: true })) || Response.error();
  }
}

async function speicherZuerst(req) {
  const cache = await caches.open(BILDER);
  const gespeichert = await cache.match(req);
  if (gespeichert) return gespeichert;
  const antwort = await fetch(req);
  if (antwort.ok || antwort.type === "opaque") {
    await cache.put(req, antwort.clone());
    const schluessel = await cache.keys();
    for (const alt of schluessel.slice(0, Math.max(0, schluessel.length - MAX_BILDER))) await cache.delete(alt);
  }
  return antwort;
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.pathname.endsWith("version.json")) return;
  if (url.origin === location.origin) e.respondWith(netzZuerst(req));
  else if (req.destination === "image" || req.destination === "font" || url.hostname === "fonts.googleapis.com") e.respondWith(speicherZuerst(req));
});
