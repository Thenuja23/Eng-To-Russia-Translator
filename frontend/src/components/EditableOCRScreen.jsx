import React, { useState, useEffect } from 'react'
import CopyButton from './CopyButton'

/**
 * Editable OCR review screen.
 * The user can correct the recognised text line by line before it is used.
 */
const EditableOCRScreen = ({ initialText = '', onSave }) => {
  const [lines, setLines] = useState(() => initialText.split('\n'))
  const [status, setStatus] = useState(null) // null | 'saved'
  const [dirty, setDirty] = useState(false)

  // Re-sync when the parent supplies a new OCR result.
  useEffect(() => {
    setLines(initialText.split('\n'))
    setDirty(false)
    setStatus(null)
  }, [initialText])

  const text = lines.join('\n')

  const handleLineChange = (idx, value) => {
    setLines((prev) => {
      const next = [...prev]
      next[idx] = value
      return next
    })
    setDirty(true)
    setStatus(null)
  }

  const handleSave = () => {
    if (onSave) onSave(text)
    setDirty(false)
    setStatus('saved')
  }

  return (
    <section className="card">
      <div className="card-header flex items-center justify-between gap-3">
        <div>
          <p className="eyebrow">Review</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            Editable OCR result
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {dirty && (
            <span className="pill hidden sm:inline-flex bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-900">
              unsaved
            </span>
          )}
          <CopyButton text={text} />
        </div>
      </div>
      <div className="card-body space-y-3">
        {lines.map((line, idx) => (
          <div key={idx} className="flex items-start gap-2">
            <span
              aria-hidden="true"
              className="mt-2.5 w-6 text-right text-[11px] font-medium text-gray-500 tabular-nums select-none"
            >
              {idx + 1}
            </span>
            <textarea
              value={line}
              onChange={(e) => handleLineChange(idx, e.target.value)}
              className="textarea-field !min-h-[48px] !text-sm !py-2 flex-1"
              lang="ru"
              aria-label={`OCR line ${idx + 1}`}
              rows={1}
            />
          </div>
        ))}
        <div className="flex items-center gap-3 pt-1">
          <button onClick={handleSave} className="btn-primary btn-sm" type="button">
            Save edits
          </button>
          <span aria-live="polite" className="text-sm">
            {status === 'saved' && (
              <span className="text-green-700 dark:text-green-400 font-medium">✓ Edits saved</span>
            )}
          </span>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Saved text feeds the tap-a-word reader above.
        </p>
      </div>
    </section>
  )
}

export default EditableOCRScreen
