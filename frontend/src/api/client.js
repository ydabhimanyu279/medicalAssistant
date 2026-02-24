import axios from 'axios'

// All requests go to the FastAPI backend via the Vite proxy
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Session endpoints
export const createSession = (title) => client.post('/sessions', { title })
export const getSessions   = ()      => client.get('/sessions')
export const getSession    = (id)    => client.get(`/sessions/${id}`)
export const deleteSession = (id)    => client.delete(`/sessions/${id}`)

// Transcription endpoint — sends audio as form data
export const transcribeAudio = (audioBlob, sessionId) => {
  const formData = new FormData()
  formData.append('file', audioBlob, 'recording.webm')
  formData.append('session_id', sessionId)
  return client.post('/transcribe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// Suggestions endpoint
export const getSuggestions = (sessionId) =>
  client.post('/suggestions', { session_id: sessionId })

// Feedback endpoint
export const submitFeedback = (suggestionId, status, doctorNote = null) =>
  client.post('/feedback', {
    suggestion_id: suggestionId,
    status,
    doctor_note: doctorNote,
  })

// Export a session as a PDF
export const exportSession = (id) =>
  client.get(`/sessions/${id}/export`, { responseType: 'blob' })

// Export a discharge summary as a PDF
export const exportDischarge = (id) =>
  client.get(`/sessions/${id}/discharge`, { responseType: 'blob' })