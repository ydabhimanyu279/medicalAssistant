from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from db.database import get_db
from db import models
from pydantic import BaseModel
from typing import Optional
from services.export_service import generate_session_pdf
from services.discharge_service import generate_discharge_pdf
from services.rag_service import run_discharge_pipeline
import io

router = APIRouter()

# Define what data is accepted when creating a session
class SessionCreate(BaseModel):
    title: Optional[str] = "New Consultation"

# Define what data is accepted when updating a session title
class SessionUpdate(BaseModel):
    title: str

# Create a new consultation session
@router.post("/sessions")
def create_session(body: SessionCreate, db: DBSession = Depends(get_db)):
    session = models.Session(title=body.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

# Get all sessions, newest first
@router.get("/sessions")
def get_sessions(db: DBSession = Depends(get_db)):
    return db.query(models.Session).order_by(models.Session.created_at.desc()).all()

# Get a single session with its transcripts and suggestions
@router.get("/sessions/{session_id}")
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    s = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session": s,
        "transcripts": s.transcripts,
        "suggestions": s.suggestions
    }

# Update the title of an existing session
@router.put("/sessions/{session_id}")
def update_session(session_id: int, body: SessionUpdate, db: DBSession = Depends(get_db)):
    s = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    s.title = body.title
    db.commit()
    db.refresh(s)
    return s

# Delete a session and all its related transcripts and suggestions
@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    s = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(s)
    db.commit()
    return {"message": "Session deleted successfully"}

# Export a session as a PDF report
@router.get("/sessions/{session_id}/export")
def export_session(session_id: int, db: DBSession = Depends(get_db)):
    s = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    pdf_bytes = generate_session_pdf(s, s.transcripts, s.suggestions)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=session_{session_id}.pdf"
        }
    )

# Generate and export a discharge summary PDF for a session
@router.get("/sessions/{session_id}/discharge")
def export_discharge(session_id: int, db: DBSession = Depends(get_db)):
    s = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the latest transcript for this session
    transcript = (
        db.query(models.Transcript)
        .filter(models.Transcript.session_id == session_id)
        .order_by(models.Transcript.created_at.desc())
        .first()
    )

    if not transcript:
        raise HTTPException(status_code=404, detail="No transcript found for this session")

    # Run the discharge RAG pipeline
    discharge_content = run_discharge_pipeline(transcript.text)

    # Generate the discharge PDF
    pdf_bytes = generate_discharge_pdf(s, transcript.text, discharge_content)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=discharge_{session_id}.pdf"
        }
    )