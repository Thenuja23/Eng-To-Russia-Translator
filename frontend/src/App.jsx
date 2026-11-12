import React, { useState } from 'react'
import WritingPage from './pages/WritingPage'
import VocabularyPage from './pages/VocabularyPage'
import AlphabetChart from './components/AlphabetChart'
import TrapLetterDrills from './components/TrapLetterDrills'
import Flashcards from './components/Flashcards'
import PracticeSheet from './components/PracticeSheet'
import FontTest from './components/FontTest'
import TapWordView from './components/TapWordView'
import EditableOCRScreen from './components/EditableOCRScreen'
import FeedbackForm from './components/FeedbackForm'
import ThemeToggle from './components/ThemeToggle'
import ImageInput from './components/ImageInput'
import AiStudio from './components/AiStudio'
import UserButton from './components/UserButton'
import { AuthProvider, useAuth } from './auth/AuthProvider'
import './auth/wait-for-auth.js'

import AuthPage from './pages/AuthPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import { Notice } from './components/auth/parts'

/**
 * Company logo mark. Falls back to the Я monogram if the logo file
 * cannot be loaded, and sits on a white plate so it stays visible in
 * both light and dark themes (the logo PNG is transparent).
 */
function BrandMark() {
  const [failed, setFailed] = useState(false)

  if (failed) {
    return (
      <span
        aria-hidden="true"
        className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white text-lg font-bold shadow-md shadow-blue-600/30"
      >
        я
      </span>
    )
  }

  return (
    <span
      className="grid h-9 w-9 place-items-center rounded-xl p-1 shadow-sm ring-1 ring-black/5 bg-[#ffffff]"
      title="Company logo"
    >
      <img
        src="/logo.png"
        alt="Company logo"
        className="h-full w-full object-contain"
        onError={() => setFailed(true)}
      />
    </span>
  )
}

function AppShell() {
  const { user } = useAuth()
  const [tab, setTab] = useState('vocab')
  const [ocrText, setOcrText] = useState('привет мир')
  const [savedOcr, setSavedOcr] = useState('привет мир')
  const [ocrBusy, setOcrBusy] = useState(false)
  const [ocrError, setOcrError] = useState('')

  const tabs = [
    { id: 'vocab', label: 'Vocabulary', icon: '🔤', hint: 'Speak, snap or type Russian words' },
    { id: 'write', label: 'Write', icon: '✍️', hint: 'Translate & see cursive' },
    { id: 'learn', label: 'Learn', icon: '📚', hint: 'Alphabet, drills, cards' },
    { id: 'tools', label: 'Tools', icon: '🛠️', hint: 'OCR, tap-a-word, feedback' },
    { id: 'ai', label: 'AI', icon: '✨', hint: 'ChatGPT + Claude + Perplexity consensus' },
    { id: 'fonts', label: 'Font Test', icon: '🔤', hint: 'Compare cursive fonts' },
  ]

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="sticky top-0 z-50 border-b border-white/60 bg-white/70 backdrop-blur-xl dark:bg-slate-950/70 dark:border-slate-700/50 shadow-[0_1px_2px_rgb(15_23_42/0.04)]">
        <div className="max-w-7xl mx-auto px-4 md:px-6 h-16 flex items-center gap-3 md:gap-4">
          {/* Brand */}
          <div className="flex items-center gap-2.5 shrink-0 select-none">
            <BrandMark />
            <span className="hidden sm:block leading-tight">
              <span className="block text-sm font-bold tracking-tight text-gray-900 dark:text-gray-100">
                Cursive&nbsp;RU
              </span>
              <span className="block text-[11px] text-gray-500 dark:text-gray-400">
                reading &amp; writing assistant
              </span>
            </span>
          </div>

          {/* Segmented tabs */}
          <div
            className="flex-1 flex items-center gap-1 overflow-x-auto rounded-xl bg-gray-100/80 p-1 border border-gray-200/70 dark:bg-slate-900/70 dark:border-slate-700/60"
            role="tablist"
            aria-label="Sections"
          >
            {tabs.map((t) => {
              const active = tab === t.id
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  role="tab"
                  aria-selected={active}
                  aria-current={active ? 'page' : undefined}
                  title={t.hint}
                  className={`flex-1 min-w-max whitespace-nowrap rounded-lg px-3 md:px-4 py-1.5 text-sm font-medium flex items-center justify-center gap-1.5 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
                    active
                      ? 'bg-white text-blue-700 shadow-sm border border-white dark:bg-slate-700 dark:text-blue-300 dark:border-slate-600'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-white/60 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <span aria-hidden="true">{t.icon}</span>
                  <span>{t.label}</span>
                </button>
              )
            })}
          </div>

          <UserButton className="shrink-0" />
          <ThemeToggle className="shrink-0" />
        </div>
      </nav>

      <main className="flex-1 pb-12">
        <AccountNotices />

        {tab === 'vocab' && <VocabularyPage />}

        {tab === 'write' && <WritingPage />}

        {tab === 'learn' && (
          <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8 animate-fade-in">
            <header className="text-center space-y-2 pt-2">
              <p className="eyebrow">Study zone</p>
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                Learn the alphabet &amp; trap letters
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                Block print beside cursive, flashcards, and drills for the letters that
                look like Latin characters.
              </p>
            </header>
            <AlphabetChart />
            <TrapLetterDrills />
            <Flashcards />
            <PracticeSheet text="привет друг" />
          </div>
        )}

        {tab === 'tools' && (
          <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8 animate-fade-in">
            <header className="text-center space-y-2 pt-2">
              <p className="eyebrow">Toolkit</p>
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                Read, check &amp; improve
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                Turn a photo into text, review it line by line, then tap any word or
                send feedback.
              </p>
            </header>

            <div className="card">
              <div className="card-header">
                <p className="eyebrow">Image → text</p>
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mt-0.5">
                  Read text from an image
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Upload a photo or take one with the camera. The recognised Russian text
                  appears below so you can correct it before it is used.
                </p>
              </div>
              <div className="card-body space-y-3">
                <ImageInput
                  onTextExtracted={setOcrText}
                  onError={setOcrError}
                  onLoading={setOcrBusy}
                />
                {ocrBusy && (
                  <p className="text-sm text-blue-600 dark:text-blue-300 animate-soft-pulse flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-blue-500" aria-hidden="true" />
                    Reading the image…
                  </p>
                )}
                {ocrError && (
                  <p className="text-sm text-red-700 dark:text-red-300" role="alert">{ocrError}</p>
                )}
              </div>
            </div>

            <TapWordView text={savedOcr} />
            <EditableOCRScreen initialText={ocrText} onSave={setSavedOcr} />
            <FeedbackForm />
          </div>
        )}

        {tab === 'ai' && <AiStudio />}

        {tab === 'fonts' && (
          <div className="max-w-7xl mx-auto p-4 md:p-8 animate-fade-in">
            <header className="text-center space-y-2 pt-2 pb-6">
              <p className="eyebrow">Typography</p>
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                Cursive font comparison
              </h2>
            </header>
            <FontTest />
          </div>
        )}
      </main>

      <footer className="no-print py-6 text-center text-xs text-gray-500 dark:text-gray-500 border-t border-gray-200/70 dark:border-slate-800 space-y-2">
        <p className="sr-only">Signed in as {user?.email}</p>
        <div className="flex items-center justify-center gap-2">
          <img
            src="/logo.png"
            alt="Company logo"
            className="h-6 w-6 object-contain"
            onError={(e) => { e.currentTarget.style.display = 'none' }}
          />
          <span className="font-medium text-gray-600 dark:text-gray-400">
            Built by the team behind Cursive&nbsp;RU
          </span>
        </div>
        <p>
          Cursive&nbsp;RU — two-stage translation (Opus&nbsp;MT) by default · optional AI
          runs only when the server has provider keys
        </p>
      </footer>
    </div>
  )
}

/** Session-backed banner: verification prompt plus one-time notices. */
function AccountNotices() {
  const { user, notice, setNotice, resendVerification } = useAuth()
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState('')

  if (!user) return null

  async function handleResend() {
    setBusy(true)
    setSent('')
    try {
      const result = await resendVerification()
      setSent(
        result?.already_verified
          ? 'Your e-mail is already confirmed.'
          : result?.email_sent
            ? 'Confirmation e-mail sent — check your inbox.'
            : 'Link created, but e-mail delivery is not configured on this server.',
      )
    } catch (err) {
      setSent(err?.message || 'Could not send the confirmation e-mail.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-6 pt-4 space-y-2">
      {notice && (
        <Notice type={notice.type} onDismiss={() => setNotice(null)}>
          {notice.message}
        </Notice>
      )}
      {!user.email_verified && (
        <div className="flex flex-col gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 sm:flex-row sm:items-center sm:justify-between dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200">
          <span>
            Confirm your e-mail address to secure your account. Signed in as{' '}
            <span className="font-medium">{user.email}</span>.
            {sent && <span className="block text-xs opacity-80">{sent}</span>}
          </span>
          <button
            type="button"
            onClick={handleResend}
            disabled={busy}
            className="btn-secondary shrink-0 !py-2 text-xs"
          >
            {busy ? 'Sending…' : 'Resend link'}
          </button>
        </div>
      )}
    </div>
  )
}

function Splash() {
  return (
    <div className="min-h-screen grid place-items-center px-6">
      <div className="flex flex-col items-center gap-3 text-center">
        <span className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-2xl font-bold text-white shadow-lg shadow-blue-600/30">
          я
        </span>
        <span
          className="h-5 w-5 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600"
          aria-hidden="true"
        />
        <p className="text-sm text-gray-600 dark:text-gray-400" role="status">
          Checking your session…
        </p>
      </div>
    </div>
  )
}

/** Server-checked gate: no app UI is rendered until /auth/me answers. */
function AuthGate() {
  const { user, loading } = useAuth()
  const path =
    typeof window !== 'undefined' ? window.location.pathname.replace(/\/+$/, '') : ''

  if (path === '/reset-password') return <ResetPasswordPage />
  if (loading) return <Splash />
  if (!user) return <AuthPage />
  return <AppShell />
}

export default function App() {
  return (
    <AuthProvider>
      <AuthGate />
    </AuthProvider>
  )
}
