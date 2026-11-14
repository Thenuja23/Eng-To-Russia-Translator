// Single place that knows where the API lives and how to talk to it.
//
// By default requests are relative, so the Vite dev/preview server proxies
// them to FastAPI on the server (see vite.config.js). That keeps the browser on
// one origin, which is required for the HttpOnly session cookie and also makes
// the app work through a remote preview hostname. For a separate API host, set
// VITE_API_URL at build time.
const configuredApi = (import.meta.env?.VITE_API_URL || '').replace(/\/$/, '')
export const API = configuredApi

const apiFetch = (path, options = {}) =>
  fetch(`${API}${path}`, { credentials: 'include', ...options })

async function parseError(res) {
  let detail = `HTTP ${res.status}`
  try {
    const body = await res.json()
    if (body && body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
  } catch {
    /* keep the status text */
  }
  return detail
}

export async function translateText(text, srcLang = 'en', tgtLang = 'ru', engine) {
  const res = await apiFetch('/translation/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, src_lang: srcLang, tgt_lang: tgtLang, ...(engine ? { engine } : {}) }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

let translationEnginesPromise = null

/** Available translation engines, including whether Google is configured. */
export async function translationEngines() {
  if (!translationEnginesPromise) {
    translationEnginesPromise = apiFetch('/translation/engines')
      .then(async (res) => {
        if (!res.ok) throw new Error(await parseError(res))
        return res.json()
      })
      .catch((err) => {
        translationEnginesPromise = null // allow a retry after a transient failure
        throw err
      })
  }
  return translationEnginesPromise
}

export async function processText(text) {
  const res = await apiFetch('/text/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function submitFeedback(payload) {
  const res = await apiFetch('/feedback/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

/** Send an image (file or Blob) to the OCR endpoint; returns { text, engine }. */
export async function ocrImage(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await apiFetch('/ocr', { method: 'POST', body: form })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

// ---------------------------------------------------------------- AI (optional)

let aiStatusPromise = null

/** Provider availability. Cached after the first successful call. */
export async function aiStatus() {
  if (!aiStatusPromise) {
    aiStatusPromise = apiFetch('/ai/status')
      .then(async (res) => {
        if (!res.ok) throw new Error(await parseError(res))
        return res.json()
      })
      .catch((err) => {
        aiStatusPromise = null // allow a retry after a transient failure
        throw err
      })
  }
  return aiStatusPromise
}

async function aiPost(path, payload) {
  const res = await apiFetch(`/ai/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

/** Multi-provider translation (consensus of OpenAI/Claude/Perplexity). */
export function aiTranslate(text, srcLang = 'en', tgtLang = 'ru', translationMode = 'accurate') {
  return aiPost('translate', { text, src_lang: srcLang, tgt_lang: tgtLang, translation_mode: translationMode })
}

/** Ask the ensemble to review and improve an existing translation. */
export function aiEnhance(text, translation, srcLang = 'en', tgtLang = 'ru') {
  return aiPost('enhance', {
    text,
    translation,
    src_lang: srcLang,
    tgt_lang: tgtLang,
  })
}

/** Explain meaning, grammar and cursive reading. */
export function aiExplain({ text, translation = '', srcLang = 'en', tgtLang = 'ru', question = '' }) {
  return aiPost('explain', {
    text,
    translation,
    src_lang: srcLang,
    tgt_lang: tgtLang,
    question,
  })
}

export async function aiPreferences() {
  const res = await apiFetch('/ai/preferences')
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function saveAiPreferences(preferences) {
  const res = await apiFetch('/ai/preferences', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(preferences) })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function saveAiCredential(provider, apiKey) {
  const res = await apiFetch(`/ai/credentials/${provider}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ api_key: apiKey, consent: true }) })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function deleteAiCredential(provider) {
  const res = await apiFetch(`/ai/credentials/${provider}?confirm=true`, { method: 'DELETE' })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function aiHistory() {
  const res = await apiFetch('/ai/history')
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function deleteAiHistory(id) {
  const res = await apiFetch(id ? `/ai/history/${encodeURIComponent(id)}` : '/ai/history', { method: 'DELETE' })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

/**
 * Word-by-word vocabulary analysis (English + Sinhala meanings, part of
 * speech, grammar notes and two example sentences per word).
 *
 * Uses the AI ensemble when the server has a provider key, and the built-in
 * Russian dictionary + grammar engine otherwise, so this always answers.
 * Resolves to { words: [...], mode: 'ai' | 'offline', stats, notice }.
 */
export async function analyzeVocab(text) {
  const res = await apiFetch('/vocab/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}
