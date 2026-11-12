// Authentication client.
//
// Auth calls deliberately use a relative path, never an absolute API host: the
// session lives in an HttpOnly cookie, and a cookie is only sent back to the
// origin that set it. Going through the Vite proxy (or a same-origin reverse
// proxy in production) keeps the cookie first-party, which is also why no token
// is ever written to localStorage.
const BASE = ''

export class AuthError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'AuthError'
    this.status = status
  }
}

async function request(path, { method = 'GET', body } = {}) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      credentials: 'include',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      cache: 'no-store',
    })
  } catch {
    throw new AuthError('Cannot reach the server. Check your connection and try again.', 0)
  }

  if (res.status === 204) return null

  let data = null
  try {
    data = await res.json()
  } catch {
    data = null
  }

  if (!res.ok) {
    const detail = data && data.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail) && detail[0]?.msg
          ? detail[0].msg
          : 'Something went wrong. Please try again.'
    throw new AuthError(message, res.status)
  }
  return data
}

export const authApi = {
  config: () => request('/auth/config'),
  me: () => request('/auth/me'),
  register: (payload) => request('/auth/register', { method: 'POST', body: payload }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  forgotPassword: (email) =>
    request('/auth/forgot-password', { method: 'POST', body: { email } }),
  resetPassword: (token, password) =>
    request('/auth/reset-password', { method: 'POST', body: { token, password } }),
  verifyEmail: (token) => request('/auth/verify-email', { method: 'POST', body: { token } }),
  resendVerification: () => request('/auth/resend-verification', { method: 'POST' }),
  updateProfile: (full_name) =>
    request('/auth/profile', { method: 'PATCH', body: { full_name } }),
}

export const googleStartUrl = '/auth/google/start'
