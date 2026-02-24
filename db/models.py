from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import enum

# Restrict feedback values to these four options only
class FeedbackStatus(str, enum.Enum):
    accepted = "accepted"
    rejected = "rejected"
    modified = "modified"
    pending  = "pending"

# Represents a single doctor-patient consultation
class Session(Base):
    __tablename__ = "sessions"

    id         = Column(Integer, primary_key=True, index=True)
    title      = Column(String(200), default="New Consultation")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Deleting a session also removes its transcripts and suggestions
    transcripts = relationship("Transcript", back_populates="session", cascade="all, delete")
    suggestions = relationship("Suggestion", back_populates="session", cascade="all, delete")

# Stores the transcribed text produced from the audio recording
class Transcript(Base):
    __tablename__ = "transcripts"

    id         = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    text       = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="transcripts")

# Stores each AI-generated suggestion linked to a session
class Suggestion(Base):
    __tablename__ = "suggestions"

    id          = Column(Integer, primary_key=True, index=True)
    session_id  = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    type        = Column(String(50))   # diagnosis | test | drug | red_flag
    content     = Column(Text)         # the suggestion text shown to the doctor
    confidence  = Column(String(20))   # high | medium | low
    source_docs = Column(Text)         # knowledge base chunks used to generate this
    status      = Column(Enum(FeedbackStatus), default=FeedbackStatus.pending)
    doctor_note = Column(Text, nullable=True)  # filled in if the doctor modifies the suggestion
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="suggestions")