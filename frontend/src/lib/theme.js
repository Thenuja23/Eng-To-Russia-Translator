/**
 * Light / dark theme handling.
 *
 * The choice is applied by toggling the `dark` class on <html>, which is what
 * Tailwind's `darkMode: 'class'` looks for. The preference is persisted in
 * localStorage; when the user has never chosen, the OS setting is used.
 */
export const THEME_KEY = 'etr-theme'

export const THEMES = ['light', 'dark']

const THEME_COLORS = { light: '#3b82f6', dark: '#0f172a' }

export function getStoredTheme() {
  try {
    const value = localStorage.getItem(THEME_KEY)
    return THEMES.includes(value) ? value : null
  } catch {
    return null
  }
}

export function getSystemTheme() {
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

/** Stored preference wins; otherwise follow the OS. */
export function getPreferredTheme() {
  return getStoredTheme() || getSystemTheme()
}

export function storeTheme(theme) {
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    /* private mode / storage disabled — the session still works */
  }
}

function syncThemeColorMeta(theme) {
  const meta = document.querySelector('meta[name="theme-color"]')
  if (meta) meta.setAttribute('content', THEME_COLORS[theme] || THEME_COLORS.light)
}

/** Apply the theme to the document without persisting it. */
export function applyTheme(theme) {
  const root = document.documentElement
  root.classList.toggle('dark', theme === 'dark')
  root.style.colorScheme = theme
  syncThemeColorMeta(theme)
}

/** Apply and remember the theme (used when the user presses the toggle). */
export function setTheme(theme) {
  storeTheme(theme)
  applyTheme(theme)
}

export function toggleTheme(current) {
  const next = current === 'dark' ? 'light' : 'dark'
  setTheme(next)
  return next
}
