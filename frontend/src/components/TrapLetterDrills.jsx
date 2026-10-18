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

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Trap-Letter Drills</h3>
      <div className="border rounded p-4">
        <p className="text-sm text-gray-600 mb-2">{TRAPS[current].desc}</p>
        <div className="flex gap-4 text-3xl justify-center my-4">
          <span>{TRAPS[current].letters[0]}</span>
          <span className="text-gray-400">vs</span>
          <span>{TRAPS[current].letters[1]}</span>
        </div>
        <div lang="ru" className="font-['Bad_Script'] text-3xl text-center my-4">
          {TRAPS[current].letters[0]}
        </div>
        <div className="flex gap-2 justify-center">
          <button
            onClick={() => setCurrent((prev) => (prev - 1 + TRAPS.length) % TRAPS.length)}
            className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
            type="button"
          >
            Previous
          </button>
          <button
            onClick={() => setCurrent((prev) => (prev + 1) % TRAPS.length)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            type="button"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}

export default TrapLetterDrills
