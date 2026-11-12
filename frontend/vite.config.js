import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The API paths are proxied to the FastAPI backend during development. That
// keeps the browser on one origin (no CORS, and the page works when it is
// opened through a preview hostname instead of 127.0.0.1).
const BACKEND = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
const apiPaths = ['/translation', '/text', '/feedback', '/ocr', '/ai', '/vocab', '/health']

const proxy = Object.fromEntries(
  apiPaths.map((path) => [path, { target: BACKEND, changeOrigin: true }]),
)

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
