import React, { useEffect, useState } from 'react'
import { applyTheme, getPreferredTheme, getStoredTheme, toggleTheme } from '../lib/theme'

/**
 * Light / dark theme switch.
 *
 * - Applies the theme by toggling the `dark` class on <html>.
 * - Remembers the user's explicit choice (localStorage).
 * - Until the user chooses, it follows the operating-system setting live.
 */
const ThemeToggle = ({ className = '' }) => {
  const [theme, setThemeState] = useState(getPreferredTheme)

  // Keep the document in sync with the current state.
  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  // While no explicit choice has been made, follow the OS setting.
  useEffect(() => {
    if (getStoredTheme()) return undefined
    let media
    try {
      media = window.matchMedia('(prefers-color-scheme: dark)')
    } catch {
      return undefined
    }
    const onChange = (event) => setThemeState(event.matches ? 'dark' : 'light')
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [])

  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={() => setThemeState((current) => toggleTheme(current))}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-pressed={isDark}
      className={
        'inline-flex items-center gap-2 h-9 px-3 rounded-full border border-gray-200 bg-white/80 text-sm font-medium text-gray-700 shadow-sm transition-colors duration-200 hover:bg-gray-50 dark:border-slate-700 dark:bg-slate-800/80 dark:text-gray-200 dark:hover:bg-slate-700 ' +
        (className || '')
      }
    >
      <span aria-hidden="true" className="text-base leading-none">
        {isDark ? '🌙' : '☀️'}
      </span>
      <span className="hidden sm:inline">{isDark ? 'Dark' : 'Light'}</span>
    </button>
  )
}

export default ThemeToggle
