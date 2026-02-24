import { useState, useRef } from 'react'
import { transcribeAudio } from '../api/client'

export default function AudioRecorder({ sessionId, onTranscriptReady }) {
  const [recording, setRecording]   = useState(false)
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState(null)

  // Hold a reference to the MediaRecorder instance across renders
  const mediaRecorderRef = useRef(null)
  // Collect audio chunks as they come in during recording
  const audioChunksRef   = useRef([])

  // Start recording from the microphone
  const startRecording = async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current   = []

      // Collect audio data as it becomes available
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      // When recording stops, send the audio to Whisper
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        await sendToWhisper(audioBlob)

        // Stop all microphone tracks to release the mic
        stream.getTracks().forEach(t => t.stop())
      }

      mediaRecorder.start()
      setRecording(true)
    } catch {
      setError('Microphone access was denied. Please allow microphone access and try again.')
    }
  }

  // Stop the recording and trigger onstop
  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setRecording(false)
  }

  // Send the recorded audio blob to the FastAPI transcribe endpoint
  const sendToWhisper = async (audioBlob) => {
    setLoading(true)
    try {
      const res = await transcribeAudio(audioBlob, sessionId)
      // Pass the transcript text up to the parent component
      onTranscriptReady(res.data.text)
    } catch {
      setError('Transcription failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="recorder">
      {error && <p className="error">{error}</p>}

      {loading ? (
        <p>Transcribing audio, please wait...</p>
      ) : recording ? (
        <button onClick={stopRecording} className="btn btn-stop">
          Stop Recording
        </button>
      ) : (
        <button onClick={startRecording} className="btn btn-start">
          Start Recording
        </button>
      )}

      {recording && <p className="recording-indicator">Recording in progress...</p>}
    </div>
  )
}