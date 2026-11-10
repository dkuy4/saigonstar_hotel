import logging
from typing import Generator, Any
import oracledb
from app.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: oracledb.ConnectionPool | None = None

def init_db_pool() -> oracledb.ConnectionPool:
    """Initialize oracledb connection pool in Thin mode."""
    global _pool
    if _pool is None:
        logger.info(f"Initializing Oracle connection pool to {settings.ORA_DSN} as {settings.ORA_USER}")
        _pool = oracledb.create_pool(
            user=settings.ORA_USER,
            password=settings.ORA_PASSWORD,
            dsn=settings.ORA_DSN,
            min=settings.ORA_POOL_MIN,
            max=settings.ORA_POOL_MAX,
            increment=2,
            homogeneous=True,
        )
    return _pool

def close_db_pool() -> None:
    """Close connection pool."""
    global _pool
    if _pool is not None:
        logger.info("Closing Oracle connection pool")
        _pool.close()
        _pool = None

def get_pool() -> oracledb.ConnectionPool:
    if _pool is None:
        return init_db_pool()
    return _pool

def get_conn() -> Generator[oracledb.Connection, None, None]:
    """
    FastAPI dependency yielding a connection from pool.
    Commits on success, rollbacks on error.
    """
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            if settings.ORA_SCHEMA:
                cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {settings.ORA_SCHEMA}")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

def fetch_cursor_as_dicts(cursor: oracledb.Cursor) -> list[dict[str, Any]]:
    """Helper to convert a SYS_REFCURSOR or cursor result into a list of dictionaries with lowercase keys."""
    columns = [col[0].lower() for col in cursor.description] if cursor.description else []
    rows = cursor.fetchall()
    return [dict(zip(columns, row)) for row in rows]
