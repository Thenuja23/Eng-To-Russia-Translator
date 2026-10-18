import React, { useState } from 'react'
import CopyButton from './CopyButton'

const TapWordView = ({ text = '', words = [] }) => {
  const [selected, setSelected] = useState(null)
  const wordList = words.length > 0 ? words : text.split(/\s+/).filter(Boolean)

  return (
    <section className="card">
      <div className="card-header flex items-baseline justify-between gap-3">
        <div>
          <p className="eyebrow">Reader</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            Tap-a-word view
          </h3>
        </div>
        <span className="pill bg-blue-50 text-blue-700 border border-blue-100 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-900">
          {wordList.length} {wordList.length === 1 ? 'word' : 'words'}
        </span>
      </div>
      <div className="card-body space-y-4">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Tap any word to inspect it.
        </p>
        <div className="flex flex-wrap gap-2">
          {wordList.length === 0 && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              No text yet — save an edited OCR result above.
            </p>
          )}
          {wordList.map((w, idx) => {
            const active = selected && selected.idx === idx
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setSelected({ word: w, idx })}
                aria-pressed={active}
                className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
                  active
                    ? 'bg-blue-600 border-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'bg-white/90 border-gray-200 text-gray-800 hover:bg-blue-50 hover:border-blue-300 hover:-translate-y-px dark:bg-slate-800 dark:border-slate-700 dark:text-gray-200 dark:hover:bg-slate-700 dark:hover:border-blue-500/60'
                }`}
                lang="ru"
              >
                {w}
              </button>
            )
          })}
        </div>

        {selected && (
          <div className="rounded-xl border border-gray-200/90 dark:border-slate-700 bg-gray-50/80 dark:bg-slate-800/60 p-4 animate-fade-in">
            <div className="flex items-center justify-between gap-3 mb-3">
              <span
                className="text-2xl font-semibold text-gray-900 dark:text-gray-100"
                lang="ru"
              >
                {selected.word}
              </span>
              <CopyButton text={selected.word} label="Copy word" />
            </div>
            <dl className="text-sm space-y-1.5 text-gray-600 dark:text-gray-300">
              <div className="flex gap-2">
                <dt className="font-medium text-gray-500 dark:text-gray-400 w-28 shrink-0">Block:</dt>
                <dd>{selected.word}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="font-medium text-gray-500 dark:text-gray-400 w-28 shrink-0">Sound:</dt>
                <dd className="text-gray-500">transliteration TBD</dd>
              </div>
              <div className="flex gap-2">
                <dt className="font-medium text-gray-500 dark:text-gray-400 w-28 shrink-0">Meaning:</dt>
                <dd className="text-gray-500">translation TBD</dd>
              </div>
            </dl>
          </div>
        )}
      </div>
    </section>
  )
}

export default TapWordView
