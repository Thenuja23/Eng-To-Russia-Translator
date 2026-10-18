// Latin-phonetic -> Russian Cyrillic
// Handles multi-letter: shch, sch, zh, ch, sh, ts, yu, ya, yo, kh
export function latinToCyrillic(input) {
  if (!input) return ''
  let s = input.toLowerCase()
  const multi = [
    { from: 'shch', to: 'щ' },
    { from: 'sch',  to: 'щ' },
    { from: 'zh',   to: 'ж' },
    { from: 'ch',   to: 'ч' },
    { from: 'sh',   to: 'ш' },
    { from: 'ts',   to: 'ц' },
    { from: 'yu',   to: 'ю' },
    { from: 'ya',   to: 'я' },
    { from: 'yo',   to: 'ё' },
    { from: 'kh',   to: 'х' },
  ]
  for (let m of multi) {
    s = s.replaceAll(m.from, m.to)
  }
  const map = {
    a:'а', b:'б', v:'в', g:'г', d:'д', e:'е', z:'з', i:'и', y:'й', k:'к',
    l:'л', m:'м', n:'н', o:'о', p:'п', r:'р', s:'с', t:'т', u:'у', f:'ф',
    h:'х', j:'й', "'":'ь', '"':'ъ',
    q:'к', w:'в', x:'кс', c:'к'
  }
  let out = ''
  for (let i=0;i<s.length;i++) {
    out += map[s[i]] ?? s[i]
  }
  return out
}

export function cyrillicToLatin(input) {
  const map = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i','й':'y',
    'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f',
    'х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ъ':'"','ы':'y','ь':"'",'э':'e','ю':'yu','я':'ya',
    'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'Yo','Ж':'Zh','З':'Z','И':'I','Й':'Y',
    'К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F',
    'Х':'Kh','Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Shch','Ъ':'"','Ы':'Y','Ь':"'",'Э':'E','Ю':'Yu','Я':'Ya'
  }
  return input.split('').map(ch=>map[ch]??ch).join('')
}
