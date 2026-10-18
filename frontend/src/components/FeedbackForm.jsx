import React, { useState } from 'react'
import { submitFeedback } from '../lib/api'

const CATEGORIES = [
  { id: 'general', label: 'General' },
  { id: 'bug', label: 'Bug' },
  { id: 'translation', label: 'Bad translation' },
  { id: 'ocr', label: 'OCR problem' },
  { id: 'idea', label: 'Idea' },
]

const FeedbackForm = () => {
  const [message, setMessage] = useState('')
  const [category, setCategory] = useState('general')
  const [consent, setConsent] = useState(false)
  const [status, setStatus] = useState(null) // null | 'sending' | 'sent' | 'error'
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (!message.trim()) {
      setStatus('error')
      setError('Please type a message first.')
      return
    }
    try {
      setStatus('sending')
      setError('')
      await submitFeedback({ message, category, consent_to_train: consent })
      setStatus('sent')
      setMessage('')
      setConsent(false)
    } catch (e) {
      setStatus('error')
      setError(e.message)
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <p className="eyebrow">Improve the app</p>
        <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
          Send feedback
        </h3>
      </div>
      <div className="card-body space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-gray-600 dark:text-gray-400" htmlFor="fb-category">
            Category
          </label>
          <select
            id="fb-category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="select-field !px-3 !py-1.5 !text-sm rounded-lg border border-gray-200/90 bg-white/90 shadow-sm dark:border-slate-700 dark:bg-slate-800/80"
          >
            {CATEGORIES.map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </select>
        </div>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="textarea-field !min-h-[90px]"
          placeholder="Report an issue, a bad translation, or suggest an idea…"
          aria-label="Feedback message"
        />
        <label className="flex items-start gap-2.5 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:bg-slate-800 dark:border-slate-600"
          />
          <span>I agree that my correction may be used to improve the models (optional)</span>
        </label>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSubmit}
            disabled={status === 'sending'}
            className="btn-primary"
            type="button"
          >
            {status === 'sending' ? 'Sending…' : 'Send feedback'}
          </button>
          <span aria-live="polite" className="text-sm">
            {status === 'sent' && (
              <span className="text-green-700 dark:text-green-400 font-medium">
                ✓ Thank you — feedback received.
              </span>
            )}
            {status === 'error' && <span className="text-red-600 dark:text-red-400">{error}</span>}
          </span>
        </div>
      </div>
    </section>
  )
}

export default FeedbackForm
