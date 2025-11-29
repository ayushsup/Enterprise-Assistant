import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    UPLOAD_DIR = "temp_uploads"
    ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json"}

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)