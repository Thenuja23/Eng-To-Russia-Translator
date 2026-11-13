import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// The app intentionally does not register a service worker.
//
// Older builds shipped an app-shell service worker that served a cached copy of
// the index page (the sign-in screen). After a successful login the browser
// kept showing that stale screen even though the backend had issued a session.
// Actively remove any registration left behind by a previous build and drop its
// caches. This has to run for existing users too, not just for new builds.
if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
  const cleanup = () => {
    navigator.serviceWorker
      .getRegistrations()
      .then((registrations) => Promise.all(registrations.map((r) => r.unregister())))
      .catch(() => {})
  }
  if (document.readyState === 'complete') cleanup()
  else window.addEventListener('load', cleanup, { once: true })
}

if (typeof window !== 'undefined' && 'caches' in window) {
  const clearCaches = () => {
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith('etr-'))
            .map((key) => caches.delete(key)),
        ),
      )
      .catch(() => {})
  }
  if (document.readyState === 'complete') clearCaches()
  else window.addEventListener('load', clearCaches, { once: true })
}
