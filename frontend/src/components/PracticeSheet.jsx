import React from 'react'

const PracticeSheet = ({ text = 'привет мир' }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Printable Practice Sheet</h3>
      <button
        onClick={() => window.print()}
        className="mb-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 print:hidden"
        type="button"
      >
        Print
      </button>
      <div className="border border-dashed p-6 print:border-0 print:p-0">
        <div className="space-y-6">
          {[1, 2, 3].map((line) => (
            <div key={line}>
              <p lang="ru" className="font-['Bad_Script'] text-3xl leading-relaxed">{text}</p>
              <div className="mt-2 h-px bg-gray-300"></div>
              <div className="mt-2 h-px bg-gray-200"></div>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-4">Slanted school guideline lines (print-friendly)</p>
      </div>
    </div>
  )
}

export default PracticeSheet
