import { useState } from 'react'
import { getSuggestions } from '../api/client'

export default function TranscriptPanel({ sessionId, transcript, onSuggestionsReady }) {
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  // Send the transcript to the RAG pipeline and get AI suggestions back
  const handleGetSuggestions = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getSuggestions(sessionId)
      // Pass the suggestions up to the parent component
      onSuggestionsReady(res.data.suggestions)
    } catch {
      setError('Failed to generate suggestions. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Nothing to show if there is no transcript yet
  if (!transcript) return null

  return (
    <div className="transcript-panel">
      <h3>Transcript</h3>

      {/* Display the transcribed text from Whisper */}
      <div className="transcript-text">
        <p>{transcript}</p>
      </div>

      {error && <p className="error">{error}</p>}

      {/* Once the doctor reviews the transcript, they can request AI suggestions */}
      <button
        onClick={handleGetSuggestions}
        disabled={loading}
        className="btn btn-primary"
      >
        {loading ? 'Generating suggestions...' : 'Get AI Suggestions'}
      </button>
    </div>
  )
}