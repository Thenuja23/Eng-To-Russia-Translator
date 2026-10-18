export async function downloadElementAsPng(element, filename = 'cursive.png') {
  if (!element) return
  try {
    const { toPng } = await import('html-to-image')
    const dataUrl = await toPng(element, { quality: 1, pixelRatio: 2 })
    const link = document.createElement('a')
    link.href = dataUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (e) {
    console.error('Download failed', e)
    alert('Download failed. Try copying text instead.')
  }
}
