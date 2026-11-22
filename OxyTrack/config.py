import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

# Load a local .env file for development. Hosted platforms should provide
# environment variables through their deployment settings.
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def _database_settings():
    """
    Prefer Railway's public connection URL when the app is hosted outside
    Railway (for example, on Vercel). A Railway private MYSQL_URL/host is
    only reachable by services on Railway's private network.
    """
    connection_url = os.getenv("MYSQL_PUBLIC_URL") or os.getenv("MYSQL_URL")

    if connection_url:
        parsed = urlparse(connection_url)
        if parsed.scheme not in ("mysql", "mysql+mysqlconnector") or not parsed.hostname:
            raise ValueError(
                "MYSQL_PUBLIC_URL/MYSQL_URL must be a valid mysql:// connection URL."
            )

        database_name = unquote(parsed.path.lstrip("/"))
        if not parsed.username or not database_name:
            raise ValueError(
                "The MySQL connection URL must include a username and database name."
            )

        return {
            "DB_HOST": parsed.hostname,
            "DB_USER": unquote(parsed.username),
            "DB_PASSWORD": unquote(parsed.password or ""),
            "DB_NAME": database_name,
            "DB_PORT": parsed.port or 3306,
        }

    # Also support individual Railway variables when the app itself runs
    # inside Railway, plus DB_* names used by local/manual deployments.
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
