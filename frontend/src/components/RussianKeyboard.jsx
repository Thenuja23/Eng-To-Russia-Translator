import React from 'react'

const RussianKeyboard = ({ onKeyPress }) => {
  const rows = [
    ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х', 'ъ'],
    ['ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э'],
    ['я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю'],
    [' ', '⌫'],
  ]

  const handleKey = (key) => {
    if (!onKeyPress) return
    if (key === '⌫') {
      onKeyPress('BACKSPACE')
      return
    }
    onKeyPress(key)
  }

  return (
    <div className="card">
      <div className="card-header">
        <p className="eyebrow">Input helper</p>
        <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
          Russian keyboard
        </h3>
      </div>
      <div className="card-body space-y-2">
        {rows.map((row, idx) => (
          <div key={idx} className="flex gap-1.5 justify-center flex-wrap">
            {row.map((key, kidx) => (
              <button
                key={kidx}
                onClick={() => handleKey(key)}
                className="key"
                type="button"
              >
                {key === ' ' ? 'Space' : key}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export default RussianKeyboard
