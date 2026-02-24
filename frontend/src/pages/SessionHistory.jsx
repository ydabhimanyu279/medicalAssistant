import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSessions, deleteSession } from '../api/client'

export default function SessionHistory() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)
  const navigate                = useNavigate()

  // Load all sessions when the page mounts
  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    setLoading(true)
    try {
      const res = await getSessions()
      setSessions(res.data)
    } catch {
      setError('Failed to load sessions.')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteSession(id)
      // Remove the deleted session from the list without refetching
      setSessions(prev => prev.filter(s => s.id !== id))
    } catch {
      setError('Failed to delete session.')
    }
  }

  // Format the date to a readable string
  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString()
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Session History</h1>
        <button onClick={() => navigate('/')} className="btn btn-secondary">
          Back to Dashboard
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p>Loading sessions...</p>
      ) : sessions.length === 0 ? (
        <p className="empty-state">No sessions found.</p>
      ) : (
        <div className="session-list">
          {sessions.map(s => (
            <div key={s.id} className="session-item">
              <div className="session-info">
                <h3>{s.title}</h3>
                <p className="session-date">{formatDate(s.created_at)}</p>
                <p className="session-id">ID: {s.id}</p>
              </div>
              <div className="session-actions">
                <button
                  onClick={() => navigate(`/?session_id=${s.id}`)}
                  className="btn btn-primary"
                >
                  View
                </button>
                <button
                  onClick={() => handleDelete(s.id)}
                  className="btn btn-reject"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}