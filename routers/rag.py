from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from db.database import get_db
from db import models
from services.rag_service import run_rag_pipeline
from pydantic import BaseModel

router = APIRouter()

class SuggestionsRequest(BaseModel):
    session_id: int

# Run the RAG pipeline on the latest transcript for a session
@router.post("/suggestions")
def get_suggestions(body: SuggestionsRequest, db: DBSession = Depends(get_db)):

    # Get the latest transcript for this session
    transcript = (
        db.query(models.Transcript)
        .filter(models.Transcript.session_id == body.session_id)
        .order_by(models.Transcript.created_at.desc())
        .first()
    )

    if not transcript:
        raise HTTPException(status_code=404, detail="No transcript found for this session")

    # Run the full RAG pipeline
    suggestions_data = run_rag_pipeline(transcript.text)

    # Save each suggestion to the database, skip empty or invalid ones
    saved = []
    for s in suggestions_data:
        # Skip suggestions that are missing required fields
        if not s.get("content") or not s.get("type"):
            continue
        suggestion = models.Suggestion(
            session_id  = body.session_id,
            type        = s.get("type",        "diagnosis"),
            content     = s.get("content",     ""),
            confidence  = s.get("confidence",  "medium"),
            source_docs = s.get("source_docs", ""),
        )
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)
        saved.append(suggestion)

    return { "suggestions": saved }