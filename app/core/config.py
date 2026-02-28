from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load .env file so OPENAI_API_KEY (and others) are available via os.getenv
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # python-dotenv is optional

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
