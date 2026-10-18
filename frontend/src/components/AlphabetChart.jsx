import React from 'react'

const ALPHABET = [
  { upper: 'А', lower: 'а' }, { upper: 'Б', lower: 'б' }, { upper: 'В', lower: 'в' },
  { upper: 'Г', lower: 'г' }, { upper: 'Д', lower: 'д' }, { upper: 'Е', lower: 'е' },
  { upper: 'Ё', lower: 'ё' }, { upper: 'Ж', lower: 'ж' }, { upper: 'З', lower: 'з' },
  { upper: 'И', lower: 'и' }, { upper: 'Й', lower: 'й' }, { upper: 'К', lower: 'к' },
  { upper: 'Л', lower: 'л' }, { upper: 'М', lower: 'м' }, { upper: 'Н', lower: 'н' },
  { upper: 'О', lower: 'о' }, { upper: 'П', lower: 'п' }, { upper: 'Р', lower: 'р' },
  { upper: 'С', lower: 'с' }, { upper: 'Т', lower: 'т' }, { upper: 'У', lower: 'у' },
  { upper: 'Ф', lower: 'ф' }, { upper: 'Х', lower: 'х' }, { upper: 'Ц', lower: 'ц' },
  { upper: 'Ч', lower: 'ч' }, { upper: 'Ш', lower: 'ш' }, { upper: 'Щ', lower: 'щ' },
  { upper: 'Ъ', lower: 'ъ' }, { upper: 'Ы', lower: 'ы' }, { upper: 'Ь', lower: 'ь' },
  { upper: 'Э', lower: 'э' }, { upper: 'Ю', lower: 'ю' }, { upper: 'Я', lower: 'я' },
]

const AlphabetChart = () => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Alphabet Chart (33 letters)</h3>
      <p className="text-sm text-gray-600 mb-4">Block beside cursive</p>
      <div className="grid grid-cols-4 md:grid-cols-6 gap-3">
        {ALPHABET.map((letter, idx) => (
          <div key={idx} className="border rounded p-2 text-center">
            <div className="text-lg font-bold">{letter.upper} {letter.lower}</div>
            <div lang="ru" className="font-['Bad_Script'] text-lg mt-1">{letter.upper} {letter.lower}</div>
            <div className="text-xs text-gray-500 mt-1">block / cursive</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AlphabetChart
