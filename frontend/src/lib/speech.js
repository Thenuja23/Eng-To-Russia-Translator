export function getVoices() {
  if (!('speechSynthesis' in window)) return []
  return window.speechSynthesis.getVoices()
}

export function speakText(text, lang = 'ru') {
  if (!text || !('speechSynthesis' in window)) {
    console.warn('Speech synthesis not supported')
    return
  }
  try {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang === 'ru' ? 'ru-RU' : 'en-US'
    utterance.rate = 0.9
    utterance.pitch = 1.0
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
  } catch (err) {
    console.error('Speech failed:', err)
  }
}
