import React from 'react'

const FeedbackForm = () => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-md font-semibold mb-2">Feedback</h3>
      <textarea className="w-full border rounded p-2" placeholder="Report issues..." />
      <button className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm">Submit</button>
    </div>
  )
}

export default FeedbackForm
