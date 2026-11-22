import mysql.connector
from mysql.connector import Error, pooling
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_pool = None

def init_db_pool():
    global db_pool
    try:
        # Create connection pool
        db_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="oxytrack_pool",
            pool_size=10,
            pool_reset_session=True,
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT
        )
        logger.info("MySQL Connection Pool successfully created.")
    except Error as e:
        logger.error(f"Error creating MySQL Connection Pool: {e}")
        db_pool = None

def get_db_connection():
    """Returns a connection from the pool, or direct connection if pool fails"""
    global db_pool
    if db_pool is None:
        init_db_pool()
    
    if db_pool:
        try:
            return db_pool.get_connection()
        except Error:
            pass
            
    # Fallback to single connection
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )

def setup_database_schema(schema_file_path=None):
    """Creates database and tables from schema.sql if they don't exist"""
    import os
    from pathlib import Path
    if schema_file_path is None:
        base_dir = Path(__file__).resolve().parent
        schema_file_path = base_dir / "sql" / "schema.sql"

    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT
        )
        cursor = conn.cursor()
        with open(schema_file_path, 'r', encoding='utf-8') as f:
            statements = f.read().split(';')
            for stmt in statements:
                stmt_clean = stmt.strip()
                if stmt_clean:
                    cursor.execute(stmt_clean)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Database schema verified and loaded.")
        init_db_pool()
        return True
    except Error as e:
        logger.warning(f"Database setup warning/notice: {e}")
        return False
