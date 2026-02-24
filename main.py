from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import Base, engine
from routers import audio, rag, sessions, feedback

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedAssist API", version="1.0.0")

# Allow all origins for now — will lock down to Vercel URL after frontend deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(audio.router,    prefix="/api", tags=["Audio"])
app.include_router(rag.router,      prefix="/api", tags=["RAG"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])

# Simple health check to confirm the server is running
@app.get("/")
def root():
    return {"status": "MedAssist API is running"}