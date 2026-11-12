import React, { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthProvider'
import { authApi } from '../lib/authApi'
import {
  AuthShell,
  GoogleButton,
  Notice,
  PasswordField,
  StrengthMeter,
} from '../components/auth/parts'

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/

const COPY = {
  login: {
    eyebrow: 'Welcome back',
    title: 'Sign in to Cursive RU',
    subtitle: 'Use your e-mail and password, or continue with Google.',
  },
  register: {
    eyebrow: 'Get started',
    title: 'Create your account',
    subtitle: 'Free, and your progress stays tied to your account.',
  },
  forgot: {
    eyebrow: 'Account recovery',
    title: 'Reset your password',
    subtitle: 'We will e-mail you a secure link to choose a new password.',
  },
}

export default function AuthPage() {
  const { login, register, forgotPassword, notice, setNotice } = useAuth()
  const [mode, setMode] = useState('login')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [busy, setBusy] = useState(false)
  const [config, setConfig] = useState({
    google_enabled: false,
    email_delivery_configured: false,
  })

  useEffect(() => {
    let active = true
    authApi
      .config()
      .then((data) => {
        if (active && data) setConfig(data)
      })
      .catch(() => {
        /* the form still works; only the Google hint is affected */
      })
    return () => {
      active = false
    }
  }, [])

  function switchMode(next) {
    setMode(next)
    setError('')
    setInfo('')
    setFieldErrors({})
    setPassword('')
    setConfirm('')
    setNotice(null)
  }

  function validate() {
    const errors = {}
    const cleanEmail = email.trim()
    if (!cleanEmail) errors.email = 'Enter your e-mail address.'
    else if (!EMAIL_RE.test(cleanEmail)) errors.email = 'That e-mail address does not look right.'

    if (mode !== 'forgot') {
      if (!password) errors.password = 'Enter your password.'
      else if (mode === 'register' && password.length < 8)
        errors.password = 'Use at least 8 characters.'
      else if (mode === 'register' && !/[A-Za-z]/.test(password))
        errors.password = 'Include at least one letter.'
      else if (mode === 'register' && !/\d/.test(password))
        errors.password = 'Include at least one number.'
      if (mode === 'register' && confirm !== password)
        errors.confirm = 'The two passwords do not match.'
    }
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setInfo('')
    setNotice(null)
    if (!validate()) return

    setBusy(true)
    try {
      if (mode === 'login') {
        await login(email.trim(), password)
      } else if (mode === 'register') {
        await register(fullName.trim(), email.trim(), password)
      } else {
        const result = await forgotPassword(email.trim())
        setInfo(
          result?.email_delivery_configured
            ? 'If an account exists for that address, a reset link is on its way. The link expires in one hour.'
            : 'If an account exists for that address, a reset link was created — but this server has no e-mail delivery configured, so nothing was sent. Ask the administrator to set the SMTP variables.',
        )
      }
    } catch (err) {
      setError(err?.message || 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  const copy = COPY[mode]
  const submitLabel =
    mode === 'login' ? 'Sign in' : mode === 'register' ? 'Create account' : 'Send reset link'
  const busyLabel =
    mode === 'login' ? 'Signing in…' : mode === 'register' ? 'Creating account…' : 'Sending…'

  return (
    <AuthShell
      eyebrow={copy.eyebrow}
      title={copy.title}
      subtitle={copy.subtitle}
      footer={
        <>
          By continuing you agree to keep your account secure. Your password is stored only as
          a salted scrypt hash.
        </>
      }
    >
      {notice && (
        <Notice type={notice.type} onDismiss={() => setNotice(null)}>
          {notice.message}
        </Notice>
      )}

      {mode !== 'forgot' && (
        <>
          <GoogleButton
            enabled={Boolean(config.google_enabled)}
            onUnavailable={() =>
              setError(
                'Google sign-in is not configured on this server yet. Add GOOGLE OAuth credentials (AUTH_GOOGLE_CLIENT_ID / AUTH_GOOGLE_CLIENT_SECRET) to the backend environment.',
              )
            }
          />
          <div className="flex items-center gap-3" aria-hidden="true">
            <span className="h-px flex-1 bg-gray-200 dark:bg-slate-700" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
              or with e-mail
            </span>
            <span className="h-px flex-1 bg-gray-200 dark:bg-slate-700" />
          </div>
        </>
      )}

      <form className="space-y-3.5" onSubmit={handleSubmit} noValidate>
        {mode === 'register' && (
          <div className="space-y-1.5">
            <label
              htmlFor="full-name"
              className="block text-sm font-medium text-gray-700 dark:text-gray-200"
            >
              Full name <span className="font-normal text-gray-400">(optional)</span>
            </label>
            <input
              id="full-name"
              name="name"
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Thenuja Ganganath"
              className="w-full rounded-xl border border-gray-200 bg-white/90 px-3.5 py-2.5 text-sm text-gray-900 shadow-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-700 dark:bg-slate-900/80 dark:text-gray-100"
            />
          </div>
        )}

        <div className="space-y-1.5">
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 dark:text-gray-200"
          >
            E-mail address
          </label>
          <input
            id="email"
            name="email"
            type="email"
            inputMode="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            aria-invalid={fieldErrors.email ? 'true' : undefined}
            aria-describedby={fieldErrors.email ? 'email-error' : undefined}
            className="w-full rounded-xl border border-gray-200 bg-white/90 px-3.5 py-2.5 text-sm text-gray-900 shadow-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-500/30 dark:border-slate-700 dark:bg-slate-900/80 dark:text-gray-100"
            placeholder="you@example.com"
          />
          {fieldErrors.email && (
            <p id="email-error" className="text-xs text-red-600 dark:text-red-300">
              {fieldErrors.email}
            </p>
          )}
        </div>

        {mode !== 'forgot' && (
          <PasswordField
            label="Password"
            value={password}
            onChange={setPassword}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            error={fieldErrors.password}
            hint={mode === 'register' ? 'At least 8 characters' : undefined}
          />
        )}

        {mode === 'register' && (
          <>
            <StrengthMeter password={password} />
            <PasswordField
              label="Confirm password"
              value={confirm}
              onChange={setConfirm}
              autoComplete="new-password"
              error={fieldErrors.confirm}
              name="confirm_password"
            />
          </>
        )}

        {error && <Notice type="error">{error}</Notice>}
        {info && <Notice type="success">{info}</Notice>}

        <button type="submit" className="btn-primary w-full" disabled={busy} aria-busy={busy}>
          {busy ? (
            <>
              <span
                className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white"
                aria-hidden="true"
              />
              {busyLabel}
            </>
          ) : (
            submitLabel
          )}
        </button>
      </form>

      <div className="space-y-2 pt-1 text-center text-sm">
        {mode === 'login' && (
          <>
            <button
              type="button"
              onClick={() => switchMode('register')}
              className="font-medium text-blue-700 hover:underline dark:text-blue-300"
            >
              New here? Create an account
            </button>
            <div>
              <button
                type="button"
                onClick={() => switchMode('forgot')}
                className="text-xs text-gray-500 hover:text-gray-700 hover:underline dark:text-gray-400 dark:hover:text-gray-200"
              >
                Forgot your password?
              </button>
            </div>
          </>
        )}
        {mode === 'register' && (
          <button
            type="button"
            onClick={() => switchMode('login')}
            className="font-medium text-blue-700 hover:underline dark:text-blue-300"
          >
            Already have an account? Sign in
          </button>
        )}
        {mode === 'forgot' && (
          <button
            type="button"
            onClick={() => switchMode('login')}
            className="font-medium text-blue-700 hover:underline dark:text-blue-300"
          >
            ← Back to sign in
          </button>
        )}
      </div>
    </AuthShell>
  )
}
