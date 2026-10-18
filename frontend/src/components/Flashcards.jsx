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
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Flashcards (SRS v1)</h3>
      <div
        className="border-2 rounded-lg p-8 text-center min-h-[150px] cursor-pointer hover:bg-gray-50"
        onClick={() => setFlipped(!flipped)}
      >
        {!flipped ? (
          <div>
            <p className="text-3xl mb-2" lang="ru">{CARDS[idx].front}</p>
            <p className="text-sm text-gray-500">Click to flip</p>
          </div>
        ) : (
          <div>
            <p className="text-2xl mb-2">{CARDS[idx].back}</p>
            <p className="text-sm text-gray-500">Click to flip back</p>
          </div>
        )}
      </div>
      <div className="flex gap-2 justify-center mt-4">
        <button onClick={prev} className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300" type="button">Prev</button>
        <button onClick={next} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700" type="button">Next</button>
      </div>
      <div className="text-xs text-gray-500 mt-2 text-center">Card {idx + 1}/{CARDS.length}</div>
    </div>
  )
}

export default Flashcards
