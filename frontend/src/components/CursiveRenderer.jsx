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
    <section className={`card ${className}`}>
      <div className="card-header flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="eyebrow">Handwriting</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5 flex items-center gap-2">
            <span aria-hidden="true">✒️</span> Cursive display
          </h3>
        </div>
        {showDownload && text.trim() && (
          <button onClick={handleDownload} className="btn-ghost btn-sm no-print" type="button">
            📥 Save as image
          </button>
        )}
      </div>
      <div className="card-body">
        {/* "Notebook paper" surface for the handwriting. */}
        <div
          ref={ref}
          className="rounded-xl border border-gray-200/80 dark:border-slate-700 p-6 shadow-inner
                     bg-[linear-gradient(180deg,#ffffff_0%,#fdfdfd_100%)]
                     dark:bg-[linear-gradient(180deg,#0f172a_0%,#111c33_100%)]
                     relative overflow-hidden"
        >
          {/* ruled lines */}
          <span
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-6 bottom-6 top-6
                       bg-[repeating-linear-gradient(180deg,transparent_0,transparent_43px,rgba(59,130,246,0.18)_43px,rgba(59,130,246,0.18)_44px)]
                       dark:bg-[repeating-linear-gradient(180deg,transparent_0,transparent_43px,rgba(96,165,250,0.22)_43px,rgba(96,165,250,0.22)_44px)]"
          />
          {/* red margin line, like school paper */}
          <span
            aria-hidden="true"
            className="pointer-events-none absolute inset-y-4 left-10 w-px bg-red-300/60 dark:bg-red-400/40"
          />
          <div
            lang="ru"
            className={`cursive-text ${selectedStyle} break-words text-center relative z-10
                        text-gray-900 dark:text-gray-100`}
            style={{ minHeight: '80px', userSelect: 'text' }}
          >
            {text || ' '}
          </div>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-3 text-center">
          Cursive is a font — copied text stays normal Cyrillic
        </p>
      </div>
    </section>
  )
}

export default CursiveRenderer
