/* Previously registered service worker kept for cleanup compatibility.
   The app no longer registers one (see src/main.jsx), but a browser that still
   has the old registration must never serve a cached sign-in screen. This
   version always goes to the network for page navigations and auth/API calls. */
const CACHE = 'etr-shell-v2'
const SHELL = ['/index.html', '/manifest.json', '/icon.svg']

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}))
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return // backend + fonts stay live

  // A navigation must always ask the server, so a fresh session is seen.
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/index.html')))
    return
  }

  // Never cache auth responses or the API.
  if (url.pathname.startsWith('/auth/') || url.pathname.startsWith('/api/')) return

  event.respondWith(
    fetch(request)
      .then((res) => {
        const copy = res.clone()
        caches.open(CACHE).then((c) => c.put(request, copy)).catch(() => {})
        return res
      })
      .catch(() => caches.match(request)),
  )
})
