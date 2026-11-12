import React, { useState } from 'react'
import VoiceInput from '../components/VoiceInput'
import ImageInput from '../components/ImageInput'
import VocabCard from '../components/VocabCard'
import { aiVocab } from '../lib/api'

/**
 * Vocabulary Learning Assistant.
 *
 * The learner supplies Russian words in any of three ways:
 *   1. speaking (microphone -> speech recognition),
 *   2. a picture (camera/upload -> backend OCR),
 *   3. typing.
 *
 * The collected text is then sent to the AI vocabulary endpoint, which returns
 * a word-by-word analysis that is rendered as learner-friendly cards with
 * English and Sinhala support.
 */

const VocabularyPage = () => {
  const [text, setText] = useState('')
  const [words, setWords] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [aiOffline, setAiOffline] = useState(false)

  const appendText = (recognized) => {
    setText((prev) => (prev.trim() ? `${prev.trim()} ${recognized}` : recognized))
  }

  const analyze = async () => {
    const source = text.trim()
    if (!source) {
      setError('Enter, speak or upload some Russian words first.')
      return
    }
    setError('')
    setBusy(true)
    try {
      const result = await aiVocab(source)
      setWords(result.words || [])
      if (!result.words || result.words.length === 0) {
        setError('No words could be analysed. Try adding a little more text.')
      }
    } catch (err) {
      setWords([])
      const message = err.message || 'Analysis failed.'
      if (/503/.test(message) || /not configured|disabled/i.test(message)) {
        setAiOffline(true)
        setError(message)
      } else {
        setError(message)
      }
    } finally {
      setBusy(false)
    }
  }



  return (
    <div className="max-w-3xl mx-auto p-4 md:p-8 space-y-6 animate-fade-in">
      <header className="text-center space-y-2 pt-2">
        <p className="eyebrow">Vocabulary</p>
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Russian vocabulary assistant
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 max-w-xl mx-auto">
          Speak, upload a picture or type Russian words. Every word is explained with
          pronunciation, English and Sinhala meanings, grammar and example sentences.
        </p>
      </header>

      {/* ------------------------------------------------------------- input */}
      <section className="card">
        <div className="card-header">
          <p className="eyebrow">Input</p>
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mt-0.5">
            Add Russian words
          </h3>
        </div>
        <div className="card-body space-y-4">
          {/* Voice + picture buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <VoiceInput onText={appendText} onError={setError} />
            <ImageInput
              onTextExtracted={setText}
              onError={setError}
              onLoading={() => {}}
            />
          </div>

          {/* Manual text entry / recognised speech / OCR result */}
          <div>
            <label
              htmlFor="vocab-text"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
            >
              Russian text
            </label>
            <textarea
              id="vocab-text"
              className="textarea-field"
              placeholder="Например: Это красивый дом."
              dir="auto"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {text.trim()
                ? `${text.trim().split(/\s+/).length} word(s) ready to analyse.`
                : 'Type words here, or speak / upload a picture to fill this box.'}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="btn-primary"
              onClick={analyze}
              disabled={busy || !text.trim()}
            >
              {busy ? 'Analysing…' : '🔍 Analyse words'}
            </button>
            {text.trim() && (
              <button
                type="button"
                className="btn-ghost btn-sm"
                onClick={() => {
                  setText('')
                  setWords([])
                  setError('')
                }}
              >
                Clear
              </button>
            )}
          </div>

          {busy && (
            <p
              className="text-sm text-blue-600 dark:text-blue-300 animate-soft-pulse flex items-center gap-2"
              role="status"
            >
              <span className="h-2 w-2 rounded-full bg-blue-500" aria-hidden="true" />
              Analysing every word — this can take a few seconds…
            </p>
          )}
          {error && (
            <p className="text-sm text-red-700 dark:text-red-300" role="alert">
              {error}
            </p>
          )}
          {aiOffline && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              The vocabulary analysis uses the optional AI providers. Add
              {' '}OPENAI_API_KEY, ANTHROPIC_API_KEY and/or PERPLEXITY_API_KEY to
              {' '}backend/.env, then restart the backend.
            </p>
          )}
        </div>
      </section>

      {/* ------------------------------------------------------------ results */}
      {words.length > 0 && (
        <section className="space-y-4" aria-live="polite">
          <div className="flex items-baseline justify-between">
            <p className="eyebrow">Word-by-word analysis</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {words.length} word(s) explained
            </p>
          </div>
          {words.map((entry, i) => (
            <VocabCard key={`${entry.word}-${i}`} entry={entry} index={i + 1} />
          ))}
        </section>
      )}
    </div>
  )
}

export default VocabularyPage
