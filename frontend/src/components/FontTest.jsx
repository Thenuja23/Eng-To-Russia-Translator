import React from 'react'

/**
 * FontTest - Tests cursive fonts on pangram and trap letters
 * Pangram: "Съешь же ещё этих мягких французских булок, да выпей чаю"
 * Trap letters: т, м, д, г, и, п, б, ш (as specified)
 */
const FontTest = () => {
  const pangram = 'Съешь же ещё этих мягких французских булок, да выпей чаю'
  const trapLetters = 'т м д г и п б ш Т М Д Г И П Б Ш'
  
  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-4">
      <h3 className="text-md font-semibold text-gray-700">Font Test (Pangram & Trap Letters)</h3>
      
      <div className="space-y-3">
        <div>
          <p className="text-sm text-gray-600 mb-1">Bad Script:</p>
          <p lang="ru" className="font-['Bad_Script'] text-xl leading-relaxed break-words">
            {pangram}<br/>{trapLetters}
          </p>
        </div>
        
        <div>
          <p className="text-sm text-gray-600 mb-1">Marck Script:</p>
          <p lang="ru" className="font-['Marck_Script'] text-xl leading-relaxed break-words">
            {pangram}<br/>{trapLetters}
          </p>
        </div>
        
        <div>
          <p className="text-sm text-gray-600 mb-1">Caveat:</p>
          <p lang="ru" className="font-['Caveat'] text-xl leading-relaxed break-words">
            {pangram}<br/>{trapLetters}
          </p>
        </div>
        
        <div>
          <p className="text-sm text-gray-600 mb-1">Fallback (italic):</p>
          <p lang="ru" className="italic text-xl leading-relaxed break-words">
            {pangram}<br/>{trapLetters}
          </p>
        </div>
      </div>
      
      <p className="text-xs text-gray-500">
        Note: Reject fonts that look like italic print. Cursive is a font - copied text stays normal Cyrillic.
      </p>
    </div>
  )
}

export default FontTest
