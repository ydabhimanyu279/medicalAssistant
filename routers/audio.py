from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from db.database import get_db
from db import models
from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()

# Load the Groq client with the API key from .env
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

router = APIRouter()

# Accept an audio file and a session ID, transcribe with Whisper via Groq, and save to DB
@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    session_id: int  = Form(...),
    db: DBSession    = Depends(get_db)
):
    # Make sure the session exists before saving the transcript
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Read the audio bytes from the uploaded file
    audio_bytes = await file.read()

    try:
        # Send the audio to Whisper via Groq for transcription
        response = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(file.filename, audio_bytes, file.content_type),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    transcript_text = response.text

    # Save the transcript to the database linked to the session
    transcript = models.Transcript(
        session_id=session_id,
        text=transcript_text
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    return { "text": transcript_text, "transcript_id": transcript.id }