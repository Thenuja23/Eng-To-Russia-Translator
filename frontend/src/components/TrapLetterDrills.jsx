import React, { useState } from 'react'

const TRAPS = [
  { letters: ['т', 'm'], desc: 'т looks like m' },
  { letters: ['д', 'g'], desc: 'д looks like g' },
  { letters: ['и', 'u'], desc: 'и looks like u' },
  { letters: ['п', 'n'], desc: 'п looks like n' },
  { letters: ['г', 'r'], desc: 'г looks like r' },
  { letters: ['б', '6'], desc: 'б looks like 6' },
]

const TrapLetterDrills = () => {
  const [current, setCurrent] = useState(0)
  const trap = TRAPS[current]

  return (
    <section className="card">
      <div className="card-header flex items-baseline justify-between gap-3">
        <div>
          <p className="eyebrow">Drill</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            Trap-letter drills
          </h3>
        </div>
        <span className="pill bg-rose-50 text-rose-700 border border-rose-100 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-900">
          {current + 1} / {TRAPS.length}
        </span>
      </div>
      <div className="card-body space-y-4">
        <p className="text-sm text-gray-600 dark:text-gray-400 text-center">{trap.desc}</p>

        <div className="rounded-xl border border-gray-200/90 dark:border-slate-700 bg-gradient-to-b from-white to-gray-50/70 dark:from-slate-800/80 dark:to-slate-900/70 p-5">
          <div className="flex items-center justify-center gap-5 text-4xl font-semibold">
            <span className="text-gray-900 dark:text-gray-100">{trap.letters[0]}</span>
            <span className="text-xs font-medium uppercase tracking-widest text-gray-500">
              vs
            </span>
            <span className="text-gray-500">{trap.letters[1]}</span>
          </div>
          <div
            lang="ru"
            className="font-['Bad_Script'] text-4xl text-center my-5 text-blue-700 dark:text-blue-300"
          >
            {trap.letters[0]}
          </div>
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => setCurrent((prev) => (prev - 1 + TRAPS.length) % TRAPS.length)}
              className="btn-secondary btn-sm"
              type="button"
            >
              ← Previous
            </button>
            <button
              onClick={() => setCurrent((prev) => (prev + 1) % TRAPS.length)}
              className="btn-primary btn-sm"
              type="button"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}

export default TrapLetterDrills
