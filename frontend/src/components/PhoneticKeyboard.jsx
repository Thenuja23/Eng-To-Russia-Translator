import React from 'react'

const PhoneticKeyboard = ({ onKeyPress }) => {
  const rows = [
    ['a', 'b', 'v', 'g', 'd', 'e', 'zh', 'z', 'i', 'y', 'k', 'l'],
    ['m', 'n', 'o', 'p', 'r', 's', 't', 'u', 'f', 'h', 'ts', 'ch'],
    ['sh', 'shch', 'kh', 'yo', 'yu', 'ya', "'", '"'],
  ]

  const handleKey = (key) => {
    if (!onKeyPress || !key) return
    onKeyPress(key)
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-semibold text-gray-800">Latin-Phonetic Keys</h3>
      </div>
      <div className="card-body space-y-2">
        {rows.map((row, idx) => (
          <div key={idx} className="flex gap-1 justify-center flex-wrap">
            {row.map((key, kidx) => (
              <button
                key={kidx}
                onClick={() => handleKey(key)}
                className="px-2 py-1.5 bg-gradient-to-r from-purple-50 to-blue-50 hover:from-purple-100 hover:to-blue-100 border border-gray-200 rounded-lg text-xs font-medium transition-colors duration-150 min-w-[38px] shadow-sm"
                type="button"
                disabled={!key}
              >
                {key}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export default PhoneticKeyboard
