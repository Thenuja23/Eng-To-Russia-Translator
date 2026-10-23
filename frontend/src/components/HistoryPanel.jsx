import React, { useEffect, useState } from 'react'
import CopyButton from './CopyButton'
import {
  addHistoryEntry,
  clearHistory,
  downloadText,
  historyToCsv,
  loadHistory,
  removeHistoryEntry,
} from '../lib/history'

const DIRECTION_LABEL = {
  'en->ru': 'EN → RU',
  'ru->en': 'RU → EN',
}

function formatWhen(ts) {
  try {
    return new Date(ts).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return ''
  }
}

/**
 * Device-local translation history with Anki export.
 *
 * `current` is the visible translation ({ text, translation, src, tgt }); the
 * user decides when to keep it, so typing does not spam the list.
 */
export default function HistoryPanel({ current, onRestore }) {
  const [items, setItems] = useState(() => loadHistory())
  const [exported, setExported] = useState(false)

  // Keep the list in sync if another tab edited it.
  useEffect(() => {
    const onStorage = (event) => {
      if (!event.key || event.key === 'etr_history_v1') setItems(loadHistory())
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const canSave = Boolean(current?.text?.trim() && current?.translation?.trim())

  const saveCurrent = () => {
    if (!canSave) return
    setItems(addHistoryEntry(current))
  }

  const remove = (id) => setItems(removeHistoryEntry(id))

  const clearAll = () => {
    if (!items.length) return
    if (!window.confirm('Delete the whole translation history on this device?')) return
    setItems(clearHistory())
  }

  const exportCsv = () => {
    if (!items.length) return
    downloadText('cursive-ru-history.csv', historyToCsv(items), 'text/csv;charset=utf-8')
    setExported(true)
    setTimeout(() => setExported(false), 2000)
  }

  return (
    <section className="card">
      <div className="card-header flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="eyebrow">On this device</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            Translation history
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Saved in your browser only. Export it as CSV and import it into Anki for
            spaced repetition.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="btn-primary btn-sm"
            onClick={saveCurrent}
            disabled={!canSave}
            title={canSave ? 'Save the visible translation' : 'Translate something first'}
          >
            ＋ Save current
          </button>
          <button
            type="button"
            className="btn-ghost btn-sm"
            onClick={exportCsv}
            disabled={!items.length}
          >
            {exported ? '✓ Exported' : '⬇ Anki CSV'}
          </button>
          <button
            type="button"
            className="btn-ghost btn-sm"
            onClick={clearAll}
            disabled={!items.length}
          >
            Clear
          </button>
        </div>
      </div>

      <div className="card-body">
        {items.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Nothing saved yet. Keep a translation you like and it will appear here.
          </p>
        ) : (
          <ul className="divide-y divide-gray-200/80 dark:divide-slate-700/70">
            {items.map((item) => (
              <li key={item.id} className="py-3 flex flex-wrap items-start gap-3">
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="pill bg-gray-100 text-gray-600 border border-gray-200 dark:bg-slate-800 dark:text-gray-300 dark:border-slate-700">
                      {DIRECTION_LABEL[`${item.src}->${item.tgt}`] || `${item.src}→${item.tgt}`}
                    </span>
                    <span className="text-[11px] text-gray-500 dark:text-gray-400">
                      {formatWhen(item.ts)}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-100 break-words line-clamp-2">
                    {item.text}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-300 break-words line-clamp-2">
                    {item.translation}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {onRestore && (
                    <button
                      type="button"
                      className="btn-ghost btn-sm"
                      onClick={() => onRestore(item)}
                    >
                      Open
                    </button>
                  )}
                  <CopyButton text={item.translation} label="Copy" />
                  <button
                    type="button"
                    className="btn-ghost btn-sm"
                    onClick={() => remove(item.id)}
                    aria-label={`Delete history entry: ${item.text.slice(0, 40)}`}
                  >
                    ✕
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
