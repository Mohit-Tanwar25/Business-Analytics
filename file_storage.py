"""
Dataset storage API — data is persisted in Supabase PostgreSQL (or configured database) via database.py.
"""

from io import BytesIO

import pandas as pd

from analysis import clean_data
from database import (
    count_duplicate_datasets,
    deduplicate_datasets_by_name,
    delete_dataset,
    format_uploaded_at,
    get_active_dataset_id,
    get_dataset,
    get_db_info,
    get_last_error,
    init_database_tables,
    list_datasets,
    load_dataset_from_database,
    load_from_database,
    run_dataset_cleanup,
    save_dataset_to_database,
    set_active_dataset,
    storage_stats,
    test_database_connection,
)

__all__ = [
    "count_duplicate_datasets",
    "deduplicate_datasets_by_name",
    "delete_dataset",
    "format_uploaded_at",
    "get_active_dataset_id",
    "get_dataset",
    "get_dataset_path",
    "get_db_info",
    "get_last_error",
    "init_database_tables",
    "list_datasets",
    "load_dataset_from_database",
    "load_from_database",
    "run_dataset_cleanup",
    "set_active_dataset",
    "storage_stats",
    "store_uploaded_csv",
    "test_database_connection",
]


def get_dataset_path(dataset_id: str):
    """Returns dataset_id if it exists in database."""
    if get_dataset(dataset_id):
        return dataset_id
    return None


def store_uploaded_csv(file_bytes: bytes, original_name: str) -> str | None:
    try:
        df = pd.read_csv(BytesIO(file_bytes))
        df = clean_data(df)
        if df.empty:
            return None
        return save_dataset_to_database(df, original_name, file_bytes)
    except Exception as e:
        print(f"Error reading CSV {original_name}: {e}")
        return None
