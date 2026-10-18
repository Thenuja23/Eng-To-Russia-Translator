import React from 'react'

const PracticeSheet = ({ text = 'привет мир' }) => {
  return (
    <section className="card no-print-parent">
      <div className="card-header flex items-baseline justify-between gap-3">
        <div>
          <p className="eyebrow">Print</p>
          <h3 className="text-lg font-semibold tracking-tight text-gray-800 dark:text-gray-100 mt-0.5">
            Printable practice sheet
          </h3>
        </div>
        <button
          onClick={() => window.print()}
          className="btn-primary btn-sm no-print"
          type="button"
        >
          🖨 Print
        </button>
      </div>
      <div className="card-body">
        <div className="rounded-xl border border-dashed border-gray-300 dark:border-slate-600 p-6 bg-white/70 dark:bg-slate-900/60 print:border-0 print:p-0 print:bg-transparent">
          <div className="space-y-7">
            {[1, 2, 3].map((line) => (
              <div key={line}>
                <p
                  lang="ru"
                  className="font-['Bad_Script'] text-3xl leading-[2] text-gray-900 dark:text-gray-100"
                >
                  {text}
                </p>
                <div className="mt-2 h-px bg-blue-200/80 dark:bg-blue-500/40" />
                <div className="mt-4 h-px bg-gray-200 dark:bg-slate-700" />
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-4 text-center">
            Trace under the model line, then copy on your own
          </p>
        </div>
      </div>
    </section>
  )
}

export default PracticeSheet
