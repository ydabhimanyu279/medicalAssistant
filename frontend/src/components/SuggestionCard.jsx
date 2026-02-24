import { useState } from 'react'
import { submitFeedback } from '../api/client'

export default function SuggestionCard({ suggestion, onFeedbackSubmitted }) {
  const [status, setStatus]       = useState(suggestion.status)
  const [doctorNote, setDoctorNote] = useState(suggestion.doctor_note || '')
  const [editing, setEditing]     = useState(false)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)

  // Submit the doctor's feedback for this suggestion
  const handleFeedback = async (newStatus) => {
    setLoading(true)
    setError(null)
    try {
      await submitFeedback(suggestion.id, newStatus, doctorNote || null)
      setStatus(newStatus)
      setEditing(false)
      // Notify the parent that feedback was submitted
      onFeedbackSubmitted()
    } catch {
      setError('Failed to submit feedback. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Map suggestion type to a readable label
  const typeLabels = {
    diagnosis: 'Diagnosis',
    test:      'Recommended Test',
    drug:      'Drug / Dosage',
    red_flag:  'Red Flag',
  }

  // Map confidence level to a visual indicator
  const confidenceColors = {
    high:   '#22c55e',
    medium: '#f59e0b',
    low:    '#ef4444',
  }

  return (
    <div className={`suggestion-card status-${status}`}>

      {/* Header row — type label and confidence indicator */}
      <div className="card-header">
        <span className="suggestion-type">{typeLabels[suggestion.type] || suggestion.type}</span>
        <span
          className="confidence-badge"
          style={{ color: confidenceColors[suggestion.confidence] }}
        >
          {suggestion.confidence} confidence
        </span>
      </div>

      {/* The actual suggestion content */}
      <p className="suggestion-content">{suggestion.content}</p>

      {/* Show which knowledge base chunks were used */}
      {suggestion.source_docs && (
        <p className="source-docs">Source: {suggestion.source_docs}</p>
      )}

      {/* Doctor note input — only visible when modifying */}
      {editing && (
        <textarea
          className="doctor-note-input"
          placeholder="Write your modification here..."
          value={doctorNote}
          onChange={(e) => setDoctorNote(e.target.value)}
          rows={3}
        />
      )}

      {error && <p className="error">{error}</p>}

      {/* Feedback controls — only show if still pending */}
      {status === 'pending' && (
        <div className="feedback-controls">
          <button
            onClick={() => handleFeedback('accepted')}
            disabled={loading}
            className="btn btn-accept"
          >
            Accept
          </button>

          <button
            onClick={() => setEditing(!editing)}
            disabled={loading}
            className="btn btn-modify"
          >
            {editing ? 'Cancel' : 'Modify'}
          </button>

          {editing && (
            <button
              onClick={() => handleFeedback('modified')}
              disabled={loading || !doctorNote}
              className="btn btn-save"
            >
              Save Modification
            </button>
          )}

          <button
            onClick={() => handleFeedback('rejected')}
            disabled={loading}
            className="btn btn-reject"
          >
            Reject
          </button>
        </div>
      )}

      {/* Show the final status once feedback is given */}
      {status !== 'pending' && (
        <div className="feedback-status">
          <span>Status: {status}</span>
          {doctorNote && <p className="doctor-note">Note: {doctorNote}</p>}
        </div>
      )}
    </div>
  )
}