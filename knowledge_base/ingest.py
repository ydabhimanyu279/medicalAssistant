import requests
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import io
import time

load_dotenv()

# Where WHO PDFs will be saved locally
DOCS_PATH = os.path.join(os.path.dirname(__file__), "docs")

# OpenFDA API endpoint for drug label information
OPENFDA_URL = "https://api.fda.gov/drug/label.json"

# Free WHO guideline PDFs — publicly available
WHO_PDFS = [
    {
        "url":   "https://iris.who.int/bitstream/handle/10665/44016/9789241547925_eng.pdf",
        "title": "WHO Pocket Book of Hospital Care for Children"
    },
    {
        "url":   "https://iris.who.int/bitstream/handle/10665/255052/9789241512442-eng.pdf",
        "title": "WHO Guidelines for the Treatment of Malaria"
    },
]

# ----------------------------------------------------------------
# OpenFDA
# ----------------------------------------------------------------

def fetch_openfda_drugs(limit=50):
    """Fetch drug label data from the OpenFDA API."""
    print(f"Fetching {limit} drug records from OpenFDA...")
    params   = { "limit": limit, "skip": 0 }
    response = requests.get(OPENFDA_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])

def parse_drug_to_text(drug):
    """Convert a raw OpenFDA drug record into a readable text chunk."""
    sections = []

    openfda = drug.get("openfda", {})
    brand   = openfda.get("brand_name",   ["Unknown"])[0]
    generic = openfda.get("generic_name", ["Unknown"])[0]
    sections.append(f"Drug: {brand} ({generic})")

    fields = {
        "indications_and_usage":     "Indications and Usage",
        "dosage_and_administration": "Dosage and Administration",
        "warnings":                  "Warnings",
        "contraindications":         "Contraindications",
        "adverse_reactions":         "Adverse Reactions",
        "drug_interactions":         "Drug Interactions",
    }

    for key, label in fields.items():
        value = drug.get(key)
        if value and isinstance(value, list):
            sections.append(f"{label}:\n{value[0][:500]}")

    return "\n\n".join(sections)

def load_openfda_documents():
    """Fetch drugs from OpenFDA and convert them into LangChain Document objects."""
    drugs = fetch_openfda_drugs(limit=50)
    docs  = []
    for drug in drugs:
        text = parse_drug_to_text(drug)
        if text.strip():
            docs.append(Document(
                page_content=text,
                metadata={"source": "OpenFDA", "type": "drug_label"}
            ))
    print(f"Loaded {len(docs)} drug documents from OpenFDA")
    return docs

# ----------------------------------------------------------------
# Chunking and Storing in Pinecone
# ----------------------------------------------------------------

def build_knowledge_base():
    """Fetch all sources, chunk the text, embed with Pinecone inference, and store."""

    # Load documents
    openfda_docs = load_openfda_documents()
    all_docs     = openfda_docs

    print(f"\nTotal documents loaded: {len(all_docs)}")

    # Split into smaller chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(all_docs)
    print(f"Total chunks after splitting: {len(chunks)}")

    # Initialize Pinecone
    pc         = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX")
    existing   = [i.name for i in pc.list_indexes()]

    # Create index if it does not exist
    if index_name not in existing:
        print(f"Creating Pinecone index: {index_name}...")
        pc.create_index(
            name=index_name,
            dimension=1024,  # dimension for multilingual-e5-large
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        # Wait for the index to be ready
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)
        print("Index created.")
    else:
        print(f"Index '{index_name}' already exists.")

    index = pc.Index(index_name)

    # Embed and store chunks in batches of 50
    print("Embedding and storing chunks in Pinecone...")
    batch_size = 50
    texts      = [c.page_content for c in chunks]

    for i in range(0, len(texts), batch_size):
        batch  = texts[i:i + batch_size]
        # Embed the batch using Pinecone inference
        embeddings = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=batch,
            parameters={"input_type": "passage"}
        )
        # Prepare vectors with metadata
        vectors = []
        for j, (text, embedding) in enumerate(zip(batch, embeddings)):
            vectors.append({
                "id":       f"chunk-{i + j}",
                "values":   embedding.values,
                "metadata": {"text": text}
            })
        index.upsert(vectors=vectors)
        print(f"Stored chunks {i + 1} to {min(i + batch_size, len(texts))}")

    print(f"\nKnowledge base built successfully.")
    print(f"Total chunks stored: {len(chunks)}")

if __name__ == "__main__":
    build_knowledge_base()