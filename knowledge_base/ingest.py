import requests
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec
from pypdf import PdfReader
from dotenv import load_dotenv
import io

load_dotenv()

# Where WHO PDFs will be saved locally
DOCS_PATH   = os.path.join(os.path.dirname(__file__), "docs")

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
# WHO Guidelines
# ----------------------------------------------------------------

def download_who_pdf(url, title):
    """Download a WHO PDF, save it to docs folder, and extract its text."""
    print(f"Downloading WHO guideline: {title}...")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        safe_name = title.replace(" ", "_").replace(":", "").replace("/", "_")
        pdf_path  = os.path.join(DOCS_PATH, f"{safe_name}.pdf")

        with open(pdf_path, "wb") as f:
            f.write(response.content)
        print(f"Saved PDF to: {pdf_path}")

        pdf   = PdfReader(io.BytesIO(response.content))
        pages = []

        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append(Document(
                    page_content=text,
                    metadata={"source": "WHO", "title": title, "page": i + 1}
                ))

        print(f"Extracted {len(pages)} pages from: {title}")
        return pages

    except Exception as e:
        print(f"Failed to download {title}: {e}")
        return []

def load_who_documents():
    """Download and parse all WHO guideline PDFs."""
    os.makedirs(DOCS_PATH, exist_ok=True)
    all_docs = []
    for item in WHO_PDFS:
        docs = download_who_pdf(item["url"], item["title"])
        all_docs.extend(docs)
    print(f"Loaded {len(all_docs)} pages from WHO guidelines")
    return all_docs

# ----------------------------------------------------------------
# Chunking, Embedding, and Storing in Pinecone
# ----------------------------------------------------------------

def build_knowledge_base():
    """Fetch all sources, chunk the text, embed it, and store in Pinecone."""

    # Load documents from both sources
    openfda_docs = load_openfda_documents()
    who_docs     = load_who_documents()
    all_docs     = openfda_docs + who_docs

    print(f"\nTotal documents loaded: {len(all_docs)}")

    # Split documents into smaller chunks for better retrieval
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(all_docs)
    print(f"Total chunks after splitting: {len(chunks)}")

    # Load the embedding model
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Initialize Pinecone and make sure the index exists
    pc           = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name   = os.getenv("PINECONE_INDEX")
    existing     = [i.name for i in pc.list_indexes()]

    if index_name not in existing:
        print(f"Creating Pinecone index: {index_name}...")
        pc.create_index(
            name=index_name,
            dimension=384,  # dimension for all-MiniLM-L6-v2
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print("Index created.")
    else:
        print(f"Index '{index_name}' already exists.")

    # Store all chunks in Pinecone
    print("Storing chunks in Pinecone...")
    PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=index_name,
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    )

    print(f"\nKnowledge base built successfully.")
    print(f"Total chunks stored: {len(chunks)}")

if __name__ == "__main__":
    build_knowledge_base()