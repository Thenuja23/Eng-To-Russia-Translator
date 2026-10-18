import React, { useState } from 'react'
import WritingPage from './pages/WritingPage'
import AlphabetChart from './components/AlphabetChart'
import TrapLetterDrills from './components/TrapLetterDrills'
import Flashcards from './components/Flashcards'
import PracticeSheet from './components/PracticeSheet'
import FontTest from './components/FontTest'
import TapWordView from './components/TapWordView'
import EditableOCRScreen from './components/EditableOCRScreen'

export default function App() {
  const [tab, setTab] = useState('write')
  const tabs = [
    {id:'write', label:'✍️ Write'},
    {id:'learn', label:'📚 Learn'},
    {id:'tools', label:'🛠️ Tools'},
    {id:'fonts', label:'🔤 Font Test'},
  ]
  return (
    <div className="min-h-screen">
      <nav className="bg-white/90 backdrop-blur-lg border-b border-white/50 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 md:px-6 flex gap-2 overflow-x-auto">
          {tabs.map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)} className={`py-3 px-4 text-sm md:text-base whitespace-nowrap border-b-2 font-medium transition-all duration-200 ${tab===t.id?'border-blue-600 text-blue-700':'border-transparent text-gray-600 hover:text-gray-900'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </nav>
      <main className="pb-12">
        {tab==='write' && <WritingPage/>}
        {tab==='learn' && (
          <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8">
            <AlphabetChart/>
            <TrapLetterDrills/>
            <Flashcards/>
            <PracticeSheet text="привет друг"/>
          </div>
        )}
        {tab==='tools' && (
          <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8">
            <TapWordView text="привет мир друг"/>
            <EditableOCRScreen initialText="привет мир"/>
          </div>
        )}
        {tab==='fonts' && (
          <div className="max-w-7xl mx-auto p-4 md:p-8">
            <FontTest/>
          </div>
        )}
      </main>
    </div>
  )
}
