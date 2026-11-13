import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The API paths are proxied to the FastAPI backend during development. That
// keeps the browser on one origin (no CORS, and the page works when it is
// opened through a preview hostname instead of 127.0.0.1).
const BACKEND = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
// /auth is proxied too: the session is an HttpOnly cookie, so the browser must
// talk to the API on its own origin for the cookie to be stored and sent.
const apiPaths = ['/translation', '/text', '/feedback', '/ocr', '/ai', '/vocab', '/health', '/auth']

// xfwd keeps the browser's Host/proto in X-Forwarded-* headers even though
// changeOrigin rewrites Host for the backend. The auth routes use those
// headers to recognise the app's own origin when checking Origin headers and
// deciding whether cookies need Secure.
//
// The error handler matters: if nothing is listening on BACKEND, Node's proxy
// would answer with an empty 500 and the UI could only say "something went
// wrong". Returning JSON with the target makes the mistake obvious.
const proxyTarget = (path) => [
  path,
  {
    target: BACKEND,
    changeOrigin: true,
    xfwd: true,
    configure(proxyServer) {
      proxyServer.on('error', (err, _request, res) => {
        if (!res || typeof res.writeHead !== 'function' || res.headersSent) return
        res.writeHead(502, { 'Content-Type': 'application/json' })
        res.end(
          JSON.stringify({
            detail:
              `Cannot reach the API backend at ${BACKEND} (${err.code || err.message}). ` +
              'Start it with "uvicorn app.main:app", or set VITE_BACKEND_URL if it runs elsewhere.',
          }),
        )
      })
    },
  },
]

const proxy = Object.fromEntries(apiPaths.map(proxyTarget))

// Vite rejects requests whose Host header it does not recognise. Hosted
// previews use their own hostname, so it is supplied at runtime instead of
// being written into this file.
const allowedHosts = (process.env.VITE_ALLOWED_HOSTS || '')
  .split(',')
  .map((host) => host.trim())
  .filter(Boolean)

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    allowedHosts,
    proxy,
  },
  preview: {
    host: '0.0.0.0',
    allowedHosts,
    proxy,
  },
})
