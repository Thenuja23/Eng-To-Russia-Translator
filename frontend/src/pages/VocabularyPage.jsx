import React, { useState } from 'react'
import VoiceInput from '../components/VoiceInput'
import ImageInput from '../components/ImageInput'
import VocabCard from '../components/VocabCard'
import { analyzeVocab } from '../lib/api'

/**
 * Russian Vocabulary Learning Assistant.
 *
 * The learner supplies Russian in any of three ways:
 *   1. speaking (microphone → Russian speech recognition),
 *   2. a picture (camera/upload → backend OCR),
 *   3. typing.
 *
 * The text is analysed word by word. Every card shows the Russian word, a
 * pronunciation guide, the English meaning with the Sinhala meaning directly
 * underneath, the part of speech in English and Sinhala, a beginner-friendly
 * grammar explanation, and two example sentences with English and Sinhala
 * translations.
 */

const EXAMPLES = [
  'Это красивый дом.',
  'Я хочу выучить русский язык.',
  'Привет! Как дела?',
]

const countWords = (value) =>
  (value.match(/[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*/g) || []).length

export default function VocabularyPage() {
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [ocrBusy, setOcrBusy] = useState(false)

  const appendText = (recognised) => {
    setError('')
    setText((prev) => (prev.trim() ? `${prev.trim()} ${recognised}` : recognised))
  }

  const analyze = async () => {
    const source = text.trim()
    if (!source) {
      setError('Type, speak or upload some Russian words first.')
      return
    }
    setError('')
    setBusy(true)
    try {
      const data = await analyzeVocab(source)
      setResult(data)
      if (!data.words || data.words.length === 0) {
        setError('No Russian words were found in that text.')
      }
    } catch (e) {
      setResult(null)
      setError(e.message || 'Analysis failed. Is the backend running?')
    } finally {
      setBusy(false)
    }
  }

  const clearAll = () => {
    setText('')
    setResult(null)
    setError('')
  }

  const words = result?.words || []
  const stats = result?.stats || null

  return (
    <div className="max-w-3xl mx-auto p-4 md:p-8 space-y-6 animate-fade-in">
      <header className="text-center space-y-2 pt-2">
        <p className="eyebrow">Vocabulary</p>
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Russian word-by-word assistant
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 max-w-xl mx-auto">
          Speak, photograph or type Russian. Every word is explained with
          pronunciation, English and{' '}
          <span lang="si">සිංහල</span> meanings, grammar, and two example
          sentences translated into both languages.
        </p>
      </header>

      {/* ------------------------------------------------------------- input */}
      <section className="card">
        <div className="card-header">
          <p className="eyebrow">Input</p>
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mt-0.5">
            Add Russian words
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Use the microphone, a photo of Russian text, or your keyboard. All
            three fill the same box, so you can mix them.
          </p>
        </div>
        <div className="card-body space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <VoiceInput onText={appendText} onError={setError} />
            <ImageInput
              onTextExtracted={(recognised) => {
                setError('')
                setText(recognised)
              }}
              onError={setError}
              onLoading={setOcrBusy}
            />
            {ocrBusy && (
              <span className="text-sm text-blue-600 dark:text-blue-300 animate-soft-pulse">
                Reading the picture…
              </span>
            )}
          </div>

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
              lang="ru"
              dir="auto"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="mt-1 flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {text.trim()
                  ? `${countWords(text)} Russian word(s) ready to analyse.`
                  : 'Type words here, or speak / upload a picture to fill this box.'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400" lang="si">
                සෑම වචනයකටම තේරුම, උච්චාරණය සහ උදාහරණ දෙකක් ලැබේ.
              </p>
            </div>
          </div>

          {!text.trim() && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                Try:
              </span>
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setText(example)}
                  className="pill border border-gray-200 bg-white text-gray-700 hover:border-blue-300 hover:text-blue-700 dark:bg-slate-800 dark:text-gray-200 dark:border-slate-700"
                >
                  {example}
                </button>
              ))}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="btn-primary"
              onClick={analyze}
              disabled={busy || !text.trim()}
            >
              {busy ? 'Analysing…' : '🔍 Analyse words'}
            </button>
            {(text.trim() || words.length > 0) && (
              <button type="button" className="btn-ghost btn-sm" onClick={clearAll}>
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
        </div>
      </section>

      {/* ----------------------------------------------------------- results */}
      {words.length > 0 && (
        <section className="space-y-4" aria-live="polite">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="eyebrow">Word-by-word analysis</p>
            <div className="flex flex-wrap items-center gap-2">
              <span className="pill border border-blue-200 bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-900">
                {result.mode === 'ai' ? 'AI analysis' : 'Dictionary + grammar'}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {words.length} word(s) explained
              </span>
            </div>
          </div>

          {stats && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {stats.dictionary} from the built-in dictionary
              {stats.rule_based > 0 ? ` · ${stats.rule_based} analysed by grammar rules` : ''}
              {stats.online_meaning > 0 ? ` · ${stats.online_meaning} meaning(s) looked up online` : ''}
              {result.notice ? ` — ${result.notice}` : ''}
            </p>
          )}

          {words.map((entry, i) => (
            <VocabCard key={`${entry.word}-${i}`} entry={entry} index={i + 1} />
          ))}
        </section>
      )}
    </div>
  )
}
