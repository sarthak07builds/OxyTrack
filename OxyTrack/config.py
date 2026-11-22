import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


def _database_settings():
    # Vercel is outside Railway's private network, so use the public TCP URL.
    # MYSQL_URL is private to Railway and must not be used as a Vercel fallback.
    public_url = os.getenv("MYSQL_PUBLIC_URL")
    if public_url:
        parsed = urlparse(public_url)
        if parsed.scheme not in ("mysql", "mysql+mysqlconnector") or not parsed.hostname:
            raise ValueError("MYSQL_PUBLIC_URL must be a valid mysql:// connection URL.")

        database_name = unquote(parsed.path.lstrip("/"))
        if not parsed.username or not database_name:
            raise ValueError("MYSQL_PUBLIC_URL must include a username and database name.")

        return {
            "DB_HOST": parsed.hostname,
            "DB_USER": unquote(parsed.username),
            "DB_PASSWORD": unquote(parsed.password or ""),
            "DB_NAME": database_name,
            "DB_PORT": parsed.port or 3306,
        }

    # Supports local development and apps deployed within Railway.
    return {
        "DB_HOST": os.getenv("DB_HOST") or os.getenv("MYSQLHOST") or "localhost",
        "DB_USER": os.getenv("DB_USER") or os.getenv("MYSQLUSER") or "root",
        "DB_PASSWORD": os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD") or "",
        "DB_NAME": os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE") or "oxytrack_db",
        "DB_PORT": int(os.getenv("DB_PORT") or os.getenv("MYSQLPORT") or 3306),
    }


_DB = _database_settings()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "oxytrack-secret-key-default")
    DB_HOST = _DB["DB_HOST"]
    DB_USER = _DB["DB_USER"]
    DB_PASSWORD = _DB["DB_PASSWORD"]
    DB_NAME = _DB["DB_NAME"]
    DB_PORT = _DB["DB_PORT"]
