// Same-origin Vercel -> FastAPI proxy. The backend URL stays server-side, and
// cookies are forwarded so the existing HttpOnly account session still works.
module.exports = async function proxyApi(req, res) {
  const backend = (process.env.BACKEND_URL || '').replace(/\/+$/, '')
  if (!backend) {
    res.statusCode = 503
    res.setHeader('content-type', 'application/json; charset=utf-8')
    res.end(JSON.stringify({ detail: 'API backend is not configured on this deployment. Set BACKEND_URL and redeploy.' }))
    return
  }

  let backendUrl
  try {
    backendUrl = new URL(backend)
    if (backendUrl.protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(backendUrl.hostname)) {
      throw new Error('BACKEND_URL must use HTTPS outside localhost.')
    }
  } catch (error) {
    res.statusCode = 500
    res.setHeader('content-type', 'application/json; charset=utf-8')
    res.end(JSON.stringify({ detail: error.message || 'BACKEND_URL is invalid.' }))
    return
  }

  const incoming = new URL(req.url, 'https://vercel.invalid')
  const backendPath = incoming.pathname.replace(/^\/api(?=\/)/, '')
  const target = `${backend}${backendPath}${incoming.search}`
  const headers = {}
  for (const name of ['accept', 'content-type', 'cookie', 'origin', 'user-agent', 'x-requested-with']) {
    if (req.headers[name]) headers[name] = req.headers[name]
  }
  headers['x-forwarded-host'] = req.headers['x-forwarded-host'] || req.headers.host || ''
  headers['x-forwarded-proto'] = 'https'

  try {
    let body
    if (req.body !== undefined && req.body !== null) {
      body = Buffer.isBuffer(req.body)
        ? req.body
        : typeof req.body === 'string'
          ? req.body
          : JSON.stringify(req.body)
    } else {
      const chunks = []
      for await (const chunk of req) chunks.push(Buffer.from(chunk))
      body = chunks.length ? Buffer.concat(chunks) : undefined
    }
    const upstream = await fetch(target, { method: req.method, headers, body })
    const payload = Buffer.from(await upstream.arrayBuffer())
    res.statusCode = upstream.status
    for (const name of ['content-type', 'cache-control', 'www-authenticate', 'retry-after']) {
      const value = upstream.headers.get(name)
      if (value) res.setHeader(name, value)
    }
    const cookies = upstream.headers.getSetCookie?.() || []
    if (cookies.length) res.setHeader('set-cookie', cookies)
    res.end(payload)
  } catch {
    // Do not include request headers/body or upstream credentials in errors.
    res.statusCode = 502
    res.setHeader('content-type', 'application/json; charset=utf-8')
    res.end(JSON.stringify({ detail: 'Could not reach the API backend. Check BACKEND_URL and backend availability.' }))
  }
}
