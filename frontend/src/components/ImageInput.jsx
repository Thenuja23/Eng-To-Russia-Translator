import React, { useEffect, useRef, useState } from 'react'
import { ocrImage } from '../lib/api'

/**
 * "Upload an image" / "Take a photo" input for Russian text.
 *
 * Both buttons open a file picker; the camera one sets `capture` so phones
 * launch the camera directly. The recognised text is handed to
 * `onTextExtracted` (the page puts it in the Russian textarea so the user can
 * fix OCR mistakes before translating — OCR of cursive is imperfect).
 */
const ENGINE_NAMES = { pytesseract: 'Tesseract', easyocr: 'EasyOCR' }

function engineLabel(engine) {
  const [name, variant] = engine.split('/')
  const label = ENGINE_NAMES[name] || name
  return variant ? `${label} (${variant} image)` : label
}

const ImageInput = ({ onTextExtracted, onError, onLoading }) => {
  const fileInput = useRef(null)
  const cameraInput = useRef(null)
  const previewUrl = useRef(null) // tracked so we can revoke object URLs
  const [preview, setPreview] = useState(null)
  const [engine, setEngine] = useState('')

  // Replace the current preview, revoking the old object URL first.
  const storePreview = (file) => {
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
    previewUrl.current = URL.createObjectURL(file)
    setPreview(previewUrl.current)
  }

  // Remove the attached / captured image. The recognised text is kept —
  // the user may have already edited it.
  const clearImage = () => {
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
    previewUrl.current = null
    setPreview(null)
    setEngine('')
    onError?.('')
  }

  // Free the object URL when the component goes away.
  useEffect(() => () => {
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current)
  }, [])

  const handleFiles = async (files, inputEl) => {
    const file = files && files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      onError?.('Please choose an image file (JPG/PNG).')
      return
    }
    storePreview(file)
    onError?.('')
    onLoading?.(true)
    try {
      const { text, engine: used } = await ocrImage(file)
      setEngine(used && used !== 'none' ? used : '')
      if (text && text.trim()) {
        onTextExtracted(text)
      } else {
        onError?.('No text found in that image. Try a clearer, closer photo.')
      }
    } catch (e) {
      onError?.(e.message)
    } finally {
      onLoading?.(false)
      if (inputEl) inputEl.value = '' // allow re-selecting the same file
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 items-center">
        <input
          ref={fileInput}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files, e.target)}
        />
        <input
          ref={cameraInput}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files, e.target)}
        />
        <button type="button" onClick={() => fileInput.current?.click()} className="btn-secondary">
          📁 Upload image
        </button>
        <button type="button" onClick={() => cameraInput.current?.click()} className="btn-secondary">
          📷 Take photo
        </button>
        {preview && (
          <span className="relative inline-flex">
            <img
              src={preview}
              alt="Uploaded for text recognition"
              className="h-12 w-12 object-cover rounded-lg border border-gray-200 dark:border-slate-700"
            />
            <button
              type="button"
              onClick={clearImage}
              aria-label="Remove image"
              title="Remove image"
              className="absolute -top-2 -right-2 h-6 w-6 grid place-items-center rounded-full
                         bg-white text-gray-600 border border-gray-300 shadow-sm
                         hover:bg-red-50 hover:text-red-600 hover:border-red-300
                         dark:bg-slate-800 dark:text-gray-300 dark:border-slate-600
                         dark:hover:bg-red-950 dark:hover:text-red-300 dark:hover:border-red-800
                         transition-colors duration-150
                         focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <span aria-hidden="true" className="text-xs leading-none font-bold">✕</span>
            </button>
          </span>
        )}
      </div>
      {preview && (
        <button
          type="button"
          onClick={clearImage}
          className="btn-ghost btn-sm !text-red-600 dark:!text-red-300 hover:!bg-red-50 dark:hover:!bg-red-950/50"
        >
          🗑 Remove image
        </button>
      )}
      {engine && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Recognised by {engineLabel(engine)}. Check the text below and fix any mistakes
          before copying.
        </p>
      )}
    </div>
  )
}

export default ImageInput
