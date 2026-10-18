import React, { useState } from 'react'

const CopyButton = ({ text, label = 'Copy' }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    if (!text) return
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text)
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        textArea.remove()
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Copy failed:', err)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className="btn-secondary"
      type="button"
      disabled={!text}
    >
      {copied ? '✓ Copied!' : `📋 ${label}`}
    </button>
  )
}

export const CopyAllButton = ({ texts = [], label = 'Copy All' }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const combined = texts.filter(Boolean).join('\n\n')
    if (!combined) return
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(combined)
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = combined
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        textArea.remove()
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Copy failed:', err)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className="btn-primary"
      type="button"
      disabled={texts.length === 0}
    >
      {copied ? '✓ Copied!' : `📋 ${label}`}
    </button>
  )
}

export const CopyBothButton = ({ text1, text2, label = 'Copy Both' }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const combined = [text1, text2].filter(Boolean).join('\n\n')
    if (!combined) return
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(combined)
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = combined
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        textArea.remove()
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Copy failed:', err)
    }
  }

  return (
    <button
      onClick={handleCopy}
      className="btn-secondary"
      type="button"
      disabled={!text1 && !text2}
    >
      {copied ? '✓ Copied!' : `📋 ${label}`}
    </button>
  )
}

export default CopyButton
