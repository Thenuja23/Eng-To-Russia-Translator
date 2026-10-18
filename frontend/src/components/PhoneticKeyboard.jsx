import React from 'react'

const PhoneticKeyboard = ({ onKeyPress }) => {
  const rows = [
    ['a', 'b', 'v', 'g', 'd', 'e', 'zh', 'z', 'i', 'y', 'k', 'l'],
    ['m', 'n', 'o', 'p', 'r', 's', 't', 'u', 'f', 'h', 'ts', 'ch'],
    ['sh', 'shch', 'kh', 'yo', 'yu', 'ya', "'", '"'],
    ['space', 'BACKSPACE'],
  ]

  const handleKey = (key) => {
    if (!onKeyPress || !key) return
    if (key === 'space') onKeyPress(' ')
    else onKeyPress(key)
  }

  const LABELS = { space: '␣ space', BACKSPACE: '⌫ back' }

  return (
    <div className="card">
      <div className="card-header">
        <p className="eyebrow">Input helper</p>
        <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
          Latin-phonetic keys
        </h3>
      </div>
      <div className="card-body space-y-2">
        {rows.map((row, idx) => (
          <div key={idx} className="flex gap-1.5 justify-center flex-wrap">
            {row.map((key, kidx) => (
              <button
                key={kidx}
                onClick={() => handleKey(key)}
                aria-label={key}
                className="key key-accent"
                type="button"
                disabled={!key}
              >
                {LABELS[key] || key}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export default PhoneticKeyboard
