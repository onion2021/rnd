import sqlite3

try:
    from .api import (
        DB_FILE,
        PROJECT_CARD_TABLE,
        PROJECT_DOE_TABLE,
        ensure_project_activity_tables,
        sync_project_activities_to_db,
    )
except ImportError:
    from api import (
        DB_FILE,
        PROJECT_CARD_TABLE,
        PROJECT_DOE_TABLE,
        ensure_project_activity_tables,
        sync_project_activities_to_db,
    )


def init_database(force_sync=False):
    """Initialize SQLite tables used by the DOE project experience app."""
    conn = sqlite3.connect(DB_FILE)
    try:
        ensure_project_activity_tables(conn)
    finally:
        conn.close()

    sync_project_activities_to_db(force=force_sync)


def test_connection():
    """Return simple row counts for the synced DOE tables."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {PROJECT_CARD_TABLE}")
        project_count = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM {PROJECT_DOE_TABLE}")
        doe_count = cursor.fetchone()[0]
        cursor.close()
        print(f"project_cards: {project_count}")
        print(f"project_doe_entries: {doe_count}")
        return True
    except Exception as e:
        print(f"SQLite connection test failed: {str(e)}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    init_database(force_sync=True)
    test_connection()
