"""Configuration management for Auto-Research Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
DB_DIR = BASE_DIR / "database"

# Create directories if they don't exist
for directory in [OUTPUT_DIR, REPORTS_DIR, LOGS_DIR, DB_DIR]:
    directory.mkdir(exist_ok=True)

# Subscription Configuration
SUBSCRIPTION_TIER = os.getenv("SUBSCRIPTION_TIER", "free")

# Free Tier API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Premium Tier API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_GEMINI_PRO_KEY = os.getenv("GOOGLE_GEMINI_PRO_KEY")

# Search API Keys
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
BING_SEARCH_KEY = os.getenv("BING_SEARCH_KEY")

# Application Settings
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "10"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))

# Agent Settings
TEMPERATURE = 0.7
MAX_TOKENS = 4096

# Citation Formats
CITATION_FORMATS = ["APA", "MLA", "IEEE"]
DEFAULT_CITATION_FORMAT = "APA"

# Database
DATABASE_PATH = DB_DIR / "research_history.db"
FAISS_INDEX_PATH = DB_DIR / "faiss_index"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "research_agent.log"
