import React from 'react'

/**
 * FontTest - Tests cursive fonts on pangram and trap letters
 * Pangram: "Съешь же ещё этих мягких французских булок, да выпей чаю"
 * Trap letters: т, м, д, г, и, п, б, ш (as specified)
 */
const SAMPLES = [
  { label: 'Bad Script', cls: 'font-["Bad_Script"]' },
  { label: 'Marck Script', cls: 'font-["Marck_Script"]' },
  { label: 'Caveat', cls: 'font-["Caveat"]' },
  { label: 'Serif italic (fallback)', cls: 'italic font-serif' },
]

const FontTest = () => {
  const pangram = 'Съешь же ещё этих мягких французских булок, да выпей чаю'
  const trapLetters = 'т м д г и п б ш Т М Д Г И П Б Ш'

  return (
    <section className="card">
      <div className="card-header">
        <p className="eyebrow">Pangram &amp; trap letters</p>
        <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
          Font test
        </h3>
      </div>
      <div className="card-body space-y-4">
        {SAMPLES.map((s) => (
          <div
            key={s.label}
            className="rounded-xl border border-gray-200/90 dark:border-slate-700 p-4 bg-gradient-to-br from-white to-slate-50/70 dark:from-slate-800/80 dark:to-slate-900/60 transition-shadow hover:shadow-md"
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-blue-600/90 dark:text-blue-400 mb-2">
              {s.label}
            </p>
            <p
              lang="ru"
              className={`text-xl leading-relaxed break-words text-gray-900 dark:text-gray-100 ${s.cls}`}
            >
              {pangram}
              <br />
              {trapLetters}
            </p>
          </div>
        ))}

        <p className="text-xs text-gray-500 dark:text-gray-400">
          Fonts that look like italic print are rejected. Cursive is a font — copied text
          stays normal Cyrillic.
        </p>
      </div>
    </section>
  )
}

export default FontTest
