import React, { useEffect, useRef, useState } from 'react'
import { useAuth } from '../auth/AuthProvider'

/** Signed-in account chip: avatar, provider info, verification status, sign out. */
export default function UserButton({ className = '' }) {
  const { user, logout, resendVerification, setNotice } = useAuth()
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [resent, setResent] = useState('')
  const wrapper = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    function onPointer(event) {
      if (wrapper.current && !wrapper.current.contains(event.target)) setOpen(false)
    }
    function onKey(event) {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('pointerdown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  if (!user) return null

  const displayName = user.full_name || user.email
  const initials = displayName.trim().charAt(0).toUpperCase() || '?'

  async function handleResend() {
    setBusy(true)
    setResent('')
    try {
      const result = await resendVerification()
      setResent(
        result?.already_verified
          ? 'Your e-mail is already confirmed.'
          : result?.email_sent
            ? 'Confirmation e-mail sent.'
            : 'Link created, but e-mail delivery is not configured on this server.',
      )
    } catch (err) {
      setResent(err?.message || 'Could not send the confirmation e-mail.')
    } finally {
      setBusy(false)
    }
  }

  async function handleLogout() {
    setBusy(true)
    setResent('')
    try {
      await logout()
      setOpen(false)
    } catch (err) {
      setResent(err?.message || 'Could not sign out. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={`relative ${className}`} ref={wrapper}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex items-center gap-2 rounded-xl border border-gray-200/80 bg-white/80 px-2 py-1.5 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-white hover:shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-slate-700 dark:bg-slate-800/80 dark:text-gray-200 dark:hover:bg-slate-800"
      >
        {user.picture_url ? (
          <img
            src={user.picture_url}
            alt=""
            className="h-7 w-7 rounded-full object-cover"
            referrerPolicy="no-referrer"
          />
        ) : (
          <span className="grid h-7 w-7 place-items-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-xs font-bold text-white">
            {initials}
          </span>
        )}
        <span className="hidden max-w-[9rem] truncate md:block">{displayName}</span>
        <span aria-hidden="true" className="text-[10px] text-gray-400">
          ▾
        </span>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-2 w-72 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-900"
        >
          <div className="border-b border-gray-100 px-4 py-3 dark:border-slate-700">
            <p className="truncate text-sm font-semibold text-gray-900 dark:text-gray-100">
              {displayName}
            </p>
            <p className="truncate text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-gray-600 dark:bg-slate-800 dark:text-gray-300">
                {user.provider === 'google' ? 'Google' : 'E-mail'}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                  user.email_verified
                    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300'
                    : 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300'
                }`}
              >
                {user.email_verified ? 'Verified' : 'Unverified'}
              </span>
              {user.role === 'admin' && (
                <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-blue-700 dark:bg-blue-500/15 dark:text-blue-300">
                  Admin
                </span>
              )}
            </div>
          </div>

          <div className="space-y-1 p-2">
            {!user.email_verified && (
              <button
                type="button"
                role="menuitem"
                onClick={handleResend}
                disabled={busy}
                className="w-full rounded-lg px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-60 dark:text-gray-200 dark:hover:bg-slate-800"
              >
                {busy ? 'Sending…' : 'Resend confirmation e-mail'}
              </button>
            )}
            {resent && (
              <p className="px-3 pb-1 text-xs text-gray-500 dark:text-gray-400">{resent}</p>
            )}
            <button
              type="button"
              role="menuitem"
              onClick={handleLogout}
              disabled={busy}
              className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-60 dark:text-red-300 dark:hover:bg-red-500/10"
            >
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
