import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env if present
load_dotenv()

# Try loading from streamlit secrets if available
_ST_SECRETS = {}
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        _ST_SECRETS = dict(st.secrets)
except Exception:
    pass

DATASETS_TABLE = "datasets"
RECORDS_TABLE = "sales_records"

STANDARD_COLUMNS = [
    "order_id",
    "order_date",
    "ship_date",
    "category",
    "product_name",
    "region",
    "sales",
    "profit",
    "quantity",
    "discount",
    "shipping_cost",
]

_last_db_error: str | None = None
_tables_initialized: bool = False


def get_last_error() -> str | None:
    global _last_db_error
    return _last_db_error


def _build_database_url() -> tuple[str, str]:
    """
    Determine the database connection URL and type.
    Supports Supabase (Postgres), PostgreSQL, MySQL, and SQLite fallback.
    """
    # 1. Check Streamlit secrets
    supabase_url = _ST_SECRETS.get("SUPABASE_DB_URL") or _ST_SECRETS.get("DATABASE_URL")
    if not supabase_url and "postgres" in _ST_SECRETS and isinstance(_ST_SECRETS["postgres"], dict):
        p = _ST_SECRETS["postgres"]
        supabase_url = f"postgresql://{p.get('user', 'postgres')}:{p.get('password', '')}@{p.get('host', 'localhost')}:{p.get('port', 5432)}/{p.get('dbname', 'postgres')}"

    # 2. Check environment variables
    if not supabase_url:
        supabase_url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

    # 3. Check individual Supabase / Postgres env vars
    if not supabase_url and os.getenv("SUPABASE_DB_HOST"):
        host = os.getenv("SUPABASE_DB_HOST")
        port = os.getenv("SUPABASE_DB_PORT", "5432" if "supabase" in host.lower() else "5432")
        user = os.getenv("SUPABASE_DB_USER", "postgres")
        pwd = os.getenv("SUPABASE_DB_PASSWORD", "")
        dbname = os.getenv("SUPABASE_DB_NAME", "postgres")
        supabase_url = f"postgresql://{user}:{pwd}@{host}:{port}/{dbname}"

    # 4. Check legacy MySQL environment variables if provided
    if not supabase_url and os.getenv("MYSQL_HOST"):
        m_user = os.getenv("MYSQL_USER", "root")
        m_pwd = os.getenv("MYSQL_PASSWORD", "")
        m_host = os.getenv("MYSQL_HOST", "localhost")
        m_db = os.getenv("MYSQL_DATABASE", "analysis")
        supabase_url = f"mysql+pymysql://{m_user}:{m_pwd}@{m_host}/{m_db}"

    # Standardize URL dialect for SQLAlchemy
    if supabase_url:
        url_str = str(supabase_url).strip()
        if url_str.startswith("postgres://"):
            url_str = "postgresql://" + url_str[len("postgres://"):]

        # Handle special characters in password (like @, #, %)
        if "://" in url_str and "@" in url_str:
            try:
                import urllib.parse
                proto, rest = url_str.split("://", 1)
                last_at = rest.rfind("@")
                userinfo, host_and_rest = rest[:last_at], rest[last_at + 1:]
                if ":" in userinfo:
                    user, pwd = userinfo.split(":", 1)
                    encoded_pwd = urllib.parse.quote_plus(urllib.parse.unquote_plus(pwd))
                    url_str = f"{proto}://{user}:{encoded_pwd}@{host_and_rest}"
            except Exception:
                pass
        
        # Ensure sslmode for Supabase if not specified
        if "supabase.co" in url_str or "pooler.supabase.com" in url_str:
            if "?" not in url_str:
                url_str += "?sslmode=require"
            elif "sslmode" not in url_str:
                url_str += "&sslmode=require"

        db_type = "Supabase (PostgreSQL)" if "supabase" in url_str.lower() else (
            "PostgreSQL" if "postgres" in url_str.lower() else "MySQL"
        )
        return url_str, db_type

    # 5. Local SQLite Fallback (Ensures zero-crash local runs before Supabase is connected)
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = (data_dir / "business_analysis.db").resolve()
    return f"sqlite:///{sqlite_path}", "SQLite (Local Fallback)"


DATABASE_URL, DB_TYPE = _build_database_url()


def _create_db_engine():
    global DATABASE_URL, DB_TYPE
    DATABASE_URL, DB_TYPE = _build_database_url()
    
    connect_args = {}
    if DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
    )


engine = _create_db_engine()


def refresh_engine():
    """Rebuild database engine with newly loaded environment or secrets."""
    global engine, DATABASE_URL, DB_TYPE, _tables_initialized
    _tables_initialized = False
    engine = _create_db_engine()
    return engine


def get_db_info() -> dict:
    """Return status and diagnostics about current database connection."""
    global DATABASE_URL, DB_TYPE, _last_db_error
    connected = test_database_connection()
    
    # Mask password in URL for display
    masked_url = DATABASE_URL
    if "@" in masked_url and "://" in masked_url:
        try:
            proto, rest = masked_url.split("://", 1)
            auth, host = rest.split("@", 1)
            if ":" in auth:
                user, _ = auth.split(":", 1)
                masked_url = f"{proto}://{user}:****@{host}"
        except Exception:
            pass

    return {
        "connected": connected,
        "type": DB_TYPE,
        "url_masked": masked_url,
        "is_supabase": "supabase" in DB_TYPE.lower() or "supabase" in DATABASE_URL.lower(),
        "is_local_sqlite": "sqlite" in DATABASE_URL.lower(),
        "last_error": _last_db_error,
    }


def table_exists(table_name: str) -> bool:
    try:
        inspector = inspect(engine)
        return inspector.has_table(table_name)
    except Exception as e:
        global _last_db_error
        _last_db_error = str(e)
        return False


def init_database_tables(force: bool = False) -> bool:
    """Create datasets and sales_records tables only once per session."""
    global _last_db_error, _tables_initialized
    if _tables_initialized and not force:
        return True

    try:
        is_postgres = "postgres" in engine.dialect.name
        is_sqlite = "sqlite" in engine.dialect.name

        with engine.begin() as connection:
            # 1. Create Datasets Table
            if is_postgres:
                connection.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {DATASETS_TABLE} (
                            id VARCHAR(12) PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            row_count INTEGER DEFAULT 0,
                            column_count INTEGER DEFAULT 0,
                            content_hash VARCHAR(32),
                            is_active BOOLEAN DEFAULT FALSE
                        )
                        """
                    )
                )
                connection.execute(
                    text(f"CREATE INDEX IF NOT EXISTS idx_{DATASETS_TABLE}_name ON {DATASETS_TABLE} (name)")
                )
            elif is_sqlite:
                connection.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {DATASETS_TABLE} (
                            id VARCHAR(12) PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            uploaded_at TIMESTAMP NOT NULL,
                            row_count INTEGER DEFAULT 0,
                            column_count INTEGER DEFAULT 0,
                            content_hash VARCHAR(32),
                            is_active INTEGER DEFAULT 0
                        )
                        """
                    )
                )
            else:
                # MySQL
                connection.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {DATASETS_TABLE} (
                            id VARCHAR(12) PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            uploaded_at DATETIME NOT NULL,
                            row_count INT DEFAULT 0,
                            column_count INT DEFAULT 0,
                            content_hash VARCHAR(32),
                            is_active TINYINT(1) DEFAULT 0,
                            INDEX idx_dataset_name (name)
                        )
                        """
                    )
                )

            # 2. Create Sales Records Table
            if is_postgres:
                connection.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {RECORDS_TABLE} (
                            record_id BIGSERIAL PRIMARY KEY,
                            dataset_id VARCHAR(12) NOT NULL REFERENCES {DATASETS_TABLE}(id) ON DELETE CASCADE,
                            order_id VARCHAR(100),
                            order_date DATE,
                            ship_date DATE,
                            category VARCHAR(100),
                            product_name VARCHAR(255),
                            region VARCHAR(100),
                            sales DOUBLE PRECISION,
                            profit DOUBLE PRECISION,
                            quantity INTEGER,
                            discount DOUBLE PRECISION,
                            shipping_cost DOUBLE PRECISION
                        )
                        """
                    )
                )
                connection.execute(
                    text(f"CREATE INDEX IF NOT EXISTS idx_{RECORDS_TABLE}_dataset_id ON {RECORDS_TABLE} (dataset_id)")
                )
            elif is_sqlite:
                connection.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {RECORDS_TABLE} (
                            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            dataset_id VARCHAR(12) NOT NULL REFERENCES {DATASETS_TABLE}(id) ON DELETE CASCADE,
                            order_id VARCHAR(100),
                            order_date DATE,
                            ship_date DATE,
                            category VARCHAR(100),
                            product_name VARCHAR(255),
                            region VARCHAR(100),
                            sales REAL,
                            profit REAL,
                            quantity INTEGER,
                            discount REAL,
                            shipping_cost REAL
                        )
                        """
                    )
                )
                connection.execute(
                    text(f"CREATE INDEX IF NOT EXISTS idx_{RECORDS_TABLE}_dataset_id ON {RECORDS_TABLE} (dataset_id)")
                )
            else:
                # MySQL
                connection.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {RECORDS_TABLE} (
                            record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            dataset_id VARCHAR(12) NOT NULL,
                            order_id VARCHAR(100),
                            order_date DATE,
                            ship_date DATE,
                            category VARCHAR(100),
                            product_name VARCHAR(255),
                            region VARCHAR(100),
                            sales DOUBLE,
                            profit DOUBLE,
                            quantity INT,
                            discount DOUBLE,
                            shipping_cost FLOAT,
                            CONSTRAINT fk_sales_dataset
                                FOREIGN KEY (dataset_id)
                                REFERENCES {DATASETS_TABLE}(id)
                                ON DELETE CASCADE,
                            INDEX idx_dataset_id (dataset_id)
                        )
                        """
                    )
                )

        _tables_initialized = True
        _last_db_error = None
        return True
    except Exception as e:
        _last_db_error = str(e)
        print(f"Database Init Error: {e}")
        return False


def count_datasets() -> int:
    return len(list_datasets())


def _file_hash(file_bytes: bytes) -> str:
    return hashlib.md5(file_bytes).hexdigest()


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in STANDARD_COLUMNS:
        if col not in out.columns:
            out[col] = None
    out = out[STANDARD_COLUMNS]
    out.insert(0, "dataset_id", None)
    return out


def _normalize_dataset_record(item: dict) -> dict:
    item["is_active"] = bool(item.get("is_active"))
    item["rows"] = int(item.get("row_count") or item.get("rows") or 0)
    item["columns"] = int(item.get("column_count") or item.get("columns") or 0)
    if hasattr(item.get("uploaded_at"), "isoformat"):
        item["uploaded_at"] = item["uploaded_at"].isoformat()
    else:
        item["uploaded_at"] = str(item.get("uploaded_at", ""))
    return item


def find_dataset_by_name(name: str) -> dict | None:
    init_database_tables()
    global _last_db_error
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    f"""
                    SELECT id, name, uploaded_at, row_count, column_count,
                           content_hash, is_active
                    FROM {DATASETS_TABLE}
                    WHERE LOWER(name) = LOWER(:name)
                    ORDER BY uploaded_at DESC
                    LIMIT 1
                    """
                ),
                {"name": name.strip()},
            ).mappings().first()
        if not row:
            return None
        item = dict(row)
        _normalize_dataset_record(item)
        return item
    except SQLAlchemyError as e:
        _last_db_error = str(e)
        print(f"Find Dataset Error: {e}")
        return None


def list_datasets() -> list[dict]:
    init_database_tables()
    global _last_db_error
    try:
        with engine.connect() as connection:
            df = pd.read_sql(
                text(
                    f"""
                    SELECT id, name, uploaded_at, row_count, column_count,
                           content_hash, is_active
                    FROM {DATASETS_TABLE}
                    ORDER BY uploaded_at DESC
                    """
                ),
                con=connection,
            )
        records = df.to_dict(orient="records")
        for item in records:
            _normalize_dataset_record(item)
        return records
    except SQLAlchemyError as e:
        _last_db_error = str(e)
        print(f"List Datasets Error: {e}")
        return []


def get_dataset(dataset_id: str) -> dict | None:
    init_database_tables()
    global _last_db_error
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    f"""
                    SELECT id, name, uploaded_at, row_count, column_count,
                           content_hash, is_active
                    FROM {DATASETS_TABLE}
                    WHERE id = :id
                    """
                ),
                {"id": dataset_id},
            ).mappings().first()
        if not row:
            return None
        item = dict(row)
        _normalize_dataset_record(item)
        return item
    except SQLAlchemyError as e:
        _last_db_error = str(e)
        print(f"Get Dataset Error: {e}")
        return None


def get_active_dataset_id() -> str | None:
    init_database_tables()
    global _last_db_error
    try:
        with engine.connect() as connection:
            is_postgres = "postgres" in engine.dialect.name
            active_filter = "is_active = TRUE" if is_postgres else "is_active = 1"
            row = connection.execute(
                text(
                    f"""
                    SELECT id FROM {DATASETS_TABLE}
                    WHERE {active_filter}
                    LIMIT 1
                    """
                ),
            ).first()
        return row[0] if row else None
    except SQLAlchemyError as e:
        _last_db_error = str(e)
        return None


def set_active_dataset(dataset_id: str | None) -> None:
    init_database_tables()
    global _last_db_error
    try:
        is_postgres = "postgres" in engine.dialect.name
        with engine.begin() as connection:
            if is_postgres:
                connection.execute(text(f"UPDATE {DATASETS_TABLE} SET is_active = FALSE"))
                if dataset_id:
                    connection.execute(
                        text(f"UPDATE {DATASETS_TABLE} SET is_active = TRUE WHERE id = :id"),
                        {"id": dataset_id},
                    )
            else:
                connection.execute(text(f"UPDATE {DATASETS_TABLE} SET is_active = 0"))
                if dataset_id:
                    connection.execute(
                        text(f"UPDATE {DATASETS_TABLE} SET is_active = 1 WHERE id = :id"),
                        {"id": dataset_id},
                    )
    except SQLAlchemyError as e:
        _last_db_error = str(e)
        print(f"Set Active Dataset Error: {e}")


def _storage_label(original_name: str) -> str:
    """Keep original filename; uploads with the same name are separate datasets."""
    return original_name.strip()


def _fast_bulk_insert_postgres(connection, records_df: pd.DataFrame):
    """Lightning-fast bulk insert for PostgreSQL / Supabase using psycopg2 execute_values."""
    try:
        import psycopg2.extras
        raw_conn = connection.connection.driver_connection
        cols = list(records_df.columns)
        col_names = ", ".join(cols)
        sql = f"INSERT INTO {RECORDS_TABLE} ({col_names}) VALUES %s"
        values = [tuple(row) for row in records_df.to_numpy()]
        with raw_conn.cursor() as cursor:
            psycopg2.extras.execute_values(cursor, sql, values, page_size=2000)
        return True
    except Exception:
        # Fallback to high-chunksize to_sql
        records_df.to_sql(
            name=RECORDS_TABLE,
            con=connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=2000,
        )
        return True


def save_dataset_to_database(
    df: pd.DataFrame,
    original_name: str,
    file_bytes: bytes | None = None,
    *,
    replace_existing_name: bool = False,
) -> str | None:
    """Save dataset rows in database (Supabase PostgreSQL / SQLite / MySQL)."""
    global _last_db_error
    init_database_tables()

    original_name = original_name.strip()
    content_hash = _file_hash(file_bytes) if file_bytes else ""
    storage_name = _storage_label(original_name)
    uploaded_at = datetime.now(timezone.utc)

    row_count = int(df.shape[0])
    column_count = int(df.shape[1])

    existing = find_dataset_by_name(storage_name) if replace_existing_name else None
    dataset_id = existing["id"] if existing else uuid4().hex[:12]

    if df.empty:
        _last_db_error = "Uploaded dataframe is empty or invalid."
        print(f"Save Dataset Error: {_last_db_error}")
        return None

    try:
        is_postgres = "postgres" in engine.dialect.name
        with engine.begin() as connection:
            if existing and replace_existing_name:
                connection.execute(
                    text(f"DELETE FROM {RECORDS_TABLE} WHERE dataset_id = :id"),
                    {"id": dataset_id},
                )
                connection.execute(
                    text(
                        f"""
                        UPDATE {DATASETS_TABLE}
                        SET uploaded_at = :uploaded_at,
                            row_count = :row_count,
                            column_count = :column_count,
                            content_hash = :content_hash
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": dataset_id,
                        "uploaded_at": uploaded_at,
                        "row_count": row_count,
                        "column_count": column_count,
                        "content_hash": content_hash,
                    },
                )
            else:
                active_val = False if is_postgres else 0
                connection.execute(
                    text(
                        f"""
                        INSERT INTO {DATASETS_TABLE}
                            (id, name, uploaded_at, row_count, column_count,
                             content_hash, is_active)
                        VALUES
                            (:id, :name, :uploaded_at, :row_count, :column_count,
                             :content_hash, :is_active)
                        """
                    ),
                    {
                        "id": dataset_id,
                        "name": storage_name,
                        "uploaded_at": uploaded_at,
                        "row_count": row_count,
                        "column_count": column_count,
                        "content_hash": content_hash,
                        "is_active": active_val,
                    },
                )

            records_df = _normalize_dataframe(df)
            records_df["dataset_id"] = dataset_id
            
            # Fast bulk insert
            if is_postgres:
                _fast_bulk_insert_postgres(connection, records_df)
            else:
                records_df.to_sql(
                    name=RECORDS_TABLE,
                    con=connection,
                    if_exists="append",
                    index=False,
                    method="multi",
                    chunksize=2000,
                )

        _last_db_error = None
        return dataset_id

    except (SQLAlchemyError, pd.errors.DatabaseError, Exception) as e:
        _last_db_error = str(e)
        print(f"Save Dataset Error: {e}")
        return None


def load_dataset_from_database(dataset_id: str) -> pd.DataFrame:
    init_database_tables()
    global _last_db_error

    try:
        with engine.connect() as connection:
            df = pd.read_sql(
                text(
                    f"""
                    SELECT order_id, order_date, ship_date, category, product_name,
                           region, sales, profit, quantity, discount, shipping_cost
                    FROM {RECORDS_TABLE}
                    WHERE dataset_id = :dataset_id
                    """
                ),
                con=connection,
                params={"dataset_id": dataset_id},
            )
        _last_db_error = None
        return df
    except (SQLAlchemyError, pd.errors.DatabaseError, Exception) as e:
        _last_db_error = str(e)
        print(f"Load Dataset Error: {e}")
        return pd.DataFrame()


def load_from_database() -> pd.DataFrame:
    """Load rows for the currently active dataset."""
    active_id = get_active_dataset_id()
    if not active_id:
        return pd.DataFrame()
    return load_dataset_from_database(active_id)


def save_to_database(df: pd.DataFrame) -> bool:
    """Backward-compatible: save active dataset rows (requires active id)."""
    active_id = get_active_dataset_id()
    if not active_id:
        return False

    dataset = get_dataset(active_id)
    if not dataset:
        return False

    result = save_dataset_to_database(df, dataset["name"])
    return result is not None


def delete_dataset(dataset_id: str) -> bool:
    init_database_tables()
    global _last_db_error
    try:
        with engine.begin() as connection:
            connection.execute(
                text(f"DELETE FROM {RECORDS_TABLE} WHERE dataset_id = :id"),
                {"id": dataset_id},
            )
            connection.execute(
                text(f"DELETE FROM {DATASETS_TABLE} WHERE id = :id"),
                {"id": dataset_id},
            )
        _last_db_error = None
        return True
    except SQLAlchemyError as e:
        _last_db_error = str(e)
        print(f"Delete Dataset Error: {e}")
        return False


def clear_active_dataset_rows() -> bool:
    active_id = get_active_dataset_id()
    if not active_id:
        return True
    global _last_db_error
    try:
        with engine.begin() as connection:
            connection.execute(
                text(f"DELETE FROM {RECORDS_TABLE} WHERE dataset_id = :id"),
                {"id": active_id},
            )
        set_active_dataset(None)
        _last_db_error = None
        return True
    except SQLAlchemyError as e:
        _last_db_error = str(e)
        print(f"Clear Active Dataset Error: {e}")
        return False


def clear_database() -> bool:
    """Clear active dataset only (legacy name)."""
    return clear_active_dataset_rows()


def _parse_uploaded_at_value(value) -> datetime:
    """Parse DB/API timestamps; naive values are treated as UTC."""
    if isinstance(value, datetime):
        dt = value
    else:
        text_value = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text_value)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_uploaded_at(item: dict) -> datetime:
    try:
        return _parse_uploaded_at_value(item.get("uploaded_at")).replace(tzinfo=None)
    except (TypeError, ValueError):
        return datetime.min


def _duplicate_ids_to_remove(datasets: list[dict]) -> tuple[set[str], dict[str, int]]:
    """Newest upload wins per filename and per identical file content (hash)."""
    by_name: set[str] = set()
    by_hash: set[str] = set()
    sorted_newest_first = sorted(
        datasets,
        key=_parse_uploaded_at,
        reverse=True,
    )

    seen_names: set[str] = set()
    for item in sorted_newest_first:
        name_key = item["name"].strip().lower()
        if name_key in seen_names:
            by_name.add(item["id"])
        else:
            seen_names.add(name_key)

    seen_hashes: set[str] = set()
    for item in sorted_newest_first:
        content_hash = (item.get("content_hash") or "").strip()
        if not content_hash:
            continue
        if content_hash in seen_hashes:
            by_hash.add(item["id"])
        else:
            seen_hashes.add(content_hash)

    return by_name | by_hash, {
        "by_name": len(by_name),
        "by_hash": len(by_hash),
    }


def count_duplicate_datasets() -> dict:
    """How many datasets would be removed by cleanup (preview, no deletes)."""
    init_database_tables()
    datasets = list_datasets()
    remove_ids, breakdown = _duplicate_ids_to_remove(datasets)
    return {
        "total": len(remove_ids),
        "by_name": breakdown["by_name"],
        "by_hash": breakdown["by_hash"],
        "remaining_after": len(datasets) - len(remove_ids),
    }


def run_dataset_cleanup() -> dict:
    """
    Remove duplicate saved datasets (keeps newest per filename and per file hash).
    Returns summary for UI feedback.
    """
    init_database_tables()
    datasets = list_datasets()
    if not datasets:
        return {
            "removed": 0,
            "remaining": 0,
            "by_name": 0,
            "by_hash": 0,
            "cleared_active": False,
        }

    remove_ids, breakdown = _duplicate_ids_to_remove(datasets)
    if not remove_ids:
        return {
            "removed": 0,
            "remaining": len(datasets),
            "by_name": 0,
            "by_hash": 0,
            "cleared_active": False,
        }

    active_id = get_active_dataset_id()
    removed = 0
    for dataset_id in remove_ids:
        if delete_dataset(dataset_id):
            removed += 1

    cleared_active = bool(active_id and active_id in remove_ids)
    if cleared_active:
        set_active_dataset(None)

    remaining = len(list_datasets())
    return {
        "removed": removed,
        "remaining": remaining,
        "by_name": breakdown["by_name"],
        "by_hash": breakdown["by_hash"],
        "cleared_active": cleared_active,
    }


def deduplicate_datasets_by_name() -> int:
    """Backward-compatible wrapper."""
    return run_dataset_cleanup()["removed"]


def storage_stats() -> dict:
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(f"SELECT COUNT(*), COALESCE(SUM(row_count), 0) FROM {DATASETS_TABLE}")
            ).first()
            if row:
                return {
                    "count": int(row[0] or 0),
                    "total_rows": int(row[1] or 0),
                    "total_size_mb": 0,
                }
    except Exception:
        pass
    
    datasets = list_datasets()
    total_rows = sum(int(d.get("row_count", 0) or 0) for d in datasets)
    return {
        "count": len(datasets),
        "total_rows": total_rows,
        "total_size_mb": 0,
    }


def format_uploaded_at(iso_value: str) -> str:
    """Show upload time in the user's local timezone."""
    try:
        local_dt = _parse_uploaded_at_value(iso_value).astimezone()
        return local_dt.strftime("%b %d, %Y %I:%M %p")
    except (TypeError, ValueError):
        return str(iso_value)


def test_database_connection() -> bool:
    global _last_db_error
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            _last_db_error = None
            return True
    except Exception as e:
        _last_db_error = str(e)
        print(f"Database Connection Failed: {e}")
        return False


__all__ = [
    "clear_active_dataset_rows",
    "clear_database",
    "count_duplicate_datasets",
    "deduplicate_datasets_by_name",
    "run_dataset_cleanup",
    "delete_dataset",
    "find_dataset_by_name",
    "format_uploaded_at",
    "get_active_dataset_id",
    "get_dataset",
    "get_db_info",
    "get_last_error",
    "init_database_tables",
    "list_datasets",
    "load_dataset_from_database",
    "load_from_database",
    "refresh_engine",
    "save_dataset_to_database",
    "save_to_database",
    "set_active_dataset",
    "storage_stats",
    "test_database_connection",
]
