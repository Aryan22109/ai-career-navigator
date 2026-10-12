import os


class Config:
    # MySQL in production, e.g. mysql+pymysql://user:pass@db:3306/career_navigator
    # Falls back to a local SQLite file so the app runs with zero setup.
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///career_navigator.db")
    MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 2 * 1024 * 1024))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")
    RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", 20))
    TRUST_PROXY = os.getenv("TRUST_PROXY", "0") == "1"  # set to 1 behind nginx / a load balancer
