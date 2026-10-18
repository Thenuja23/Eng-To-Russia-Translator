import React from 'react'

const ALPHABET = [
  { upper: 'А', lower: 'а', hint: 'a' }, { upper: 'Б', lower: 'б', hint: 'b' },
  { upper: 'В', lower: 'в', hint: 'v' }, { upper: 'Г', lower: 'г', hint: 'g' },
  { upper: 'Д', lower: 'д', hint: 'd' }, { upper: 'Е', lower: 'е', hint: 'ye' },
  { upper: 'Ё', lower: 'ё', hint: 'yo' }, { upper: 'Ж', lower: 'ж', hint: 'zh' },
  { upper: 'З', lower: 'з', hint: 'z' }, { upper: 'И', lower: 'и', hint: 'i' },
  { upper: 'Й', lower: 'й', hint: 'y' }, { upper: 'К', lower: 'к', hint: 'k' },
  { upper: 'Л', lower: 'л', hint: 'l' }, { upper: 'М', lower: 'м', hint: 'm' },
  { upper: 'Н', lower: 'н', hint: 'n' }, { upper: 'О', lower: 'о', hint: 'o' },
  { upper: 'П', lower: 'п', hint: 'p' }, { upper: 'Р', lower: 'р', hint: 'r' },
  { upper: 'С', lower: 'с', hint: 's' }, { upper: 'Т', lower: 'т', hint: 't' },
  { upper: 'У', lower: 'у', hint: 'u' }, { upper: 'Ф', lower: 'ф', hint: 'f' },
  { upper: 'Х', lower: 'х', hint: 'kh' }, { upper: 'Ц', lower: 'ц', hint: 'ts' },
  { upper: 'Ч', lower: 'ч', hint: 'ch' }, { upper: 'Ш', lower: 'ш', hint: 'sh' },
  { upper: 'Щ', lower: 'щ', hint: 'shch' }, { upper: 'Ъ', lower: 'ъ', hint: '—' },
  { upper: 'Ы', lower: 'ы', hint: 'y' }, { upper: 'Ь', lower: 'ь', hint: '—' },
  { upper: 'Э', lower: 'э', hint: 'e' }, { upper: 'Ю', lower: 'ю', hint: 'yu' },
  { upper: 'Я', lower: 'я', hint: 'ya' },
]

const AlphabetChart = () => {
  return (
    <section className="card">
      <div className="card-header flex items-baseline justify-between gap-3">
        <div>
          <p className="eyebrow">Reference</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            Alphabet chart
          </h3>
        </div>
        <span className="pill bg-indigo-50 text-indigo-700 border border-indigo-100 dark:bg-indigo-950/60 dark:text-indigo-300 dark:border-indigo-900">
          33 letters
        </span>
      </div>
      <div className="card-body">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Block print beside its cursive form, with an approximate Latin sound.
        </p>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2.5">
          {ALPHABET.map((letter, idx) => (
            <button
              key={idx}
              type="button"
              title={`${letter.upper} ${letter.lower} ≈ "${letter.hint}"`}
              className="group rounded-xl border border-gray-200/90 dark:border-slate-700 bg-white/80 dark:bg-slate-800/70 p-2.5 text-center transition-all duration-200 hover:-translate-y-0.5 hover:border-blue-300 dark:hover:border-blue-500/60 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <div className="text-lg font-bold leading-none text-gray-800 dark:text-gray-100">
                {letter.upper} {letter.lower}
              </div>
              <div
                lang="ru"
                className="font-['Bad_Script'] text-xl mt-1.5 leading-none text-blue-700 dark:text-blue-300"
              >
                {letter.upper} {letter.lower}
              </div>
              <div className="text-[10px] uppercase tracking-wider text-gray-500 mt-1.5">
                {letter.hint}
              </div>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}

export default AlphabetChart
