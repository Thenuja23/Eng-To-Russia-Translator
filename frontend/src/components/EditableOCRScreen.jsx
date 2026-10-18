import React, { useState } from 'react'

const EditableOCRScreen = ({ initialText = '', onSave }) => {
  const [text, setText] = useState(initialText)
  const [lines, setLines] = useState(initialText.split('\n'))

  const handleLineChange = (idx, value) => {
    const newLines = [...lines]
    newLines[idx] = value
    setLines(newLines)
    setText(newLines.join('\n'))
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Editable OCR Results</h3>
      <p className="text-sm text-gray-600 mb-4">Edit recognized text line by line</p>
      <div className="space-y-2">
        {lines.map((line, idx) => (
          <textarea
            key={idx}
            value={line}
            onChange={(e) => handleLineChange(idx, e.target.value)}
            className="w-full border rounded p-2 text-sm min-h-[60px]"
            lang="ru"
          />
        ))}
      </div>
      <button
        onClick={() => onSave && onSave(text)}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        type="button"
      >
        Save Edits
      </button>
      <p className="text-xs text-gray-500 mt-2">Original Russian shown beside English in final view (per spec)</p>
    </div>
  )
}

export default EditableOCRScreen
