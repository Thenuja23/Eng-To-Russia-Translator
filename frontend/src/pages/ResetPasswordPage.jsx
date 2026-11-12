import React, { useState } from 'react'
import { useAuth } from '../auth/AuthProvider'
import { AuthShell, Notice, PasswordField, StrengthMeter } from '../components/auth/parts'

export default function ResetPasswordPage() {
  const { resetPassword } = useAuth()
  const params =
    typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null
  const token = params?.get('token') || ''

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    if (password.length < 8 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      setError('Use at least 8 characters, including a letter and a number.')
      return
    }
    if (password !== confirm) {
      setError('The two passwords do not match.')
      return
    }
    setBusy(true)
    try {
      await resetPassword(token, password)
      setDone(true)
      setPassword('')
      setConfirm('')
    } catch (err) {
      setError(err?.message || 'That link could not be used. Please request a new one.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell
      eyebrow="Account recovery"
      title={done ? 'Password updated' : 'Choose a new password'}
      subtitle={
        done
          ? 'You have been signed out of other sessions for safety.'
          : 'Pick something you have not used before.'
      }
      footer="Reset links expire after one hour and can only be used once."
    >
      {!token && (
        <Notice type="error">
          This page needs a reset link. Open the link from your e-mail, or request a new one from
          the sign-in screen.
        </Notice>
      )}

      {done ? (
        <>
          <Notice type="success">Your password has been changed. Sign in with the new one.</Notice>
          <a href="/" className="btn-primary w-full">
            Go to sign in
          </a>
        </>
      ) : (
        <form className="space-y-3.5" onSubmit={handleSubmit} noValidate>
          <PasswordField
            label="New password"
            value={password}
            onChange={setPassword}
            autoComplete="new-password"
            disabled={!token}
          />
          <StrengthMeter password={password} />
          <PasswordField
            label="Confirm new password"
            value={confirm}
            onChange={setConfirm}
            autoComplete="new-password"
            name="confirm_password"
          />
          {error && <Notice type="error">{error}</Notice>}
          <button
            type="submit"
            className="btn-primary w-full"
            disabled={busy || !token}
            aria-busy={busy}
          >
            {busy ? 'Updating…' : 'Update password'}
          </button>
          <a
            href="/"
            className="block text-center text-sm font-medium text-blue-700 hover:underline dark:text-blue-300"
          >
            Back to sign in
          </a>
        </form>
      )}
    </AuthShell>
  )
}
