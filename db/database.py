from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Read the Neon connection string from the environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file")

# Create the engine that connects to the PostgreSQL database
engine = create_engine(DATABASE_URL)

# Each request gets its own isolated database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all models inherit from to register their tables
Base = declarative_base()

# Provide a database session to any route that needs it,
# and close it when done, even if an error occurs
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()