import mysql.connector
from mysql.connector import Error
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_pool = None


def init_db_pool():
    global db_pool
    try:
        db_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="oxytrack_pool",
            pool_size=10,
            pool_reset_session=True,
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT,
        )
        logger.info("MySQL connection pool successfully created.")
    except Error as e:
        logger.error("Error creating MySQL connection pool: %s", e)
        db_pool = None


def get_db_connection():
    """Return a pooled connection, falling back to a direct connection."""
    global db_pool
    if db_pool is None:
        init_db_pool()

    if db_pool:
        try:
            return db_pool.get_connection()
        except Error as e:
            logger.warning("Could not get pooled connection; trying direct connection: %s", e)

    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT,
    )


def setup_database_schema(schema_file_path=None):
    """Create tables inside the configured database."""
    from pathlib import Path

    if schema_file_path is None:
        schema_file_path = Path(__file__).resolve().parent / "sql" / "schema.sql"

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT,
        )
        cursor = conn.cursor()
        with open(schema_file_path, "r", encoding="utf-8") as f:
            statements = f.read().split(";")
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    cursor.execute(statement)
        conn.commit()
        logger.info("Database schema verified and loaded into %s.", Config.DB_NAME)
        init_db_pool()
        return True
    except (Error, OSError) as e:
        logger.error("Database schema setup failed: %s", e)
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
