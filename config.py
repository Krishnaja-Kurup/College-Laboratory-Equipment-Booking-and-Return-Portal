import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config:
    """
    Application configuration class.
    Loads sensitive credentials from environment variables for PostgreSQL and Flask.
    """
    # Secret key for signing session cookies
    SECRET_KEY = os.getenv("SECRET_KEY", "college-lab-secret-key-2026")

    # PostgreSQL Database URL
    # Example: postgresql://postgres:password@localhost:5432/college_lab_portal
    raw_db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/college_lab_portal"
    )

    # SQLAlchemy 2.0+ requires postgresql:// instead of legacy postgres://
    if raw_db_url and raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
