import React from 'react'
import { speakText } from '../lib/speech'

/**
 * One analysed Russian word, presented exactly in the learning format:
 *
 *   Russian Word / Pronunciation / English Meaning / Sinhala Meaning /
 *   Part of Speech / Grammar Explanation / two example sentences with
 *   English and Sinhala translations.
 */

const POS_LABELS = {
  verb: 'Verb',
  noun: 'Noun',
  adjective: 'Adjective',
  adverb: 'Adverb',
  pronoun: 'Pronoun',
  preposition: 'Preposition',
  numeral: 'Numeral',
  conjunction: 'Conjunction',
  particle: 'Particle',
  interjection: 'Interjection',
  other: 'Other',
}

// Soft colour per part of speech so word types are visually distinguishable.
const POS_STYLES = {
  verb: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800',
  noun: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-800',
  adjective: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/60 dark:text-purple-300 dark:border-purple-800',
  adverb: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800',
  pronoun: 'bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950/60 dark:text-cyan-300 dark:border-cyan-800',
  preposition: 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800',
}

const VocabCard = ({ entry, index }) => {
  if (!entry || !entry.word) return null
  const pos = entry.part_of_speech || 'other'
  const posLabel = POS_LABELS[pos] || 'Other'
  const posStyle = POS_STYLES[pos] || POS_STYLES.other
  const examples = Array.isArray(entry.examples) ? entry.examples.slice(0, 2) : []

  return (
    <article className="card overflow-hidden">
      <div className="card-body space-y-3">
        {/* Russian word + listen button */}
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="text-2xl font-bold text-gray-900 dark:text-gray-100 leading-tight">
            <span className="text-blue-600/90 dark:text-blue-400/90 text-sm font-semibold uppercase tracking-wide mr-2">
              {index}. Russian word:
            </span>
            {entry.word}
          </h4>
          {entry.occurrences > 1 && (
            <span className="pill border border-gray-200 bg-gray-50 text-gray-600 dark:bg-slate-800 dark:text-gray-300 dark:border-slate-700">
              appears {entry.occurrences}×
            </span>
          )}
          {entry.lemma && entry.lemma.toLowerCase() !== entry.word.toLowerCase() && (
            <span className="pill border border-gray-200 bg-gray-50 text-gray-600 dark:bg-slate-800 dark:text-gray-300 dark:border-slate-700">
              dictionary form: {entry.lemma}
            </span>
          )}
          <button
            type="button"
            onClick={() => speakText(entry.word, 'ru')}
            title="Listen"
            aria-label={`Listen to ${entry.word}`}
            className="btn-ghost btn-sm"
          >
            🔊
          </button>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400">
          <span className="font-semibold text-gray-800 dark:text-gray-200">Pronunciation:</span>{' '}
          {entry.pronunciation || '—'}
        </p>

        <p className="text-sm">
          <span className="font-semibold text-gray-800 dark:text-gray-200">English meaning:</span>{' '}
          <span className="text-gray-700 dark:text-gray-300">{entry.english || '—'}</span>
        </p>

        <p className="text-sm" lang="si">
          <span className="font-semibold text-gray-800 dark:text-gray-200">Sinhala meaning:</span>{' '}
          <span className="text-gray-700 dark:text-gray-300">{entry.sinhala || '—'}</span>
        </p>

        {/* Part of speech */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">Part of speech:</span>
          <span className={`pill border ${posStyle}`}>
            {posLabel}
            {entry.pos_sinhala ? ` (${entry.pos_sinhala})` : ''}
          </span>
        </div>

        {/* Grammar explanation */}
        {entry.grammar && (
          <div className="rounded-xl bg-gray-50/80 border border-gray-100 p-3 dark:bg-slate-800/50 dark:border-slate-700/70">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-gray-500 dark:text-gray-400 mb-1">
              Grammar explanation
            </p>
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
              {entry.grammar}
            </p>
            {entry.grammar_sinhala && (
              <p
                lang="si"
                className="mt-1.5 text-sm text-gray-600 dark:text-gray-400 leading-relaxed"
              >
                {entry.grammar_sinhala}
              </p>
            )}
          </div>
        )}

        {/* Example sentences */}
        {examples.length > 0 && (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-gray-500 dark:text-gray-400 mb-2">
              Example sentences
            </p>
            <ol className="space-y-3">
              {examples.map((ex, i) => (
                <li key={`${entry.word}-ex-${i}`} className="flex gap-2.5">
                  <span
                    className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-blue-100 text-xs font-bold text-blue-700 dark:bg-blue-950/70 dark:text-blue-300"
                    aria-hidden="true"
                  >
                    {i + 1}
                  </span>
                  <div className="min-w-0 space-y-0.5">
                    <p className="text-base font-medium text-gray-900 dark:text-gray-100 leading-snug">
                      {ex.ru}
                      {ex.ru && (
                        <button
                          type="button"
                          onClick={() => speakText(ex.ru, 'ru')}
                          title="Listen"
                          aria-label={`Listen to ${ex.ru}`}
                          className="btn-ghost btn-sm !px-1.5 !py-0.5 ml-1 align-middle"
                        >
                          🔊
                        </button>
                      )}
                    </p>
                    {ex.en && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        <span className="font-semibold text-gray-700 dark:text-gray-300">English:</span>{' '}
                        {ex.en}
                      </p>
                    )}
                    {ex.si && (
                      <p className="text-sm text-gray-600 dark:text-gray-400" lang="si">
                        <span className="font-semibold text-gray-700 dark:text-gray-300">Sinhala:</span>{' '}
                        {ex.si}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </article>
  )
}

export default VocabCard
