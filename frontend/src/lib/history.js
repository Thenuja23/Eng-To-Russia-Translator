// Translation history stored on the device only (localStorage).
// No server involvement, so it keeps working offline and never leaks text.

const KEY = 'etr_history_v1'
const MAX_ENTRIES = 60

function safeStorage() {
  try {
    if (typeof window === 'undefined' || !window.localStorage) return null
    return window.localStorage
  } catch {
    return null
  }
}

export function loadHistory() {
  const store = safeStorage()
  if (!store) return []
  try {
    const parsed = JSON.parse(store.getItem(KEY) || '[]')
    return Array.isArray(parsed) ? parsed.filter((e) => e && e.text) : []
  } catch {
    return []
  }
}

function persist(list) {
  const store = safeStorage()
  if (!store) return
  try {
    store.setItem(KEY, JSON.stringify(list))
  } catch {
    /* storage full or blocked — history is a convenience, never required */
  }
}

function sameEntry(a, b) {
  return (
    (a.text || '').trim() === (b.text || '').trim() &&
    (a.translation || '').trim() === (b.translation || '').trim() &&
    a.src === b.src &&
    a.tgt === b.tgt
  )
}

export function addHistoryEntry(entry) {
  if (!entry || !entry.text?.trim() || !entry.translation?.trim()) {
    return loadHistory()
  }
  const item = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    ts: Date.now(),
    src: entry.src || 'en',
    tgt: entry.tgt || 'ru',
    text: entry.text.trim(),
    translation: entry.translation.trim(),
  }
  const list = loadHistory().filter((e) => !sameEntry(e, item))
  const next = [item, ...list].slice(0, MAX_ENTRIES)
  persist(next)
  return next
}

export function removeHistoryEntry(id) {
  const next = loadHistory().filter((e) => e.id !== id)
  persist(next)
  return next
}

export function clearHistory() {
  persist([])
  return []
}

export function historyToCsv(list) {
  const escape = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`
  const rows = list.map((e) => {
    // Anki: front is the Russian side, back is the English side.
    const russian = e.src === 'ru' ? e.text : e.translation
    const english = e.src === 'ru' ? e.translation : e.text
    return [escape(russian), escape(english), escape(`${e.src}->${e.tgt}`), escape(new Date(e.ts).toISOString())].join(',')
  })
  return ['Front,Back,Direction,Date', ...rows].join('\n')
}

export function downloadText(filename, text, mime = 'text/plain;charset=utf-8') {
  try {
    const blob = new Blob([text], { type: mime })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (err) {
    console.error('Download failed:', err)
  }
}
