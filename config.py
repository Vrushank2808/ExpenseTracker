import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = PROJECT_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(PROJECT_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-local-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DIR / 'expense.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
