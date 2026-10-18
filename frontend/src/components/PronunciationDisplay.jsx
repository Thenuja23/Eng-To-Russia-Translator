import React from 'react'
import { speakText, getVoices } from '../lib/speech'

const PronunciationDisplay = ({ text, lang = 'ru' }) => {
  const handleSpeak = () => {
    speakText(text, lang)
  }

  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-md font-semibold text-gray-700">Pronunciation</h3>
        <button
          onClick={handleSpeak}
          className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          type="button"
        >
          Play Audio
        </button>
      </div>
      <div className="text-sm text-gray-600">
        <span className="font-medium">Text:</span> <span lang={lang}>{text}</span>
      </div>
    </div>
  )
}

export default PronunciationDisplay
