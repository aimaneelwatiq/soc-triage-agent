import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # --- Ollama ---
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "phi4-mini")
    
    # --- OSINT ---
    VT_API_KEY: str = os.getenv("VT_API_KEY", "")
    ABUSEIPDB_API_KEY: str = os.getenv("ABUSEIPDB_API_KEY", "")
    
    # --- Comportement ---
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 800

settings = Settings()