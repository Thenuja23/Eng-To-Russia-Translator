/**
 * Clipboard utilities for text copying
 * Supports both modern clipboard API and fallback
 * Output is always real selectable text with user-select: text
 */

export async function copyToClipboard(text) {
  if (!text) return false
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    } else {
      // Fallback for non-secure contexts
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      textArea.style.userSelect = 'text'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      const successful = document.execCommand('copy')
      textArea.remove()
      return successful
    }
  } catch (err) {
    console.error('Copy failed:', err)
    return false
  }
}

export function copyBoth(text1, text2) {
  const combined = [text1, text2].filter(Boolean).join('\n\n')
  return copyToClipboard(combined)
}

export function copyAll(texts = []) {
  const combined = texts.filter(Boolean).join('\n\n')
  return copyToClipboard(combined)
}
