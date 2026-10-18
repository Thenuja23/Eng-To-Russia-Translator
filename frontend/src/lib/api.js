// Single place that knows where the API lives and how to talk to it.
export const API = import.meta.env?.VITE_API_URL || 'http://127.0.0.1:8000'

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
  const res = await fetch(`${API}/translation/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, src_lang: srcLang, tgt_lang: tgtLang, ...(engine ? { engine } : {}) }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function processText(text) {
  const res = await fetch(`${API}/text/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function submitFeedback(payload) {
  const res = await fetch(`${API}/feedback/`, {
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
  const res = await fetch(`${API}/ocr`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}
