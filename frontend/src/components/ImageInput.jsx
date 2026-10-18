import React, { useRef, useState } from 'react'
import { ocrImage } from '../lib/api'

/**
 * "Upload an image" / "Take a photo" input for Russian text.
 *
 * Both buttons open a file picker; the camera one sets `capture` so phones
 * launch the camera directly. The recognised text is handed to
 * `onTextExtracted` (the page puts it in the Russian textarea so the user can
 * fix OCR mistakes before translating — OCR of cursive is imperfect).
 */
const ImageInput = ({ onTextExtracted, onError, onLoading }) => {
  const fileInput = useRef(null)
  const cameraInput = useRef(null)
  const [preview, setPreview] = useState(null)
  const [engine, setEngine] = useState('')

  const handleFiles = async (files, inputEl) => {
    const file = files && files[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      onError?.('Please choose an image file (JPG/PNG).')
      return
    }
    setPreview(URL.createObjectURL(file))
    onError?.('')
    onLoading?.(true)
    try {
      const { text, engine: used } = await ocrImage(file)
      setEngine(used || '')
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
          <img
            src={preview}
            alt="Uploaded for text recognition"
            className="h-12 w-12 object-cover rounded-lg border border-gray-200 dark:border-slate-700"
          />
        )}
      </div>
      {engine && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Recognised by {engine.replace('/', ' — ')}. Check the text below and fix any mistakes
          before copying.
        </p>
      )}
    </div>
  )
}

export default ImageInput
