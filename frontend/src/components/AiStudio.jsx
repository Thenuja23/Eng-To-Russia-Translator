import React, { useEffect, useMemo, useState } from 'react'
import { aiEnhance, aiExplain, aiStatus, aiTranslate, aiPreferences, saveAiPreferences, saveAiCredential, deleteAiCredential, aiHistory, deleteAiHistory } from '../lib/api'
import CopyButton from './CopyButton'

const PROVIDER_NAMES = {
  openai: 'ChatGPT',
  anthropic: 'Claude',
  perplexity: 'Perplexity',
}

const DIRECTION_LABEL = {
  'en-ru': 'English → Russian',
  'ru-en': 'Russian → English',
}

function ProviderChip({ provider }) {
  return (
    <span
      className={`pill border ${
        provider.configured
          ? 'bg-green-50 text-green-800 border-green-200 dark:bg-green-950/40 dark:text-green-300 dark:border-green-900'
          : 'bg-gray-50 text-gray-500 border-gray-200 dark:bg-slate-800 dark:text-gray-400 dark:border-slate-700'
      }`}
    >
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 rounded-full ${provider.configured ? 'bg-green-500' : 'bg-gray-400'}`}
      />
      {PROVIDER_NAMES[provider.name] || provider.name}
      <span className="text-[10px] opacity-70">{provider.model}</span>
    </span>
  )
}

function TokenBadge({ ok }) {
  return (
    <span
      className={`pill border ${
        ok
          ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900'
          : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900'
      }`}
    >
      {ok ? '✓ tokens intact' : '✕ token lost'}
    </span>
  )
}

function SetupCard() {
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-800 dark:bg-amber-950/30 space-y-2">
      <p className="text-sm font-semibold text-amber-900 dark:text-amber-200">
        Cloud AI providers are not configured.
      </p>
      <p className="text-sm text-amber-800 dark:text-amber-300">
        The AI ensemble needs a provider key. Local Opus-MT translation remains available
        on the Write tab. To enable the ensemble, add one or more keys on the server:
      </p>
      <pre className="text-xs overflow-x-auto rounded-lg bg-white/80 p-3 border border-amber-200 dark:bg-slate-900/80 dark:border-amber-900 text-gray-700 dark:text-gray-300">
{`cd backend
cp .env.example .env
# edit .env and set any of:
#   OPENAI_API_KEY=sk-...
#   ANTHROPIC_API_KEY=sk-ant-...
#   PERPLEXITY_API_KEY=pplx-...
# then restart the backend`}
      </pre>
      <p className="text-xs text-amber-700 dark:text-amber-400">
        Every configured provider is queried in parallel; the safest, most
        consistent answer wins. Keys never reach the browser.
      </p>
    </div>
  )
}

function BestAnswer({ result, onUseAsTranslation }) {
  const text = result.mode === 'enhance' ? result.improved_text : result.text
  const label = result.mode === 'enhance' ? 'Improved translation' : 'Ensemble translation'
  return (
    <section className="card">
      <div className="card-header flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow">Consensus result</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            {label}
          </h3>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="pill bg-blue-50 text-blue-700 border border-blue-100 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-900">
            {PROVIDER_NAMES[result.provider] || result.provider}
          </span>
          <span className="pill bg-white text-gray-600 border border-gray-200 dark:bg-slate-800 dark:text-gray-300 dark:border-slate-700">
            agreement {Math.round((result.agreement || 0) * 100)}%
          </span>
          <TokenBadge ok={result.tokens_preserved} />
          {result.cached && (
            <span className="pill bg-white text-gray-500 border border-gray-200 dark:bg-slate-800 dark:text-gray-400 dark:border-slate-700">
              cached
            </span>
          )}
        </div>
      </div>
      <div className="card-body space-y-3">
        <div className="output-block min-h-[80px]">
          <p className="text-xl md:text-2xl font-medium break-words text-gray-900 dark:text-gray-100">
            {text}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <CopyButton text={text} />
          {result.mode === 'enhance' && onUseAsTranslation && (
            <button type="button" className="btn-ghost btn-sm" onClick={() => onUseAsTranslation(text)}>
              Use as translation
            </button>
          )}
          <span className="text-xs text-gray-500 dark:text-gray-400 self-center">
            {result.providers_used} provider{result.providers_used === 1 ? '' : 's'} answered
          </span>
        </div>
      </div>
    </section>
  )
}

function Candidates({ candidates }) {
  if (!candidates?.length) return null
  return (
    <section className="card">
      <div className="card-header">
        <p className="eyebrow">Transparency</p>
        <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
          Every model's answer
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Ranked by token safety, agreement with the other models, sentence
          completeness and script. The top card is what the app returned.
        </p>
      </div>
      <div className="card-body grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {candidates.map((c) => (
          <article
            key={`${c.provider}-${c.model}`}
            className={`rounded-xl border p-3 space-y-2 ${
              c.error
                ? 'border-red-200 bg-red-50/50 dark:border-red-900 dark:bg-red-950/20'
                : 'border-gray-200 bg-white/70 dark:border-slate-700 dark:bg-slate-900/60'
            }`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                {PROVIDER_NAMES[c.provider] || c.provider}
              </span>
              <span className="text-[11px] text-gray-500 dark:text-gray-400">
                {c.latency_ms} ms
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              <span className="pill bg-gray-100 text-gray-600 border border-gray-200 dark:bg-slate-800 dark:text-gray-300 dark:border-slate-700">
                score {c.score.toFixed(2)}
              </span>
              <span className="pill bg-gray-100 text-gray-600 border border-gray-200 dark:bg-slate-800 dark:text-gray-300 dark:border-slate-700">
                {Math.round((c.agreement || 0) * 100)}% agree
              </span>
            </div>
            {c.error ? (
              <p className="text-xs text-red-700 dark:text-red-300 break-words">{c.error}</p>
            ) : (
              <p className="text-sm text-gray-700 dark:text-gray-200 break-words whitespace-pre-wrap">
                {c.text}
              </p>
            )}
          </article>
        ))}
      </div>
    </section>
  )
}

function ExplanationCard({ explanation }) {
  return (
    <section className="card">
      <div className="card-header flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow">Tutor</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            Explanation
          </h3>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="pill bg-indigo-50 text-indigo-700 border border-indigo-100 dark:bg-indigo-950/60 dark:text-indigo-300 dark:border-indigo-900">
            {PROVIDER_NAMES[explanation.provider] || explanation.provider}
          </span>
          {explanation.cached && (
            <span className="pill bg-white text-gray-500 border border-gray-200 dark:bg-slate-800 dark:text-gray-400 dark:border-slate-700">
              cached
            </span>
          )}
        </div>
      </div>
      <div className="card-body space-y-3">
        <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap text-gray-800 dark:text-gray-200">
          {explanation.explanation}
        </p>
        <CopyButton text={explanation.explanation} label="Copy explanation" />
      </div>
    </section>
  )
}

export default function AiStudio() {
  const [status, setStatus] = useState(null)
  const [statusError, setStatusError] = useState('')
  const [direction, setDirection] = useState('en-ru')
  const [text, setText] = useState(
    'Email anna.smith@example.com about the meeting on 2026-10-20 at 15:30.',
  )
  const [translation, setTranslation] = useState('')
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [explanation, setExplanation] = useState(null)
  const [preferences, setPreferences] = useState({ provider_mode: 'auto', providers: ['openai', 'anthropic', 'perplexity'], translation_mode: 'accurate', level: 'intermediate', explanation_language: 'en', include_grammar: false, include_examples: true, history_enabled: false })
  const [providerKey, setProviderKey] = useState('')
  const [history, setHistory] = useState([])

  useEffect(() => {
    let alive = true
    aiStatus()
      .then((s) => alive && setStatus(s))
      .catch((e) => alive && setStatusError(e.message))
    aiPreferences().then((p) => alive && setPreferences((old) => ({ ...old, ...p }))).catch(() => {})
    return () => {
      alive = false
    }
  }, [])

  const [src, tgt] = useMemo(
    () => (direction === 'en-ru' ? ['en', 'ru'] : ['ru', 'en']),
    [direction],
  )

  const configured = status?.configured || 0
  const canRun = configured > 0 && !busy

  const run = async (kind, fn) => {
    setBusy(kind)
    setError('')
    try {
      const data = await fn()
      if (kind === 'explain') setExplanation(data)
      else {
        setResult(data)
        if (data.mode === 'translate') setTranslation(data.text)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy('')
    }
  }

  const onTranslate = () =>
    run('translate', () => aiTranslate(text, src, tgt, preferences.translation_mode))

  const updatePreference = async (next) => {
    const value = { ...preferences, ...next }
    setPreferences(value)
    try { await saveAiPreferences(value); const s = await aiStatus(); setStatus(s) } catch (e) { setError(e.message) }
  }

  const connectKey = async (provider) => {
    if (!providerKey || !window.confirm('The provider receives text you submit under its own privacy terms. You pay for API usage. The key is stored encrypted on this server and will not be shown again. Connect this provider?')) return
    try { await saveAiCredential(provider, providerKey); setProviderKey(''); const s = await aiStatus(); setStatus(s) } catch (e) { setError(e.message) }
  }

  const refreshHistory = async () => { try { setHistory(await aiHistory()) } catch (e) { setError(e.message) } }

  const onEnhance = () =>
    run('enhance', () => aiEnhance(text, translation, src, tgt))

  const onExplain = () =>
    run('explain', () =>
      aiExplain({
        text,
        translation: translation || result?.text || '',
        srcLang: src,
        tgtLang: tgt,
        question,
      }),
    )

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-6 animate-fade-in">
      <header className="text-center space-y-2">
        <p className="eyebrow">Multi-model AI</p>
        <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          One answer from ChatGPT, Claude &amp; Perplexity
        </h2>
        <p className="text-sm md:text-base text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
          Every configured model answers the same prompt in parallel. The app keeps the
          answer that preserves your e-mails, dates and course codes and agrees most with
          the others — then shows you every candidate so nothing is hidden.
        </p>
      </header>

      {statusError && (
        <div className="card">
          <div className="card-body text-sm text-red-700 dark:text-red-300" role="alert">
            AI service unreachable: {statusError}
          </div>
        </div>
      )}

      <section className="card">
        <div className="card-header flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="eyebrow">Providers</p>
            <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
              {status
                ? status.mode === 'ensemble'
                  ? 'Ensemble active'
                  : status.mode === 'single'
                    ? 'Single provider active'
                    : 'Cloud AI not configured'
                : 'Checking…'}
            </h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {(status?.providers || []).map((p) => (
              <ProviderChip key={p.name} provider={p} />
            ))}
          </div>
        </div>
        <div className="card-body space-y-4">
          {status && status.mode === 'offline' && <SetupCard />}

          {configured > 0 && (
            <>
              <div className="flex flex-wrap items-center gap-3">
                <label htmlFor="ai-direction" className="eyebrow !text-gray-500 dark:!text-gray-400">
                  Direction
                </label>
                <select
                  id="ai-direction"
                  value={direction}
                  onChange={(e) => setDirection(e.target.value)}
                  className="select-field !px-3 !py-1.5 rounded-lg border border-gray-200/90 bg-white/90 dark:border-slate-700 dark:bg-slate-800/80 shadow-sm"
                >
                  {Object.entries(DIRECTION_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              <div className="grid lg:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="ai-text" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Source text
                  </label>
                  <textarea
                    id="ai-text"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    className="textarea-field min-h-[140px]"
                    placeholder="Type or paste the text…"
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="ai-translation" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Existing translation <span className="font-normal text-gray-500">(for Review / Explain)</span>
                  </label>
                  <textarea
                    id="ai-translation"
                    value={translation}
                    onChange={(e) => setTranslation(e.target.value)}
                    className="textarea-field min-h-[140px]"
                    placeholder="Paste a translation to improve it…"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="ai-question" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Ask about it <span className="font-normal text-gray-500">(optional)</span>
                </label>
                <input
                  id="ai-question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="input-field"
                  placeholder="Why is it «на почте» and not «в почте»?"
                />
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  className="btn-primary btn-sm"
                  onClick={onTranslate}
                  disabled={!canRun || !text.trim()}
                >
                  {busy === 'translate' ? 'Translating…' : '✨ Translate (ensemble)'}
                </button>
                <button
                  type="button"
                  className="btn-ghost btn-sm"
                  onClick={onEnhance}
                  disabled={!canRun || !text.trim() || !translation.trim()}
                >
                  {busy === 'enhance' ? 'Reviewing…' : 'Review translation'}
                </button>
                <button
                  type="button"
                  className="btn-ghost btn-sm"
                  onClick={onExplain}
                  disabled={!canRun || !text.trim()}
                >
                  {busy === 'explain' ? 'Explaining…' : 'Explain like a tutor'}
                </button>
              </div>

              {error && (
                <p className="text-sm text-red-700 dark:text-red-300" role="alert">
                  {error}
                </p>
              )}

              <p className="text-xs text-gray-500 dark:text-gray-400">
                Limits: {status.limits.max_chars} characters, {status.limits.requests_per_minute} requests/min.
                Results are cached for {status.cache_ttl_seconds}s. Keys stay on the server — the browser never sees them.
              </p>
            </>
          )}
        </div>
      </section>

      <section className="card" aria-labelledby="ai-settings-title">
        <div className="card-header"><h3 id="ai-settings-title" className="text-lg font-semibold">Learning and provider settings</h3></div>
        <div className="card-body grid gap-4 md:grid-cols-2">
          <label className="text-sm">Provider routing
            <select className="select-field mt-1" value={preferences.provider_mode} onChange={(e) => updatePreference({ provider_mode: e.target.value })}>
              <option value="auto">Auto (recommended)</option><option value="custom">Custom personal-key combination</option><option value="personal">Personal keys only</option>
            </select>
          </label>
          <label className="text-sm">Translation mode
            <select className="select-field mt-1" value={preferences.translation_mode} onChange={(e) => updatePreference({ translation_mode: e.target.value })}>
              <option value="accurate">Accurate translation</option><option value="natural">Natural Russian</option><option value="student">Student learning</option><option value="academic">Academic Russian</option><option value="simple">Simple Russian</option><option value="context">Context-aware translation</option><option value="grammar">Grammar correction</option>
            </select>
          </label>
          <fieldset className="text-sm"><legend className="font-medium">Enabled providers</legend>{[['openai','OpenAI'],['anthropic','Claude'],['perplexity','Perplexity']].map(([id,label]) => <label key={id} className="mr-4 inline-flex items-center gap-2"><input type="checkbox" checked={preferences.providers.includes(id)} onChange={(e) => updatePreference({ providers: e.target.checked ? [...preferences.providers,id] : preferences.providers.filter((p) => p !== id) })}/>{label}</label>)}</fieldset>
          <label className="text-sm">Russian proficiency
            <select className="select-field mt-1" value={preferences.level} onChange={(e) => updatePreference({ level: e.target.value })}><option>beginner</option><option>intermediate</option><option>advanced</option></select>
          </label>
          <label className="text-sm">Explanation language
            <select className="select-field mt-1" value={preferences.explanation_language} onChange={(e) => updatePreference({ explanation_language: e.target.value })}><option value="en">English</option><option value="ru">Русский</option><option value="si">සිංහල</option></select>
          </label>
          <label className="text-sm inline-flex items-center gap-2"><input type="checkbox" checked={preferences.history_enabled} onChange={(e) => updatePreference({ history_enabled: e.target.checked })}/>Save AI requests to my account history (off by default)</label>
          <div className="md:col-span-2 rounded-lg bg-gray-50 p-3 text-xs text-gray-600 dark:bg-slate-800 dark:text-gray-300">
            Connecting a personal key means submitted text is sent to that provider under its privacy terms and you pay its API charges. Keys are encrypted on this server and are never displayed again. Configure <code>AI_CREDENTIALS_ENCRYPTION_KEY</code> on the backend to enable personal key storage.
            <div className="mt-2 flex flex-wrap gap-2"><input aria-label="Provider API key" type="password" autoComplete="off" value={providerKey} onChange={(e) => setProviderKey(e.target.value)} className="input-field" placeholder="Paste personal provider key"/>{[['openai','Connect OpenAI'],['anthropic','Connect Claude'],['perplexity','Connect Perplexity']].map(([id,label]) => <button key={id} type="button" className="btn-secondary btn-sm" onClick={() => connectKey(id)}>{label}</button>)}</div>
            <div className="mt-2 flex gap-2">{(status?.connected_personal || []).map((p) => <button key={p} type="button" className="btn-ghost btn-sm" onClick={async () => { if (window.confirm(`Delete saved ${p} credential? This cannot be undone.`)) { await deleteAiCredential(p); setStatus(await aiStatus()) } }}>Disconnect {p}</button>)}</div>
          </div>
          {preferences.history_enabled && <div className="md:col-span-2"><button className="btn-secondary btn-sm" onClick={refreshHistory}>Load AI history</button>{history.length > 0 && <><button className="btn-ghost btn-sm ml-2" onClick={async () => { if (window.confirm('Clear your entire AI history?')) { await deleteAiHistory(); setHistory([]) } }}>Clear history</button><ul className="mt-3 space-y-2">{history.map((h) => <li key={h.id} className="rounded border p-2 text-xs"><span>{new Date(h.created_at).toLocaleString()} · {h.provider} / {h.model} · {h.mode}</span><p>{h.source} → {h.translated}</p><button className="btn-ghost btn-sm" onClick={async () => { await deleteAiHistory(h.id); setHistory(history.filter((x) => x.id !== h.id)) }}>Delete</button></li>)}</ul></>}</div>}
        </div>
      </section>

      {result && (
        <BestAnswer
          result={result}
          onUseAsTranslation={setTranslation}
        />
      )}
      {explanation && <ExplanationCard explanation={explanation} />}
      {result && <Candidates candidates={result.candidates} />}
    </div>
  )
}
