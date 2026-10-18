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
        <h3 className="text-lg font-semibold text-gray-800">Russian Keyboard</h3>
      </div>
      <div className="card-body space-y-2">
        {rows.map((row, idx) => (
          <div key={idx} className="flex gap-1 justify-center flex-wrap">
            {row.map((key, kidx) => (
              <button
                key={kidx}
                onClick={() => handleKey(key)}
                className="px-2 py-2 bg-white hover:bg-blue-50 border border-gray-200 rounded-lg text-sm font-medium transition-colors duration-150 min-w-[32px] shadow-sm"
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
