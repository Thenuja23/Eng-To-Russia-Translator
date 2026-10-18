import React, { useRef } from 'react'
import { downloadElementAsPng } from '../lib/downloadAsImage'

const CursiveRenderer = ({ text = '', style = 'cursive1', className = '', showDownload = true }) => {
  const ref = useRef(null)
  const fontStyles = {
    cursive1: 'font-["Bad_Script"]',
    cursive2: 'font-["Marck_Script"]',
    cursive3: 'font-["Caveat"]',
    cursive4: 'font-serif italic',
  }
  const selectedStyle = fontStyles[style] || fontStyles.cursive1

  const handleDownload = async () => {
    if (ref.current && text.trim()) await downloadElementAsPng(ref.current, 'russian-cursive.png')
  }

  return (
    <div className={`card ${className}`}>
      <div className="card-header flex items-center justify-between">
        <h3 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
          <span className="text-2xl">✒️</span> Cursive Display
        </h3>
        <div className="flex gap-2">
          {showDownload && text.trim() && (
            <button onClick={handleDownload} className="btn-ghost text-sm">
              📥 Download as image
            </button>
          )}
        </div>
      </div>
      <div className="card-body">
        <div ref={ref} className="p-6 rounded-xl bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 border border-white/50">
          <div
            lang="ru"
            className={`cursive-text ${selectedStyle} break-words text-center`}
            style={{ minHeight: '80px', userSelect: 'text' }}
          >
            {text || ' '}
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-3 text-center">Cursive is a font — copied text stays normal Cyrillic</p>
      </div>
    </div>
  )
}

export default CursiveRenderer
