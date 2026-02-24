from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from db.database import get_db
from db import models
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Define what data is accepted when the doctor submits feedback
class FeedbackBody(BaseModel):
    suggestion_id: int
    status: models.FeedbackStatus
    doctor_note: Optional[str] = None

# Submit feedback for a single suggestion
@router.post("/feedback")
def submit_feedback(body: FeedbackBody, db: DBSession = Depends(get_db)):
    suggestion = db.query(models.Suggestion).filter(
        models.Suggestion.id == body.suggestion_id
    ).first()

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    # Update the status and optional doctor note
    suggestion.status      = body.status
    suggestion.doctor_note = body.doctor_note

    db.commit()
    db.refresh(suggestion)
    return suggestion

# Get all feedback for a specific session
@router.get("/feedback/{session_id}")
def get_feedback(session_id: int, db: DBSession = Depends(get_db)):
    suggestions = db.query(models.Suggestion).filter(
        models.Suggestion.session_id == session_id
    ).all()

    if not suggestions:
        raise HTTPException(status_code=404, detail="No suggestions found for this session")

    return suggestions