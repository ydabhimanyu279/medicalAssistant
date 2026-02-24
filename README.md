# MedAssist — AI-Powered Clinical Decision Support System

Doctors spend a significant amount of time on documentation and clinical decision-making during consultations. MedAssist is a full-stack web application I built to help with that — it listens to doctor-patient conversations, transcribes them in real time, pulls relevant medical knowledge, and suggests possible diagnoses, tests, drugs, and red flags. When the consultation is done, it generates a discharge summary with one click.

## Live Demo

- **Frontend**: [https://medical-assistant-three.vercel.app](https://medical-assistant-three.vercel.app)
- **Backend API Docs**: [https://medicalassistant-production.up.railway.app/docs](https://medicalassistant-production.up.railway.app/docs)

---

## What It Does

**During a consultation**, the doctor hits record. The app captures the conversation and sends it to Whisper (via Groq) for transcription. Once transcribed, the doctor can request AI suggestions — the app extracts symptoms from the transcript, searches a medical knowledge base stored in Pinecone, and uses LLaMA 3.3 70B to generate structured clinical suggestions.

**Each suggestion** includes a type (diagnosis, recommended test, drug dosage, or red flag), a confidence level, and the source it was based on. The doctor can accept, reject, or modify each one before anything is finalized.

**At the end of the consultation**, the doctor can preview and download a discharge summary PDF that includes a possible cause analysis, prescribed drugs, follow-up tests, and patient instructions — all generated from the conversation.

---

## Features

- Record doctor-patient conversations directly in the browser
- Transcribe audio using Whisper (via Groq) — fast and accurate on medical terminology
- Extract symptoms and retrieve relevant knowledge from a vector database (Pinecone)
- Generate structured AI suggestions — diagnoses, tests, drugs, and red flags
- Accept, reject, or modify each suggestion with doctor notes
- Preview and export discharge summaries as PDFs
- Export full consultation reports as PDFs
- View and manage all past consultation sessions

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| FastAPI | REST API framework |
| PostgreSQL (Neon) | Persistent cloud database |
| SQLAlchemy | ORM for database models |
| Groq Whisper | Audio transcription |
| LangChain | RAG pipeline orchestration |
| Pinecone | Cloud vector database |
| Groq LLaMA 3.3 70B | LLM for suggestions and discharge summaries |
| ReportLab | PDF generation |

### Frontend
| Technology | Purpose |
|---|---|
| React + Vite | Frontend framework |
| Axios | API communication |
| React Router | Client-side routing |
| MediaRecorder API | Browser audio recording |

### Infrastructure
| Service | Purpose |
|---|---|
| Railway | Backend deployment |
| Vercel | Frontend deployment |
| Neon | Managed PostgreSQL |
| Pinecone | Managed vector database |

---

## How It Works

```
Browser (React)
    │
    ├── Record Audio → FastAPI /transcribe → Groq Whisper → Transcript
    │
    ├── Get Suggestions → FastAPI /suggestions
    │       │
    │       ├── Extract symptoms (Groq LLaMA)
    │       ├── Embed query (Pinecone Inference)
    │       ├── Retrieve chunks (Pinecone Vector DB)
    │       └── Generate suggestions (Groq LLaMA) → PostgreSQL
    │
    ├── Doctor Feedback → FastAPI /feedback → PostgreSQL
    │
    └── Export PDF → FastAPI /sessions/{id}/export or /discharge → ReportLab
```

---

## Knowledge Base

The RAG pipeline searches through **348 medical knowledge chunks** built from:
- **OpenFDA Drug Labels** — real drug data including indications, dosages, warnings, contraindications, adverse reactions, and drug interactions for 50 drugs

All chunks are embedded using Pinecone's `multilingual-e5-large` model and stored in a Pinecone serverless index.

---

## Running It Locally

### What you will need
- Python 3.13+
- Node.js 18+
- uv package manager
- Free accounts on Neon, Pinecone, and Groq

### Backend

```bash
# Clone the repo
git clone https://github.com/your-username/medassist.git
cd medassist

# Set up virtual environment
uv venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Install dependencies
uv add fastapi "uvicorn[standard]" sqlalchemy python-multipart pydantic \
    groq langchain langchain-community langchain-groq langchain-pinecone \
    langchain-text-splitters pinecone python-dotenv reportlab psycopg2-binary pypdf

# Add your environment variables to a .env file
DATABASE_URL=your_neon_connection_string
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=medassist

# Build the knowledge base (only needs to run once)
uv run python knowledge_base/ingest.py

# Start the server
uv run uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and you are good to go.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/sessions | Create a new consultation session |
| GET | /api/sessions | List all sessions |
| GET | /api/sessions/{id} | Get a session with transcripts and suggestions |
| DELETE | /api/sessions/{id} | Delete a session |
| POST | /api/transcribe | Upload audio and transcribe with Whisper |
| POST | /api/suggestions | Run RAG pipeline and generate suggestions |
| POST | /api/feedback | Submit doctor feedback on a suggestion |
| GET | /api/sessions/{id}/export | Export consultation report as PDF |
| GET | /api/sessions/{id}/discharge | Export discharge summary as PDF |

---

## Project Structure

```
medassist/
├── main.py                      # FastAPI app entry point
├── db/
│   ├── database.py              # PostgreSQL connection
│   └── models.py                # SQLAlchemy models
├── routers/
│   ├── audio.py                 # Whisper transcription endpoint
│   ├── rag.py                   # Suggestions endpoint
│   ├── sessions.py              # Session CRUD + PDF export
│   └── feedback.py              # Doctor feedback endpoint
├── services/
│   ├── rag_service.py           # RAG pipeline logic
│   ├── export_service.py        # Consultation PDF generation
│   └── discharge_service.py     # Discharge summary PDF generation
├── knowledge_base/
│   ├── ingest.py                # Knowledge base ingestion script
│   └── docs/                    # Raw documents
└── frontend/
    └── src/
        ├── api/client.js        # Axios API client
        ├── components/
        │   ├── AudioRecorder.jsx
        │   ├── TranscriptPanel.jsx
        │   ├── SuggestionCard.jsx
        │   └── DischargePreview.jsx
        └── pages/
            ├── Dashboard.jsx
            └── SessionHistory.jsx
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `GROQ_API_KEY` | Groq API key for Whisper and LLaMA |
| `PINECONE_API_KEY` | Pinecone API key |
| `PINECONE_INDEX` | Pinecone index name |

---

## License

MIT
