import React, { useState } from 'react'
import CopyButton from './CopyButton'

const TapWordView = ({ text = '', words = [] }) => {
  const [selected, setSelected] = useState(null)
  const wordList = words.length > 0 ? words : text.split(/\s+/).filter(Boolean)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Tap-a-Word View</h3>
      <div className="flex flex-wrap gap-2 mb-4">
        {wordList.map((w, idx) => (
          <span
            key={idx}
            onClick={() => setSelected({ word: w, idx })}
            className="px-2 py-1 bg-gray-100 hover:bg-blue-100 rounded cursor-pointer border"
            lang="ru"
          >
            {w}
          </span>
        ))}
      </div>
      {selected && (
        <div className="border rounded p-4 bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold" lang="ru">{selected.word}</span>
            <CopyButton text={selected.word} label="Copy word" />
          </div>
          <div className="text-sm text-gray-600 space-y-1">
            <div><span className="font-medium">Block:</span> {selected.word}</div>
            <div><span className="font-medium">Pronunciation:</span> (transliteration TBD)</div>
            <div><span className="font-medium">Translation:</span> (translation TBD)</div>
          </div>
        </div>
      )}
      <p className="text-xs text-gray-500 mt-2">Per spec: block version, pronunciation, translation per word</p>
    </div>
  )
}

export default TapWordView
