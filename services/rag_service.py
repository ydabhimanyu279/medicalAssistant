import os
import json
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# Initialize Pinecone client
pc    = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

# Load the same embedding model used during ingestion
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Connect LangChain to the Pinecone index
db = PineconeVectorStore(index=index, embedding=embeddings)

# Load the Groq LLM
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile",
)

def extract_symptoms(transcript: str) -> str:
    """Use the LLM to extract key symptoms and medical terms from the transcript."""
    prompt = f"""
You are a medical assistant. Extract all symptoms, medical conditions, and key clinical
terms from the following doctor-patient conversation transcript.
Return only a comma-separated list of terms, nothing else.

Transcript:
{transcript}
"""
    response = llm.invoke(prompt)
    return response.content.strip()

def retrieve_relevant_chunks(query: str, k: int = 5) -> list:
    """Search Pinecone for the most relevant knowledge base chunks."""
    results = db.similarity_search(query, k=k)
    return results

def generate_suggestions(transcript: str, chunks: list) -> list:
    """Use the LLM to generate structured suggestions based on the transcript and retrieved chunks."""

    context = "\n\n".join([doc.page_content for doc in chunks])

    prompt = f"""
You are a clinical decision support assistant helping a doctor during a consultation.
Based on the patient transcript and the medical knowledge provided, generate structured suggestions.

Return ONLY a valid JSON array with no extra text, no markdown, no explanation.
Each item in the array must have these exact fields:
- type: one of "diagnosis", "test", "drug", "red_flag"
- content: the suggestion text
- confidence: one of "high", "medium", "low"
- source_docs: a short description of the source used

Medical Knowledge:
{context}

Patient Transcript:
{transcript}

JSON array:
"""
    response = llm.invoke(prompt)
    raw      = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        suggestions = json.loads(raw)
    except json.JSONDecodeError:
        try:
            start       = raw.index("[")
            end         = raw.rindex("]") + 1
            suggestions = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            suggestions = [{
                "type":        "red_flag",
                "content":     "Could not parse AI suggestions. Please review the transcript manually.",
                "confidence":  "low",
                "source_docs": "N/A"
            }]

    return suggestions

def generate_discharge_content(transcript: str, chunks: list) -> dict:
    """Generate discharge summary content based on the transcript and retrieved chunks."""

    context = "\n\n".join([doc.page_content for doc in chunks])

    prompt = f"""You are a clinical decision support assistant helping a doctor write a discharge summary.
Based on the patient transcript and the medical knowledge provided, generate a structured discharge summary.

You MUST return ONLY a raw JSON object. No markdown, no code blocks, no backticks, no explanation, no preamble.
Start your response with {{ and end with }}.

The JSON object must have exactly these fields:
- "possible_cause": a string paragraph explaining the most likely underlying cause
- "prescribed_drugs": an array of strings, each being a drug name with dosage and frequency
- "followup_tests": an array of strings, each being a recommended test
- "followup_instructions": an array of strings, each being a patient instruction

Medical Knowledge:
{context}

Patient Transcript:
{transcript}
"""
    response = llm.invoke(prompt)
    raw      = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        content = json.loads(raw)
    except json.JSONDecodeError:
        try:
            start   = raw.index("{")
            end     = raw.rindex("}") + 1
            content = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            content = {
                "possible_cause":        "Could not generate cause analysis. Please review manually.",
                "prescribed_drugs":      [],
                "followup_tests":        [],
                "followup_instructions": []
            }

    return content

def run_rag_pipeline(transcript: str) -> list:
    """Run the full RAG pipeline — extract symptoms, retrieve chunks, generate suggestions."""

    symptoms    = extract_symptoms(transcript)
    print(f"Extracted symptoms: {symptoms}")

    chunks      = retrieve_relevant_chunks(symptoms, k=5)
    print(f"Retrieved {len(chunks)} chunks from Pinecone")

    suggestions = generate_suggestions(transcript, chunks)
    print(f"Generated {len(suggestions)} suggestions")

    return suggestions

def run_discharge_pipeline(transcript: str) -> dict:
    """Run the RAG pipeline specifically for generating discharge content."""

    symptoms = extract_symptoms(transcript)
    print(f"Extracted symptoms for discharge: {symptoms}")

    chunks   = retrieve_relevant_chunks(symptoms, k=5)
    print(f"Retrieved {len(chunks)} chunks for discharge")

    content  = generate_discharge_content(transcript, chunks)
    print("Discharge content generated")

    return content