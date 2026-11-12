import React, { useEffect, useRef, useState } from 'react'

/**
 * Microphone button that recognises spoken Russian and turns it into text.
 *
 * Uses the browser's Web Speech API (SpeechRecognition). The recognised text
 * is handed to `onText(text)` once the user stops speaking. Interim results
 * are shown live while listening so the user gets immediate feedback.
 *
 * Chrome/Edge/Safari support it; Firefox currently does not, in which case a
 * friendly message is shown instead of a broken button.
 */
const VoiceInput = ({ onText, onError }) => {
  const [supported] = useState(
    () => 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window,
  )
  const [listening, setListening] = useState(false)
  const [interim, setInterim] = useState('')
  const recognitionRef = useRef(null)

  useEffect(() => () => {
    // Stop the microphone if the component unmounts mid-listen.
    try { recognitionRef.current?.stop() } catch { /* already stopped */ }
  }, [])

  const stop = () => {
    try { recognitionRef.current?.stop() } catch { /* nothing running */ }
    setListening(false)
  }

  const start = () => {
    onError?.('')
    const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!Ctor) {
      onError?.(
        'Voice input is not supported in this browser. Try Chrome, Edge or Safari, or type the words instead.',
      )
      return
    }
    const recognition = new Ctor()
    recognitionRef.current = recognition
    recognition.lang = 'ru-RU'
    recognition.interimResults = true
    recognition.continuous = false
    recognition.maxAlternatives = 1

    let finalText = ''
    recognition.onresult = (event) => {
      let live = ''
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i]
        if (result.isFinal) finalText += result[0].transcript
        else live += result[0].transcript
      }
      setInterim(live)
    }
    recognition.onerror = (event) => {
      setListening(false)
      setInterim('')
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        onError?.('Microphone access was blocked. Allow the microphone and try again.')
      } else if (event.error === 'no-speech') {
        onError?.('No speech was heard. Press the microphone and speak in Russian.')
      } else if (event.error !== 'aborted') {
        onError?.(`Voice recognition error: ${event.error}`)
      }
    }
    recognition.onend = () => {
      setListening(false)
      setInterim('')
      const text = finalText.trim()
      if (text) onText?.(text)
    }

    try {
      recognition.start()
      setListening(true)
    } catch {
      onError?.('Could not start the microphone. Try again.')
    }
  }

  if (!supported) return null

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={listening ? stop : start}
        aria-pressed={listening}
        title={listening ? 'Stop recording' : 'Speak in Russian'}
        className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all duration-200
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
          dark:focus-visible:ring-offset-slate-900 active:scale-[0.98]
          ${listening
            ? 'text-white bg-red-600 shadow-md shadow-red-600/30 animate-soft-pulse'
            : 'text-white bg-gradient-to-b from-rose-500 to-red-600 shadow-[0_6px_16px_-8px_rgb(220_38_38/0.9)] hover:from-rose-600 hover:to-red-700'}`}
      >
        <span aria-hidden="true" className="text-lg leading-none">🎤</span>
        <span>{listening ? 'Listening… (tap to stop)' : 'Speak Russian'}</span>
      </button>
      {interim && (
        <span
          className="text-sm text-gray-600 dark:text-gray-300 italic truncate max-w-[16rem] md:max-w-xs"
          aria-live="polite"
        >
          {interim}…
        </span>
      )}
    </div>
  )
}

export default VoiceInput
