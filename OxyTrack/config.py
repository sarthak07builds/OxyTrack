import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is explicitly loaded from OxyTrack project directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "oxytrack-secret-key-default")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "oxytrack_db")
    DB_PORT = int(os.getenv("DB_PORT", 3306))

