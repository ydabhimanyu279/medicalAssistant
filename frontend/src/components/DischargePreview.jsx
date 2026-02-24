import { useState } from 'react'
import { exportDischarge } from '../api/client'

export default function DischargePreview({ session, onClose }) {
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [preview, setPreview]   = useState(null)

  // Fetch discharge content from the backend for preview
  const loadPreview = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await exportDischarge(session.id)
      // Create a blob URL to show the PDF inline in the browser
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      setPreview(url)
    } catch {
      setError('Failed to load discharge preview. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Download the PDF directly
  const handleDownload = () => {
    const link = document.createElement('a')
    link.href  = preview
    link.setAttribute('download', `discharge_${session.id}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  // Load the preview when the modal first opens
  useState(() => {
    loadPreview()
  }, [])

  return (
    <div className="modal-overlay" onClick={onClose}>

      {/* Stop click from closing the modal when clicking inside */}
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>

        {/* Modal header */}
        <div className="modal-header">
          <div>
            <h2>Discharge Summary Preview</h2>
            <p className="session-id">Session: {session.title} — ID: {session.id}</p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {preview && (
              <button onClick={handleDownload} className="btn btn-primary">
                Download PDF
              </button>
            )}
            <button onClick={onClose} className="btn btn-secondary">
              Close
            </button>
          </div>
        </div>

        {/* Modal body */}
        <div className="modal-body">
          {error && <p className="error">{error}</p>}

          {loading ? (
            <div className="modal-loading">
              <p>Generating discharge summary, please wait...</p>
            </div>
          ) : preview ? (
            // Show the PDF inline using an iframe
            <iframe
              src={preview}
              title="Discharge Summary Preview"
              className="pdf-preview"
            />
          ) : null}
        </div>

      </div>
    </div>
  )
}