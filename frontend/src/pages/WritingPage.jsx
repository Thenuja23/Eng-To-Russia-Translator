import React, { useState, useEffect } from 'react'
import CursiveRenderer from '../components/CursiveRenderer'
import RussianKeyboard from '../components/RussianKeyboard'
import PhoneticKeyboard from '../components/PhoneticKeyboard'
import CopyButton, { CopyBothButton, CopyAllButton } from '../components/CopyButton'
import { latinToCyrillic } from '../lib/phonetic'

const API = 'http://127.0.0.1:8000'

export default function WritingPage() {
  const [mode, setMode] = useState('en-ru')
  const [en, setEn] = useState('hello world')
  const [ru, setRu] = useState('привет мир')
  const [phon, setPhon] = useState('privet mir')
  const [transEnRu, setTransEnRu] = useState('привет мир')
  const [transRuEn, setTransRuEn] = useState('hello world')
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('')

  async function translate(text, src='ru', tgt='en') {
    try {
      setLoading(true)
      const res = await fetch(`${API}/translation/`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({text, src_lang:src, tgt_lang:tgt})
      })
      const data = await res.json()
      // Surface a notice when the offline glossary fallback was used
      if (data.meta && data.meta.fallback) {
        setNotice(data.meta.notice || 'Using limited offline glossary.')
      } else {
        setNotice('')
      }
      return data.translated_text || text
    } catch(e) {
      setNotice('Translation service unreachable — is the backend running on ' + API + '?')
      return text
    } finally {
      setLoading(false)
    }
  }

  function doPhonToRu() {
    setRu(latinToCyrillic(phon))
  }

  // Auto-translate on change for better UX
  useEffect(() => {
    const t = setTimeout(() => {
      translate(en, 'en', 'ru').then(setTransEnRu)
    }, 500)
    return () => clearTimeout(t)
  }, [en])

  useEffect(() => {
    const t = setTimeout(() => {
      translate(ru, 'ru', 'en').then(setTransRuEn)
    }, 500)
    return () => clearTimeout(t)
  }, [ru])

  useEffect(() => {
    setRu(latinToCyrillic(phon))
  }, [phon])

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
        <header className="text-center space-y-4">
          <h1 className="text-3xl md:text-5xl font-bold gradient-text">
            Russian Cursive Learning & Reading Assistant
          </h1>
          <p className="text-lg md:text-xl text-gray-600 max-w-3xl mx-auto">
            English → Russian • Russian → English • Block + Cursive
          </p>
          <div className="inline-block card px-6 py-4">
            <select value={mode} onChange={e=>setMode(e.target.value)} className="text-base font-medium bg-transparent border-0 focus:outline-none cursor-pointer">
              <option value="en-ru">English → Russian (Block + Cursive)</option>
              <option value="ru-cursive">Russian Keyboard → English (Block + Cursive)</option>
              <option value="phonetic">Latin-Phonetic → Russian (Block + Cursive)</option>
            </select>
          </div>
          {notice && (
            <div className="max-w-3xl mx-auto text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-4 py-2">
              ⚠️ {notice}
            </div>
          )}
        </header>

        {mode==='en-ru' && (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="card">
              <div className="card-header">
                <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
                  English Input
                </h2>
              </div>
              <div className="card-body space-y-4">
                <textarea value={en} onChange={e=>setEn(e.target.value)} className="textarea-field min-h-[140px]" placeholder="Type English..."/>
                <div className="flex flex-wrap gap-3">
                  <CopyButton text={en}/>
                </div>
              </div>
            </div>
            <div className="space-y-6">
              <div className="card">
                <div className="card-header flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-800">Russian — Block</h2>
                  <CopyButton text={transEnRu}/>
                </div>
                <div className="card-body">
                  <div lang="ru" className="text-2xl md:text-3xl p-4 rounded-xl bg-gradient-to-r from-gray-50 to-blue-50 border border-gray-100 break-words min-h-[80px] flex items-center">{transEnRu || ' '}</div>
                </div>
              </div>
              <CursiveRenderer text={transEnRu}/>
            </div>
          </div>
        )}

        {mode==='ru-cursive' && (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="space-y-6">
              <div className="card">
                <div className="card-header">
                  <h2 className="text-xl font-semibold text-gray-800">Russian Input</h2>
                </div>
                <div className="card-body space-y-4">
                  <textarea value={ru} onChange={e=>setRu(e.target.value)} className="textarea-field min-h-[120px]" lang="ru" placeholder="Напишите по-русски..."/>
                  <RussianKeyboard onKeyPress={(k)=>{ if(k==='BACKSPACE') setRu(p=>p.slice(0,-1)); else setRu(p=>p+k) }}/>
                  <CopyButton text={ru}/>
                </div>
              </div>
              <div className="card">
                <div className="card-header flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-800">English (Translated)</h3>
                  <CopyButton text={transRuEn}/>
                </div>
                <div className="card-body">
                  <div className="text-lg p-3 rounded-xl bg-gradient-to-r from-gray-50 to-green-50 border border-gray-100 break-words min-h-[60px]">{transRuEn || ' '}</div>
                </div>
              </div>
            </div>
            <div className="space-y-6">
              <div className="card">
                <div className="card-header flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-800">Russian — Block</h2>
                  <CopyButton text={ru}/>
                </div>
                <div className="card-body">
                  <div lang="ru" className="text-2xl md:text-3xl p-4 rounded-xl bg-gradient-to-r from-gray-50 to-blue-50 border border-gray-100 break-words">{ru || ' '}</div>
                </div>
              </div>
              <CursiveRenderer text={ru}/>
            </div>
          </div>
        )}

        {mode==='phonetic' && (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="card">
              <div className="card-header">
                <h2 className="text-xl font-semibold text-gray-800">Latin-Phonetic Input</h2>
              </div>
              <div className="card-body space-y-4">
                <textarea value={phon} onChange={e=>setPhon(e.target.value)} className="textarea-field min-h-[120px]" placeholder="privet mir"/>
                <PhoneticKeyboard onKeyPress={(k)=>setPhon(p=>p+k)}/>
                <CopyButton text={phon}/>
              </div>
            </div>
            <div className="space-y-6">
              <div className="card">
                <div className="card-header flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-800">Russian — Block</h2>
                  <CopyButton text={ru}/>
                </div>
                <div className="card-body">
                  <div lang="ru" className="text-2xl md:text-3xl p-4 rounded-xl bg-gradient-to-r from-gray-50 to-blue-50 border border-gray-100 break-words">{ru || ' '}</div>
                </div>
              </div>
              <CursiveRenderer text={ru}/>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
