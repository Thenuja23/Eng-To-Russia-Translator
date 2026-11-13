import React, { useId, useState } from 'react'

/** Two-column auth layout that keeps the existing app look and works on mobile. */
export function AuthShell({ eyebrow = 'Your account', title, subtitle, children, footer }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-white/60 bg-white/70 backdrop-blur-xl dark:bg-slate-950/70 dark:border-slate-700/50">
        <div className="max-w-6xl mx-auto px-4 md:px-6 h-16 flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white text-lg font-bold shadow-md shadow-blue-600/30">
            я
          </span>
          <span className="leading-tight">
            <span className="block text-sm font-bold tracking-tight text-gray-900 dark:text-gray-100">
              Cursive&nbsp;RU
            </span>
            <span className="block text-[11px] text-gray-500 dark:text-gray-400">
              reading &amp; writing assistant
            </span>
          </span>
        </div>
      </header>

      <main className="flex-1 grid lg:grid-cols-2 gap-8 lg:gap-12 max-w-6xl w-full mx-auto px-4 md:px-6 py-8 md:py-14 items-center">
        <section className="hidden lg:block space-y-5 animate-fade-in">
          <p className="eyebrow">Russian vocabulary assistant</p>
          <h1 className="text-3xl xl:text-4xl font-bold tracking-tight text-gray-900 dark:text-gray-100 leading-tight">
            Speak, snap or type Russian.
            <br />
            Get every word explained.
          </h1>
          <p className="text-gray-600 dark:text-gray-300 max-w-md">
            Pronunciation, English and Sinhala meanings, part of speech, grammar notes
            and two translated examples for each word you bring.
          </p>
          <ul className="space-y-2.5 text-sm text-gray-600 dark:text-gray-300">
            {[
              'Voice, photo and keyboard input',
              'Word-by-word grammar, beginner friendly',
              'සිංහල අර්ථ සහ ව්‍යාකරණ පැහැදිලි කිරීම්',
            ].map((item) => (
              <li key={item} className="flex items-start gap-2.5">
                <span
                  aria-hidden="true"
                  className="mt-1 grid h-4 w-4 shrink-0 place-items-center rounded-full bg-blue-100 text-[10px] font-bold text-blue-700 dark:bg-blue-500/20 dark:text-blue-300"
                >
                  ✓
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="w-full max-w-md mx-auto lg:mx-0 lg:justify-self-end">
          <div className="card">
            <div className="card-header">
              <p className="eyebrow">{eyebrow}</p>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mt-0.5">
                {title}
              </h2>
              {subtitle && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{subtitle}</p>
              )}
            </div>
            <div className="card-body space-y-4">{children}</div>
          </div>
          {footer && (
            <p className="mt-4 text-center text-xs text-gray-500 dark:text-gray-400">{footer}</p>
          )}
        </section>
      </main>
    </div>
  )
}

export function Notice({ type = 'info', children, onDismiss }) {
  if (!children) return null
  const styles =
    type === 'error'
      ? 'border-red-200 bg-red-50 text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-200'
      : type === 'success'
        ? 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-200'
        : 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-200'
  return (
    <div
      role={type === 'error' ? 'alert' : 'status'}
      className={`flex items-start justify-between gap-3 rounded-xl border px-3.5 py-2.5 text-sm ${styles}`}
    >
      <span>{children}</span>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded px-1 text-xs font-semibold opacity-70 hover:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current"
          aria-label="Dismiss message"
        >
          ✕
        </button>
      )}
    </div>
  )
}

/** Password input with a visibility toggle (required for both fields). */
export function PasswordField({
  label,
  value,
  onChange,
  autoComplete = 'current-password',
  error,
  hint,
  id,
  name,
  disabled = false,
}) {
  const [visible, setVisible] = useState(false)
  const generatedId = useId()
  const fieldId = id || `password-${generatedId}`
  return (
    <div className="space-y-1.5">
      <label
        htmlFor={fieldId}
        className="block text-sm font-medium text-gray-700 dark:text-gray-200"
      >
        {label}
      </label>
      <div className="relative">
        <input
          id={fieldId}
          name={name || 'password'}
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          disabled={disabled}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error || hint ? `${fieldId}-help` : undefined}
          className="w-full rounded-xl border border-gray-200 bg-white/90 px-3.5 py-2.5 pr-16 text-sm text-gray-900 shadow-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-500/30 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900/80 dark:text-gray-100"
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          disabled={disabled}
          className="absolute inset-y-0 right-1.5 my-auto h-7 rounded-lg px-2 text-xs font-semibold text-blue-700 hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:text-blue-300 dark:hover:bg-slate-800"
          aria-label={visible ? 'Hide password' : 'Show password'}
        >
          {visible ? 'Hide' : 'Show'}
        </button>
      </div>
      {(error || hint) && (
        <p
          id={`${fieldId}-help`}
          className={`text-xs ${error ? 'text-red-600 dark:text-red-300' : 'text-gray-500 dark:text-gray-400'}`}
        >
          {error || hint}
        </p>
      )}
    </div>
  )
}

/** Simple four-step strength meter mirroring the server's rules. */
export function StrengthMeter({ password }) {
  const value = password || ''
  const checks = [
    value.length >= 8,
    value.length >= 12,
    /[A-Za-z]/.test(value) && /\d/.test(value),
    /[^A-Za-z0-9]/.test(value) || /[A-Z]/.test(value),
  ]
  const score = checks.filter(Boolean).length
  const labels = ['Too short', 'Weak', 'Fair', 'Good', 'Strong']
  const colors = [
    'bg-gray-300 dark:bg-slate-600',
    'bg-red-400',
    'bg-amber-400',
    'bg-lime-500',
    'bg-emerald-500',
  ]
  return (
    <div className="space-y-1.5" aria-live="polite">
      <div className="flex gap-1.5" aria-hidden="true">
        {[0, 1, 2, 3].map((index) => (
          <span
            key={index}
            className={`h-1.5 flex-1 rounded-full ${
              index < score ? colors[score] : 'bg-gray-200 dark:bg-slate-700'
            }`}
          />
        ))}
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Password strength: <span className="font-medium">{labels[score]}</span> · at least 8
        characters with a letter and a number
      </p>
    </div>
  )
}

/** Google's official four-colour mark (brand guidelines: no recolouring). */
function GoogleMark() {
  return (
    <svg viewBox="0 0 48 48" className="h-5 w-5" aria-hidden="true" focusable="false">
      <path
        fill="#EA4335"
        d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
      />
      <path
        fill="#4285F4"
        d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
      />
      <path
        fill="#FBBC05"
        d="M10.53 28.59A14.5 14.5 0 0 1 9.77 24c0-1.58.28-3.11.76-4.59l-7.98-6.19A23.94 23.94 0 0 0 0 24c0 3.88.93 7.54 2.56 10.78l7.97-6.19z"
      />
      <path
        fill="#34A853"
        d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.46-9.9l-7.97 6.19C6.51 42.62 14.62 48 24 48z"
      />
    </svg>
  )
}

/**
 * Google sign-in button. When the backend has no OAuth credentials the button
 * says so instead of pretending to start a login.
 */
export function GoogleButton({ enabled, disabled, onUnavailable, busy = false, onStart }) {
  if (enabled) {
    return (
      <button
        type="button"
        disabled={disabled || busy}
        onClick={onStart}
        className="flex w-full items-center justify-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 hover:shadow disabled:cursor-wait disabled:opacity-60 dark:border-slate-600 dark:bg-slate-100 dark:text-gray-800 dark:hover:bg-white"
        aria-label={busy ? 'Connecting to Google' : 'Continue with Google'}
        aria-busy={busy}
      >
        <GoogleMark />
        {busy ? 'Connecting to Google…' : 'Continue with Google'}
      </button>
    )
  }
  return (
    <div className="space-y-1.5">
      <button
        type="button"
        onClick={onUnavailable}
        aria-disabled="true"
        className="flex w-full cursor-not-allowed items-center justify-center gap-3 rounded-xl border border-dashed border-gray-300 bg-white/60 px-4 py-2.5 text-sm font-medium text-gray-400 dark:border-slate-600 dark:bg-slate-800/40 dark:text-gray-500"
      >
        <GoogleMark />
        Continue with Google
      </button>
      <p className="text-[11px] text-gray-500 dark:text-gray-400">
        Not connected yet — the server needs Google OAuth credentials.
      </p>
    </div>
  )
}
