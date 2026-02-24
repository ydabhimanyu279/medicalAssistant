from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import Base, engine
from routers import audio, rag, sessions, feedback

# Create the database tables when the server starts
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MedAssist API", version="1.0.0")

# Allow the React frontend on port 5173 to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect each router to the app under the /api prefix
app.include_router(audio.router,    prefix="/api", tags=["Audio"])
app.include_router(rag.router,      prefix="/api", tags=["RAG"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])

# Simple health check to confirm the server is running
@app.get("/")
def root():
    return {"status": "MedAssist API is running"}