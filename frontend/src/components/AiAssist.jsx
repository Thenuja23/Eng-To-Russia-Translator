import React, { useEffect, useState } from 'react'
import { aiEnhance, aiExplain, aiStatus } from '../lib/api'

const PROVIDER_NAMES = {
  openai: 'ChatGPT',
  anthropic: 'Claude',
  perplexity: 'Perplexity',
}

/**
 * Compact "AI check" card for a translation result.
 *
 * It renders nothing at all when no provider key is configured, so the core
 * offline experience is never cluttered by unavailable features.
 */
export default function AiAssist({
  source,
  translation,
  src = 'en',
  tgt = 'ru',
  onUse,
}) {
  const [status, setStatus] = useState(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [suggestion, setSuggestion] = useState(null)
  const [explanation, setExplanation] = useState(null)

  useEffect(() => {
    let alive = true
    aiStatus()
      .then((s) => alive && setStatus(s))
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [])

  // A stale suggestion must never be applied to new text.
  useEffect(() => {
    setSuggestion(null)
    setError('')
  }, [source, translation])

  const configured = status?.configured || 0
  if (!configured) return null

  const runReview = async () => {
    setBusy('review')
    setError('')
    try {
      setSuggestion(await aiEnhance(source, translation, src, tgt))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy('')
    }
  }

  const runExplain = async () => {
    setBusy('explain')
    setError('')
    try {
      setExplanation(
        await aiExplain({
          text: source,
          translation: translation || '',
          srcLang: src,
          tgtLang: tgt,
        }),
      )
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy('')
    }
  }

  return (
    <section className="card border-dashed">
      <div className="card-header flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow">Optional AI</p>
          <h3 className="text-base font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            Check &amp; explain this translation
          </h3>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {(status.providers || [])
            .filter((p) => p.configured)
            .map((p) => (
              <span
                key={p.name}
                className="pill bg-white text-gray-600 border border-gray-200 dark:bg-slate-800 dark:text-gray-300 dark:border-slate-700"
              >
                {PROVIDER_NAMES[p.name] || p.name}
              </span>
            ))}
        </div>
      </div>
      <div className="card-body space-y-3">
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className="btn-primary btn-sm"
            onClick={runReview}
            disabled={Boolean(busy) || !source?.trim() || !translation?.trim()}
          >
            {busy === 'review' ? 'Reviewing…' : '✨ Review translation'}
          </button>
          <button
            type="button"
            className="btn-ghost btn-sm"
            onClick={runExplain}
            disabled={Boolean(busy) || !source?.trim()}
          >
            {busy === 'explain' ? 'Explaining…' : '🎓 Explain'}
          </button>
        </div>

        {error && (
          <p className="text-sm text-red-700 dark:text-red-300" role="alert">
            {error}
          </p>
        )}

        {suggestion && (
          <div
            className="rounded-xl border border-blue-200 bg-blue-50/60 p-3 space-y-2 dark:border-blue-900 dark:bg-blue-950/30"
            aria-live="polite"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="pill bg-white text-blue-700 border border-blue-200 dark:bg-slate-900 dark:text-blue-300 dark:border-blue-900">
                {PROVIDER_NAMES[suggestion.provider] || suggestion.provider}
              </span>
              <span className="pill bg-white text-gray-600 border border-gray-200 dark:bg-slate-900 dark:text-gray-300 dark:border-slate-700">
                agreement {Math.round((suggestion.agreement || 0) * 100)}%
              </span>
              <span
                className={`pill border ${
                  suggestion.tokens_preserved
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900'
                    : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900'
                }`}
              >
                {suggestion.tokens_preserved ? '✓ tokens intact' : '✕ token lost'}
              </span>
            </div>
            <p className="text-lg font-medium break-words text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
              {suggestion.improved_text}
            </p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="btn-primary btn-sm"
                onClick={() => {
                  onUse?.(suggestion.improved_text)
                  setSuggestion(null)
                }}
              >
                Use this
              </button>
              <button
                type="button"
                className="btn-ghost btn-sm"
                onClick={() => setSuggestion(null)}
              >
                Keep current
              </button>
            </div>
          </div>
        )}

        {explanation && (
          <div
            className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-3 space-y-2 dark:border-indigo-900 dark:bg-indigo-950/30"
            aria-live="polite"
          >
            <span className="pill bg-white text-indigo-700 border border-indigo-200 dark:bg-slate-900 dark:text-indigo-300 dark:border-indigo-900">
              {PROVIDER_NAMES[explanation.provider] || explanation.provider}
            </span>
            <p className="text-sm leading-relaxed whitespace-pre-wrap text-gray-800 dark:text-gray-200">
              {explanation.explanation}
            </p>
            <button
              type="button"
              className="btn-ghost btn-sm"
              onClick={() => setExplanation(null)}
            >
              Hide
            </button>
          </div>
        )}
      </div>
    </section>
  )
}
