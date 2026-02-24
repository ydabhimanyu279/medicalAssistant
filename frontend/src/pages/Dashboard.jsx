import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { createSession, getSession, exportSession } from '../api/client'
import AudioRecorder from '../components/AudioRecorder'
import TranscriptPanel from '../components/TranscriptPanel'
import SuggestionCard from '../components/SuggestionCard'
import DischargePreview from '../components/DischargePreview'

export default function Dashboard() {
  const [session, setSession]             = useState(null)
  const [transcript, setTranscript]       = useState(null)
  const [suggestions, setSuggestions]     = useState([])
  const [loading, setLoading]             = useState(false)
  const [error, setError]                 = useState(null)
  const [showDischarge, setShowDischarge] = useState(false)
  const navigate                          = useNavigate()
  const [searchParams]                    = useSearchParams()

  // Load an existing session if session_id is in the URL, otherwise create a new one
  useEffect(() => {
    const sessionId = searchParams.get('session_id')
    if (sessionId) {
      loadExistingSession(parseInt(sessionId))
    } else {
      handleNewSession()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Load an existing session by ID including its transcripts and suggestions
  const loadExistingSession = async (id) => {
    setLoading(true)
    setError(null)
    try {
      const res = await getSession(id)
      setSession(res.data.session)
      setSuggestions(res.data.suggestions)
      // Show the last transcript if one exists
      if (res.data.transcripts.length > 0) {
        setTranscript(res.data.transcripts[res.data.transcripts.length - 1].text)
      }
    } catch {
      setError('Failed to load session.')
    } finally {
      setLoading(false)
    }
  }

  // Create a new consultation session
  const handleNewSession = async () => {
    setLoading(true)
    setError(null)
    setTranscript(null)
    setSuggestions([])
    try {
      const res = await createSession('New Consultation')
      setSession(res.data)
      // Update the URL without reloading the page
      navigate(`/?session_id=${res.data.id}`, { replace: true })
    } catch {
      setError('Failed to create a new session. Please refresh the page.')
    } finally {
      setLoading(false)
    }
  }

  // Called by AudioRecorder when Whisper returns the transcript
  const handleTranscriptReady = (text) => {
    setTranscript(text)
    setSuggestions([])
  }

  // Called by TranscriptPanel when the RAG pipeline returns suggestions
  const handleSuggestionsReady = (data) => {
    setSuggestions(data)
  }

  // Refresh the session data after the doctor submits feedback
  const handleFeedbackSubmitted = async () => {
    if (!session) return
    try {
      const res = await getSession(session.id)
      setSuggestions(res.data.suggestions)
    } catch {
      setError('Failed to refresh suggestions.')
    }
  }

  // Download the consultation report as a PDF
  const handleExport = async () => {
    try {
      const res  = await exportSession(session.id)
      const url  = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href  = url
      link.setAttribute('download', `session_${session.id}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch {
      setError('Failed to export session.')
    }
  }

  return (
    <div className="dashboard">

      {/* Header */}
      <div className="dashboard-header">
        <h1>MedAssist</h1>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => navigate('/history')} className="btn btn-secondary">
            Session History
          </button>
          <button onClick={handleNewSession} className="btn btn-secondary">
            New Consultation
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p>Loading session...</p>
      ) : session ? (
        <div className="dashboard-body">

          {/* Left panel — recording and transcript */}
          <div className="left-panel">
            <h2>Session: {session.title}</h2>
            <p className="session-id">ID: {session.id}</p>

            <button onClick={handleExport} className="btn btn-primary" style={{ marginBottom: '8px' }}>
              Export as PDF
            </button>
            <button onClick={() => setShowDischarge(true)} className="btn btn-accept" style={{ marginBottom: '16px' }}>
              Preview Discharge Summary
            </button>

            {/* Audio recorder component */}
            <AudioRecorder
              sessionId={session.id}
              onTranscriptReady={handleTranscriptReady}
            />

            {/* Transcript panel — only appears after recording */}
            <TranscriptPanel
              sessionId={session.id}
              transcript={transcript}
              onSuggestionsReady={handleSuggestionsReady}
            />
          </div>

          {/* Right panel — AI suggestions */}
          <div className="right-panel">
            <h2>AI Suggestions</h2>

            {suggestions.length === 0 ? (
              <p className="empty-state">
                Suggestions will appear here after the transcript is processed.
              </p>
            ) : (
              suggestions.map((s) => (
                <SuggestionCard
                  key={s.id}
                  suggestion={s}
                  onFeedbackSubmitted={handleFeedbackSubmitted}
                />
              ))
            )}
          </div>

        </div>
      ) : null}

      {/* Discharge preview modal */}
      {showDischarge && session && (
        <DischargePreview
          session={session}
          onClose={() => setShowDischarge(false)}
        />
      )}
    </div>
  )
}