import React, { useState, useEffect, useCallback } from 'react'
import CursiveRenderer from '../components/CursiveRenderer'
import RussianKeyboard from '../components/RussianKeyboard'
import PhoneticKeyboard from '../components/PhoneticKeyboard'
import CopyButton, { CopyBothButton, CopyAllButton } from '../components/CopyButton'
import { latinToCyrillic } from '../lib/phonetic'
import { translateText } from '../lib/api'
import { speakText } from '../lib/speech'
import { transliterate } from '../lib/translit'
import ImageInput from '../components/ImageInput'
import AiAssist from '../components/AiAssist'
import HistoryPanel from '../components/HistoryPanel'

const CURSIVE_STYLES = [
  { id: 'cursive1', label: 'Bad Script' },
  { id: 'cursive2', label: 'Marck Script' },
  { id: 'cursive3', label: 'Caveat' },
  { id: 'cursive4', label: 'Serif Italic (fallback)' },
]

/** Card with an eyebrow label, title and an action slot on the right. */
const Section = ({ eyebrow, title, action, children, className = '' }) => (
  <section className={`card ${className}`}>
    <div className="card-header flex items-center justify-between gap-3">
      <div className="min-w-0">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5 truncate">
          {title}
        </h2>
      </div>
      {action}
    </div>
    <div className="card-body">{children}</div>
  </section>
)

/** Large translated/source text panel with a language badge, listening and
 *  an optional Cyrillic→Latin reading aid. */
const OutputBlock = ({ lang, label, children, speakLang, translit = false }) => {
  const [showTranslit, setShowTranslit] = useState(false)
  const text = typeof children === 'string' ? children : ''

  return (
    <div className="output-block min-h-[80px]">
      <span className="pill mb-2 bg-blue-50 text-blue-700 border border-blue-100 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-900">
        {lang}
      </span>
      <div
        lang={lang === 'EN' ? 'en' : 'ru'}
        className="text-2xl md:text-3xl font-medium break-words text-gray-900 dark:text-gray-100"
      >
        {children || <span className="output-block-empty text-base font-normal">…</span>}
      </div>

      {(speakLang || translit) && text.trim() && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {speakLang && (
            <button
              type="button"
              className="btn-ghost btn-sm"
              onClick={() => speakText(text, speakLang)}
              title="Read aloud with your browser's speech engine"
            >
              🔊 Listen
            </button>
          )}
          {translit && (
            <button
              type="button"
              className="btn-ghost btn-sm"
              onClick={() => setShowTranslit((v) => !v)}
              aria-expanded={showTranslit}
            >
              {showTranslit ? 'Hide transliteration' : 'aA Transliteration'}
            </button>
          )}
        </div>
      )}

      {translit && showTranslit && text.trim() && (
        <p className="mt-2 text-sm italic text-gray-500 dark:text-gray-400 break-words">
          {transliterate(text)}
        </p>
      )}

      {label && (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{label}</p>
      )}
    </div>
  )
}

export default function WritingPage() {
  const [mode, setMode] = useState('en-ru')
  const [en, setEn] = useState('Hello world')
  const [ru, setRu] = useState('Привет мир')
  const [phon, setPhon] = useState('privet mir')
  const [transEnRu, setTransEnRu] = useState('')
  const [transRuEn, setTransRuEn] = useState('')
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('')
  const [cursiveStyle, setCursiveStyle] = useState('cursive1')
  const [ocrLoading, setOcrLoading] = useState(false)
  const [ocrError, setOcrError] = useState('')

  const translate = useCallback(async (text, src, tgt) => {
    if (!text || !text.trim()) {
      setNotice('')
      return ''
    }
    try {
      setLoading(true)
      const data = await translateText(text, src, tgt)
      setNotice(
        data.meta?.fallback
          ? data.meta.notice || 'Using the limited offline glossary.'
          : '',
      )
      return data.translated_text ?? ''
    } catch (e) {
      setNotice(`Translation failed: ${e.message}`)
      return ''
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => { translate(en, 'en', 'ru').then(setTransEnRu) }, 500)
    return () => clearTimeout(t)
  }, [en, translate])

  useEffect(() => {
    const t = setTimeout(() => { translate(ru, 'ru', 'en').then(setTransRuEn) }, 500)
    return () => clearTimeout(t)
  }, [ru, translate])

  useEffect(() => {
    setRu(latinToCyrillic(phon))
  }, [phon])

  const typeRu = useCallback((key) => {
    if (key === 'BACKSPACE') setRu((p) => p.slice(0, -1))
    else setRu((p) => p + key)
  }, [])

  const typePhon = useCallback((key) => {
    if (key === 'BACKSPACE') setPhon((p) => p.slice(0, -1))
    else setPhon((p) => p + key)
  }, [])

  const handleOcrResult = useCallback((text) => {
    if (!text || !text.trim()) return
    setOcrError('')
    setNotice('')
    setRu(text)
    translate(text, 'ru', 'en').then(setTransRuEn)
  }, [translate])

  const busy = loading || ocrLoading

  const historyCurrent =
    mode === 'en-ru'
      ? { text: en, translation: transEnRu, src: 'en', tgt: 'ru' }
      : mode === 'ru-cursive'
        ? { text: ru, translation: transRuEn, src: 'ru', tgt: 'en' }
        : { text: ru, translation: '', src: 'ru', tgt: 'en' }

  const restoreHistory = useCallback((item) => {
    if (item.src === 'ru') {
      setMode('ru-cursive')
      setRu(item.text)
      setTransRuEn(item.translation)
    } else {
      setMode('en-ru')
      setEn(item.text)
      setTransEnRu(item.translation)
    }
  }, [])

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
        {/* Hero */}
        <header className="text-center space-y-4 pt-2">
          {/* Company logo */}
          <div className="mx-auto h-20 w-20 md:h-24 md:w-24 rounded-2xl bg-[#ffffff] p-2 shadow-lg ring-1 ring-black/5 grid place-items-center">
            <img
              src="/logo.png"
              alt="Company logo"
              className="h-full w-full object-contain"
              onError={(e) => { if (e.currentTarget.parentElement) e.currentTarget.parentElement.style.display = 'none' }}
            />
          </div>
          <p className="eyebrow">Type · Speak · Snap a photo</p>
          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight gradient-text leading-[1.1]">
            Russian Cursive Learning
            <span className="block text-2xl md:text-4xl mt-2 font-bold opacity-90">
              &amp; Reading Assistant
            </span>
          </h1>
          <p className="text-base md:text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            English ⇄ Russian, shown as block print and as real handwriting — with every
            email, date and course code kept intact.
          </p>
        </header>

        {/* Toolbar */}
        <div className="card overflow-visible">
          <div className="card-body py-4 flex flex-wrap items-center justify-center gap-x-6 gap-y-4">
            <div className="flex items-center gap-3">
              <label
                htmlFor="mode-select"
                className="eyebrow !text-gray-500 dark:!text-gray-400"
              >
                Mode
              </label>
              <select
                id="mode-select"
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                aria-label="Input mode"
                className="select-field !px-3 !py-1.5 rounded-lg border border-gray-200/90 bg-white/90 dark:border-slate-700 dark:bg-slate-800/80 shadow-sm"
              >
                <option value="en-ru">English → Russian</option>
                <option value="ru-cursive">Russian keyboard → English</option>
                <option value="phonetic">Latin-phonetic → Russian</option>
              </select>
            </div>

            <span
              className="hidden md:block h-8 w-px bg-gray-200 dark:bg-slate-700"
              aria-hidden="true"
            />

            <div className="flex items-center gap-3">
              <label
                htmlFor="font-select"
                className="eyebrow !text-gray-500 dark:!text-gray-400"
              >
                Cursive font
              </label>
              <select
                id="font-select"
                value={cursiveStyle}
                onChange={(e) => setCursiveStyle(e.target.value)}
                aria-label="Cursive font"
                className="select-field !px-3 !py-1.5 rounded-lg border border-gray-200/90 bg-white/90 dark:border-slate-700 dark:bg-slate-800/80 shadow-sm"
              >
                {CURSIVE_STYLES.map((s) => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Status line */}
          <div
            aria-live="polite"
            className="px-6 pb-4 flex flex-wrap items-center justify-center gap-2 min-h-[24px]"
          >
            {busy && (
              <span className="pill bg-blue-50 text-blue-700 border border-blue-100 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-900 animate-soft-pulse">
                <span className="h-1.5 w-1.5 rounded-full bg-blue-500" aria-hidden="true" />
                Processing…
              </span>
            )}
            {notice && (
              <span className="pill !text-amber-800 dark:!text-amber-300 bg-amber-50 dark:bg-amber-900/40 border border-amber-200 dark:border-amber-800 !px-4 !py-1.5 !text-sm">
                ⚠️ {notice}
              </span>
            )}
            {ocrError && (
              <span className="pill !text-red-700 dark:!text-red-300 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 !px-4 !py-1.5 !text-sm">
                {ocrError}
              </span>
            )}
          </div>
        </div>

        {/* ------------------------------------------------ English → Russian */}
        {mode === 'en-ru' && (
          <div className="grid lg:grid-cols-2 gap-6">
            <Section
              eyebrow="Input"
              title="English"
              action={<CopyButton text={en} />}
            >
              <div className="space-y-4">
                <textarea
                  value={en}
                  onChange={(e) => setEn(e.target.value)}
                  className="textarea-field min-h-[160px]"
                  placeholder="Type English…"
                  aria-label="English input"
                />
                <div className="flex flex-wrap gap-3">
                  <CopyBothButton text1={en} text2={transEnRu} label="Copy English + Russian" />
                  <CopyAllButton texts={[en, transEnRu]} label="Copy All" />
                </div>
              </div>
            </Section>

            <div className="space-y-6">
              <Section
                eyebrow="Result"
                title="Russian — Block"
                action={<CopyButton text={transEnRu} />}
              >
                <OutputBlock lang="RU" speakLang="ru" translit>{transEnRu}</OutputBlock>
              </Section>
              <AiAssist
                source={en}
                translation={transEnRu}
                src="en"
                tgt="ru"
                onUse={setTransEnRu}
              />
              <CursiveRenderer text={transEnRu} style={cursiveStyle} />
            </div>
          </div>
        )}

        {/* ------------------------------------------------ Russian → English */}
        {mode === 'ru-cursive' && (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="space-y-6">
              <Section
                eyebrow="Input"
                title="Russian"
                action={<CopyButton text={ru} />}
              >
                <div className="space-y-4">
                  <textarea
                    value={ru}
                    onChange={(e) => setRu(e.target.value)}
                    className="textarea-field min-h-[120px]"
                    lang="ru"
                    placeholder="Напишите по-русски…"
                    aria-label="Russian input"
                  />
                  <ImageInput
                    onTextExtracted={handleOcrResult}
                    onError={(e) => setOcrError(e)}
                    onLoading={setOcrLoading}
                  />
                  <RussianKeyboard onKeyPress={typeRu} />
                  <div className="flex flex-wrap gap-3">
                    <CopyBothButton text1={ru} text2={transRuEn} label="Copy Russian + English" />
                    <CopyAllButton texts={[ru, transRuEn]} label="Copy All" />
                  </div>
                </div>
              </Section>

              <Section
                eyebrow="Result"
                title="English (translated)"
                action={<CopyButton text={transRuEn} />}
              >
                <div className="output-block min-h-[60px] !border-green-100 dark:!border-green-900/60 bg-gradient-to-br from-white via-white to-green-50/60 dark:from-slate-900 dark:via-slate-900 dark:to-green-950/30">
                  <span className="pill mb-2 bg-green-50 text-green-700 border border-green-100 dark:bg-green-950/60 dark:text-green-300 dark:border-green-900">
                    EN
                  </span>
                  <p className="text-lg font-medium break-words text-gray-900 dark:text-gray-100">
                    {transRuEn || <span className="output-block-empty text-base font-normal">…</span>}
                  </p>
                  {transRuEn?.trim() && (
                    <button
                      type="button"
                      className="btn-ghost btn-sm mt-3"
                      onClick={() => speakText(transRuEn, 'en')}
                      title="Read the English translation aloud"
                    >
                      🔊 Listen
                    </button>
                  )}
                </div>
              </Section>
              <AiAssist
                source={ru}
                translation={transRuEn}
                src="ru"
                tgt="en"
                onUse={setTransRuEn}
              />
            </div>

            <div className="space-y-6">
              <Section
                eyebrow="Same text"
                title="Russian — Block"
                action={<CopyButton text={ru} />}
              >
                <OutputBlock lang="RU" speakLang="ru" translit>{ru}</OutputBlock>
              </Section>
              <CursiveRenderer text={ru} style={cursiveStyle} />
            </div>
          </div>
        )}

        {/* ---------------------------------------------------- Phonetic mode */}
        {mode === 'phonetic' && (
          <div className="grid lg:grid-cols-2 gap-6">
            <Section
              eyebrow="Input"
              title="Latin-phonetic"
              action={<CopyButton text={phon} />}
            >
              <div className="space-y-4">
                <textarea
                  value={phon}
                  onChange={(e) => setPhon(e.target.value)}
                  className="textarea-field min-h-[120px]"
                  placeholder="privet mir"
                  aria-label="Latin-phonetic input"
                />
                <PhoneticKeyboard onKeyPress={typePhon} />
                <div className="flex flex-wrap gap-3">
                  <CopyBothButton text1={phon} text2={ru} label="Copy Phonetic + Russian" />
                  <CopyAllButton texts={[phon, ru]} label="Copy All" />
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Latin-phonetic is mapped client-side, so it is instant and never mixes
                  with the Russian keyboard.
                </p>
              </div>
            </Section>

            <div className="space-y-6">
              <Section
                eyebrow="Mapped"
                title="Russian — Block"
                action={<CopyButton text={ru} />}
              >
                <OutputBlock lang="RU" speakLang="ru" translit>{ru}</OutputBlock>
              </Section>
              <CursiveRenderer text={ru} style={cursiveStyle} />
            </div>
          </div>
        )}

        <HistoryPanel current={historyCurrent} onRestore={restoreHistory} />
      </div>
    </div>
  )
}
