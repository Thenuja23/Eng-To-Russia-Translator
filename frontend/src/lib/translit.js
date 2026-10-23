// Cyrillic → Latin reading aid for English speakers.
// This is a display convenience only; it is not a linguistic standard.

const MAP = {
  а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ё: 'yo', ж: 'zh',
  з: 'z', и: 'i', й: 'y', к: 'k', л: 'l', м: 'm', н: 'n', о: 'o',
  п: 'p', р: 'r', с: 's', т: 't', у: 'u', ф: 'f', х: 'kh', ц: 'ts',
  ч: 'ch', ш: 'sh', щ: 'shch', ъ: '', ы: 'y', ь: '', э: 'e', ю: 'yu',
  я: 'ya',
}

export function transliterate(text) {
  return Array.from(text || '')
    .map((ch) => {
      const lower = ch.toLowerCase()
      const mapped = MAP[lower]
      if (mapped === undefined) return ch
      if (!mapped) return ''
      return ch !== lower ? mapped.charAt(0).toUpperCase() + mapped.slice(1) : mapped
    })
    .join('')
}
