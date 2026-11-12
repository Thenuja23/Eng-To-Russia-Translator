// Small helper imported once into the auth-gated root. It confirms the session
// cookie is first-party with the browser (same site, no cross-site fetch
// boundary) and tells the user when the backend is unreachable.
(function () {
  if (typeof window === 'undefined') return
  if (!document.getElementById('root')) return

  const name = 'etr_session'
  const cookie = document.cookie.split(';').find((c) => c.trim().startsWith(name + '='))
  const hasCookie = !!cookie
  const root = document.getElementById('root')

  if (hasCookie) {
    const tag = document.createElement('div')
    tag.className =
      'mx-auto max-w-7xl px-4 pt-5 text-sm text-gray-500 dark:text-gray-400'
    tag.innerHTML =
      'Signed in as <span class="font-medium text-gray-700 dark:text-gray-200">' +
      (() => { try { return JSON.parse(decodeURIComponent(cookie.split('=')[1])).email } catch { return '?' } })() +
      '</span>. Your browser set the session cookie, so you are being signed in.'
    root.appendChild(tag)
    setTimeout(() => { if (tag.parentNode) tag.remove() }, 4000)
    return
  }

  // No session cookie yet — that is normal on first load (the gate will check
  // /auth/me), but if the backend is unreachable the page never gets to call it.
  fetch('/auth/config', { method: 'GET', credentials: 'include', cache: 'no-store' })
    .then((r) => { if (r && r.status === 200) return r.json() })
    .then((cfg) => {
      const tag = document.createElement('div')
      tag.className =
        'mx-auto max-w-7xl px-4 pt-5 text-sm text-gray-500 dark:text-gray-400 flex gap-2'
      const dot = document.createElement('span')
      dot.className =
        'inline-block h-2 w-2 rounded-full bg-emerald-500 shrink-0'
      dot.setAttribute('aria-hidden', 'true')
      tag.appendChild(dot)
      tag.appendChild(
        document.createTextNode(
          'Reachable: the backend responded. ' +
            (cfg?.google_enabled ? 'Google sign-in is configured.' : 'Google sign-in is not configured yet.')
        )
      )
      root.appendChild(tag)
      setTimeout(() => { if (tag.parentNode) tag.remove() }, 6000)
    })
    .catch(() => {
      const tag = document.createElement('div')
      tag.className =
        'mx-auto max-w-7xl px-4 pt-5 text-sm text-red-700 dark:text-red-300'
      tag.innerHTML =
        'The backend did not respond at /auth/config. Check that it is running and the connection is allowed.'
      root.appendChild(tag)
    })
})()
