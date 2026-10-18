import React, { useState } from 'react'

const CARDS = [
  { front: 'привет', back: 'hello' },
  { front: 'мир', back: 'world' },
  { front: 'спасибо', back: 'thank you' },
  { front: 'пожалуйста', back: 'please' },
]

const Flashcards = () => {
  const [idx, setIdx] = useState(0)
  const [flipped, setFlipped] = useState(false)

  const next = () => {
    setIdx((prev) => (prev + 1) % CARDS.length)
    setFlipped(false)
  }

  const prev = () => {
    setIdx((prev) => (prev - 1 + CARDS.length) % CARDS.length)
    setFlipped(false)
  }

  return (
    <section className="card">
      <div className="card-header flex items-baseline justify-between gap-3">
        <div>
          <p className="eyebrow">Memorise</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            Flashcards
          </h3>
        </div>
        <span className="pill bg-blue-50 text-blue-700 border border-blue-100 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-900">
          {idx + 1} / {CARDS.length}
        </span>
      </div>
      <div className="card-body space-y-4">
        <button
          type="button"
          onClick={() => setFlipped(!flipped)}
          aria-label={flipped ? 'Show Russian word' : 'Show translation'}
          className="w-full min-h-[170px] rounded-2xl border border-dashed border-blue-200 dark:border-blue-900/70
                     bg-gradient-to-br from-blue-50/80 via-white to-indigo-50/70
                     dark:from-slate-800 dark:via-slate-800 dark:to-indigo-950/40
                     p-8 flex flex-col items-center justify-center gap-2 transition-all duration-300
                     hover:shadow-lg hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          {!flipped ? (
            <>
              <p className="text-4xl font-medium text-gray-900 dark:text-gray-100" lang="ru">
                {CARDS[idx].front}
              </p>
              <p className="text-xs uppercase tracking-widest text-gray-500 mt-2">
                tap to reveal
              </p>
            </>
          ) : (
            <>
              <p className="text-3xl font-medium text-blue-700 dark:text-blue-300">
                {CARDS[idx].back}
              </p>
              <p className="text-xs uppercase tracking-widest text-gray-500 mt-2">
                tap to flip back
              </p>
            </>
          )}
        </button>

        <div className="flex gap-2 justify-center">
          <button onClick={prev} className="btn-secondary btn-sm" type="button">
            ← Prev
          </button>
          <button onClick={next} className="btn-primary btn-sm" type="button">
            Next →
          </button>
        </div>
      </div>
    </section>
  )
}

export default Flashcards
