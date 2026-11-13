import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { authApi } from '../lib/authApi'

const AuthContext = createContext(null)

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside <AuthProvider>')
  return value
}

/** Messages for the redirects the backend uses to report OAuth/verification outcomes. */
const REDIRECT_MESSAGES = {
  'google_not_configured':
    'Google sign-in is not configured on this server yet. Add the Google OAuth credentials to the backend .env file.',
  'google_access_denied': 'Google sign-in was cancelled.',
  'google_state': 'That Google sign-in attempt expired or did not match this browser. Please try again.',
  'google_expired': 'That Google sign-in attempt expired. Please try again.',
  'google_failed': 'Google sign-in could not be completed. Please try again.',
  'google_email': 'Google did not confirm an e-mail address for that account.',
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState(() => readRedirectNotice())

  // Automatic authentication-state detection: one authoritative server call.
  const refresh = useCallback(async () => {
    try {
      const data = await authApi.me()
      setUser(data?.user ?? null)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await authApi.me()
        if (!cancelled) setUser(data?.user ?? null)
      } catch {
        if (!cancelled) setUser(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const applyUser = useCallback((nextUser, message = '') => {
    setUser(nextUser)
    if (message) setNotice({ type: 'success', message })
  }, [])

  const login = useCallback(
    async (email, password) => {
      const data = await authApi.login({ email, password })
      applyUser(data.user, 'Welcome back!')
      return data.user
    },
    [applyUser],
  )

  const register = useCallback(
    async (fullName, email, password) => {
      const data = await authApi.register({
        full_name: fullName,
        email,
        password,
      })
      applyUser(
        data.user,
        data.email_sent
          ? 'Account created. We sent you a link to confirm your e-mail address.'
          : 'Account created. E-mail delivery is not configured on this server, so the confirmation link cannot be sent yet.',
      )
      return data
    },
    [applyUser],
  )

  const logout = useCallback(async () => {
    await authApi.logout()
    setUser(null)
    setNotice({ type: 'success', message: 'You have been signed out.' })
  }, [])

  const forgotPassword = useCallback((email) => authApi.forgotPassword(email), [])
  const resetPassword = useCallback((token, password) => authApi.resetPassword(token, password), [])
  const verifyEmail = useCallback(
    async (token) => {
      await authApi.verifyEmail(token)
      await refresh()
    },
    [refresh],
  )
  const resendVerification = useCallback(async () => {
    const data = await authApi.resendVerification()
    return data
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      notice,
      setNotice,
      login,
      register,
      logout,
      forgotPassword,
      resetPassword,
      verifyEmail,
      resendVerification,
      refresh,
    }),
    [
      user,
      loading,
      notice,
      login,
      register,
      logout,
      forgotPassword,
      resetPassword,
      verifyEmail,
      resendVerification,
      refresh,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function readRedirectNotice() {
  if (typeof window === 'undefined') return null
  const params = new URLSearchParams(window.location.search)
  const error = params.get('auth_error')
  const verify = params.get('verify')
  const signedIn = params.get('signed_in')

  let notice = null
  if (error) {
    notice = {
      type: 'error',
      message: REDIRECT_MESSAGES[error] || 'Sign-in failed. Please try again.',
    }
  } else if (verify === 'ok') {
    notice = { type: 'success', message: 'Your e-mail address is confirmed.' }
  } else if (verify === 'invalid') {
    notice = {
      type: 'error',
      message: 'That confirmation link is invalid or has expired. Request a new one below.',
    }
  } else if (signedIn) {
    notice = { type: 'success', message: 'Signed in with Google.' }
  }

  if (error || verify || signedIn) {
    // Drop the query string so a refresh does not replay the message.
    const clean = window.location.pathname + window.location.hash
    window.history.replaceState({}, document.title, clean)
  }
  return notice
}
