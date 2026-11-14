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
  const [providerKeys, setProviderKeys] = useState({})
  const [visibleKeys, setVisibleKeys] = useState({})
  const [connectionState, setConnectionState] = useState({})
  const [connectionError, setConnectionError] = useState({})
  const [history, setHistory] = useState([])
  const [historyQuery, setHistoryQuery] = useState('')
  const [historyProvider, setHistoryProvider] = useState('')

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
    const key = providerKeys[provider]?.trim()
    if (!key) return
    if (!window.confirm('Text you submit will be sent to this provider under its own privacy terms. You pay any API charges. The key is encrypted on this server and will not be shown again. Continue?')) return
    setConnectionState((s) => ({ ...s, [provider]: 'connecting' }))
    setConnectionError((s) => ({ ...s, [provider]: '' }))
    try {
      await saveAiCredential(provider, key)
      setProviderKeys((s) => ({ ...s, [provider]: '' }))
      setConnectionState((s) => ({ ...s, [provider]: 'connected' }))
      const status = await aiStatus(); setStatus(status)
    } catch (e) {
      setConnectionState((s) => ({ ...s, [provider]: 'failed' }))
      setConnectionError((s) => ({ ...s, [provider]: e.message }))
    }
  }

  const disconnectProvider = async (provider) => {
    if (!window.confirm(`Delete your saved ${provider} API key? This cannot be undone.`)) return
    try {
      await deleteAiCredential(provider)
      setConnectionState((s) => ({ ...s, [provider]: 'not_connected' }))
      setStatus(await aiStatus())
    } catch (e) { setConnectionError((s) => ({ ...s, [provider]: e.message })) }
  }

  const refreshHistory = async () => { try { setHistory(await aiHistory({ q: historyQuery, provider: historyProvider })) } catch (e) { setError(e.message) } }

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
        <p className="text-xs text-gray-500 dark:text-gray-400">AI translations are suggestions, not guaranteed corrections. Review the result in context.</p>
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
                  <div className="flex flex-wrap gap-2" aria-label="Russian grammar analysis shortcuts">
                    {['Part of speech and word meaning', 'Noun gender and case', 'Verb infinitive, conjugation and aspect', 'Adjective agreement', 'Declension and conjugation', 'Sentence structure'].map((prompt) => <button key={prompt} type="button" className="btn-ghost btn-sm" onClick={() => setQuestion(`Analyze: ${prompt}. Explain at university learner level and include at least two practical examples.`)}>{prompt}</button>)}
                  </div>
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
          <div className="flex flex-col gap-2 text-sm"><label className="inline-flex items-center gap-2"><input type="checkbox" checked={preferences.include_grammar} onChange={(e) => updatePreference({ include_grammar: e.target.checked })}/>Include grammar in explanations</label><label className="inline-flex items-center gap-2"><input type="checkbox" checked={preferences.include_examples} onChange={(e) => updatePreference({ include_examples: e.target.checked })}/>Include example sentences</label></div>
          <div className="md:col-span-2">
            <h4 className="mb-2 font-semibold">Personal AI provider connections</h4>
            <p className="mb-3 text-xs text-gray-600 dark:text-gray-300">Provider validation runs on the server. Keys are encrypted at rest, never returned to this page, and must be pasted again when updating. Text is sent to the chosen provider under its terms; personal API usage may incur charges.</p>
            <div className="grid gap-3 lg:grid-cols-3">
              {[
                { id: 'openai', name: 'OpenAI', mark: 'O', url: 'https://platform.openai.com/api-keys' },
                { id: 'anthropic', name: 'Claude', mark: 'A', url: 'https://platform.claude.com/settings/keys' },
                { id: 'perplexity', name: 'Perplexity', mark: 'P', url: 'https://www.perplexity.ai/account/api/keys' },
              ].map(({ id, name, mark, url }) => {
                const connected = (status?.connected_personal || []).includes(id)
                const state = connectionState[id] || (connected ? 'connected' : 'not_connected')
                const styles = state === 'connected'
                  ? 'bg-green-50 text-green-700 dark:bg-green-950/40 dark:text-green-300'
                  : state === 'failed'
                    ? 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300'
                    : state === 'connecting'
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300'
                      : 'bg-gray-100 text-gray-600 dark:bg-slate-700 dark:text-gray-300'
                const statusLabel = { connected: 'Connected', connecting: 'Connecting…', failed: 'Connection Failed', not_connected: 'Not Connected' }[state]
                return <article key={id} className="rounded-xl border border-gray-200 p-4 dark:border-slate-700">
                  <div className="mb-3 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2"><span aria-hidden="true" className="grid h-8 w-8 place-items-center rounded-lg bg-gray-100 font-bold dark:bg-slate-700">{mark}</span><h5 className="font-semibold">{name}</h5></div>
                    <span role="status" className={`inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs ${styles}`}><span aria-hidden="true" className={`h-2 w-2 rounded-full ${state === 'connected' ? 'bg-green-500' : state === 'failed' ? 'bg-red-500' : state === 'connecting' ? 'bg-blue-500' : 'bg-gray-400'}`}/>{statusLabel}</span>
                  </div>
                  <a href={url} target="_blank" rel="noopener noreferrer" className="btn-secondary btn-sm inline-flex">Connect {name}</a>
                  <label className="mt-3 block text-xs font-medium" htmlFor={`api-key-${id}`}>{connected ? 'Replace saved API key' : 'Personal API key'}</label>
                  <div className="mt-1 flex gap-1"><input id={`api-key-${id}`} type={visibleKeys[id] ? 'text' : 'password'} autoComplete="new-password" spellCheck="false" value={providerKeys[id] || ''} onChange={(e) => setProviderKeys((s) => ({ ...s, [id]: e.target.value }))} className="input-field min-w-0 flex-1" placeholder={connected ? '••••••••••••  (saved key)' : 'Paste API key'} aria-describedby={`key-note-${id}`}/><button type="button" className="btn-ghost btn-sm" aria-label={`${visibleKeys[id] ? 'Hide' : 'Show'} ${name} API key`} onClick={() => setVisibleKeys((s) => ({ ...s, [id]: !s[id] }))}>{visibleKeys[id] ? 'Hide' : 'Show'}</button></div>
                  <p id={`key-note-${id}`} className="mt-1 text-[11px] text-gray-500">Saved keys are masked and cannot be retrieved.</p>
                  <div className="mt-2 flex flex-wrap gap-2"><button type="button" className="btn-primary btn-sm" disabled={!providerKeys[id]?.trim() || state === 'connecting'} onClick={() => connectKey(id)}>{state === 'connecting' ? 'Validating…' : 'Save API Key'}</button>{connected && <button type="button" className="btn-ghost btn-sm" onClick={() => disconnectProvider(id)}>Disconnect</button>}</div>
                  {connectionError[id] && <p role="alert" className="mt-2 text-xs text-red-700 dark:text-red-300">{connectionError[id]}</p>}
                </article>
              })}
            </div>
            <p className="mt-2 text-xs text-gray-500">Personal key storage requires the server setting <code>AI_CREDENTIALS_ENCRYPTION_KEY</code>.</p>
          </div>
          {preferences.history_enabled && <div className="md:col-span-2"><div className="mb-2 flex flex-wrap gap-2"><input className="input-field" aria-label="Search AI history" placeholder="Search history" value={historyQuery} onChange={(e) => setHistoryQuery(e.target.value)}/><select className="select-field" aria-label="Filter AI history by provider" value={historyProvider} onChange={(e) => setHistoryProvider(e.target.value)}><option value="">All providers</option><option value="openai">OpenAI</option><option value="anthropic">Claude</option><option value="perplexity">Perplexity</option></select><button className="btn-secondary btn-sm" onClick={refreshHistory}>Search history</button><button className="btn-ghost btn-sm" onClick={async () => { if (window.confirm('Clear your entire AI history?')) { await deleteAiHistory(); setHistory([]) } }}>Clear history</button></div>{history.length > 0 && <ul className="mt-3 space-y-2">{history.map((h) => <li key={h.id} className="rounded border p-2 text-xs"><span>{new Date(h.created_at).toLocaleString()} · {h.provider} / {h.model} · {h.mode}</span><p>{h.source} → {h.translated}</p><button className="btn-ghost btn-sm" onClick={() => { setText(h.source); setTranslation(h.translated) }}>Reuse</button><button className="btn-ghost btn-sm" onClick={async () => { await deleteAiHistory(h.id); setHistory(history.filter((x) => x.id !== h.id)) }}>Delete</button></li>)}</ul>}</div>}
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
