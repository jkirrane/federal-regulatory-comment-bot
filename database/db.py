"""
Database utilities for Federal Regulatory Comment Bot

Provides functions for:
- Database initialization
- Comment period CRUD operations
- Posting status tracking
- Common queries
"""

import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any


DB_PATH = Path(__file__).parent / "comment_periods.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """
    Get a connection to the database with row_factory for dict-like access
    
    Returns:
        sqlite3.Connection with row_factory set
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """
    Initialize the database from schema.sql
    
    Safe to run multiple times (uses IF NOT EXISTS)
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()
    
    conn = get_connection()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {DB_PATH}")


def upsert_comment_period(
    document_id: str,
    docket_id: str,
    title: str,
    agency_id: str,
    agency_name: str,
    posted_date: str,
    comment_end_date: str,
    regulations_url: str,
    **kwargs
) -> int:
    """
    Insert or update a comment period
    
    Uses ON CONFLICT pattern from court bot for idempotent scraping.
    Safe to run multiple times - will update if document_id exists.
    
    Args:
        document_id: Unique document ID (e.g., FDA-2024-N-1234)
        docket_id: Parent docket ID
        title: Rule/notice title
        agency_id: Agency abbreviation (EPA, FDA, etc.)
        agency_name: Full agency name
        posted_date: Date posted (YYYY-MM-DD)
        comment_end_date: Comment deadline (YYYY-MM-DD)
        regulations_url: Direct link to comment
        **kwargs: Optional fields (abstract, summary, topics, etc.)
    
    Returns:
        int: ID of inserted/updated record
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build dynamic SQL for optional fields
    optional_fields = [
        'document_type', 'comment_start_date', 'abstract', 'summary',
        'federal_register_url', 'details_url', 'topics', 'keywords', 'source_url'
    ]
    
    provided_optional = {k: v for k, v in kwargs.items() if k in optional_fields and v is not None}
    
    # Base fields
    fields = [
        'document_id', 'docket_id', 'title', 'agency_id', 'agency_name',
        'posted_date', 'comment_end_date', 'regulations_url'
    ] + list(provided_optional.keys())
    
    placeholders = ', '.join(['?'] * len(fields))
    field_names = ', '.join(fields)
    
    # ON CONFLICT update clause
    update_clause = ', '.join([
        f"{field}=excluded.{field}" for field in fields if field != 'document_id'
    ] + ['updated_at=CURRENT_TIMESTAMP'])
    
    sql = f"""
        INSERT INTO comment_periods ({field_names})
        VALUES ({placeholders})
        ON CONFLICT(document_id)
        DO UPDATE SET {update_clause}
    """
    
    values = [
        document_id, docket_id, title, agency_id, agency_name,
        posted_date, comment_end_date, regulations_url
    ] + list(provided_optional.values())
    
    cursor.execute(sql, values)
    conn.commit()
    
    # Get the inserted/updated ID
    period_id = cursor.lastrowid if cursor.lastrowid > 0 else cursor.execute(
        "SELECT id FROM comment_periods WHERE document_id = ?", (document_id,)
    ).fetchone()[0]
    
    conn.close()
    return period_id


def get_new_comment_periods(days: int = 1, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get comment periods posted in the last N days that haven't been posted yet
    
    Args:
        days: Number of days back to look
        limit: Maximum number of results (None for all)
    
    Returns:
        List of comment period dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    sql = """
        SELECT * FROM comment_periods
        WHERE posted_date >= ?
          AND posted_new = 0
          AND comment_end_date >= date('now')
        ORDER BY posted_date DESC
    """
    
    if limit:
        sql += f" LIMIT {limit}"
    
    cursor.execute(sql, (cutoff_date,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def get_closing_soon(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get comment periods closing in N days
    
    Filters based on which reminders have already been posted.
    
    Args:
        days: Number of days until deadline (7, 3, or 1)
    
    Returns:
        List of comment period dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Determine which reminder flag to check
    if days == 7:
        reminder_field = 'posted_7day_reminder'
    elif days == 3:
        reminder_field = 'posted_3day_reminder'
    elif days == 1:
        reminder_field = 'posted_last_day'
    else:
        raise ValueError("days must be 7, 3, or 1")
    
    sql = f"""
        SELECT * FROM comment_periods
        WHERE date(comment_end_date) = ?
          AND {reminder_field} = 0
        ORDER BY agency_id, title
    """
    
    cursor.execute(sql, (target_date,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def mark_posted(period_id: int, post_type: str, post_uri: Optional[str] = None) -> None:
    """
    Mark a comment period as posted
    
    Args:
        period_id: ID of comment period
        post_type: Type of post ('new', '7day', '3day', 'last_day')
        post_uri: Bluesky post URI (optional, for tracking)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Map post_type to database field
    field_map = {
        'new': 'posted_new',
        '7day': 'posted_7day_reminder',
        '3day': 'posted_3day_reminder',
        'last_day': 'posted_last_day'
    }
    
    if post_type not in field_map:
        raise ValueError(f"Invalid post_type: {post_type}")
    
    field = field_map[post_type]
    
    # Update the posting flag
    cursor.execute(
        f"UPDATE comment_periods SET {field} = 1 WHERE id = ?",
        (period_id,)
    )
    
    # Insert into bot_posts for tracking
    if post_uri:
        cursor.execute(
            "INSERT INTO bot_posts (comment_period_id, post_type, post_uri) VALUES (?, ?, ?)",
            (period_id, post_type, post_uri)
        )
    
    conn.commit()
    conn.close()


def get_period_by_document_id(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single comment period by document_id
    
    Args:
        document_id: Document ID (e.g., FDA-2024-N-1234)
    
    Returns:
        Comment period dict or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM comment_periods WHERE document_id = ?",
        (document_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_all_open_periods() -> List[Dict[str, Any]]:
    """
    Get all comment periods that are currently open
    
    Returns:
        List of comment period dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM comment_periods
        WHERE comment_end_date >= date('now')
        ORDER BY comment_end_date ASC
    """)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def get_stats() -> Dict[str, int]:
    """
    Get database statistics
    
    Returns:
        Dict with counts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total periods
    cursor.execute("SELECT COUNT(*) FROM comment_periods")
    stats['total_periods'] = cursor.fetchone()[0]
    
    # Currently open
    cursor.execute("SELECT COUNT(*) FROM comment_periods WHERE comment_end_date >= date('now')")
    stats['open_periods'] = cursor.fetchone()[0]
    
    # Posted
    cursor.execute("SELECT COUNT(*) FROM comment_periods WHERE posted_new = 1")
    stats['posted_periods'] = cursor.fetchone()[0]
    
    # Total posts
    cursor.execute("SELECT COUNT(*) FROM bot_posts")
    stats['total_posts'] = cursor.fetchone()[0]
    
    conn.close()
    return stats


def main():
    """
    Initialize database and display statistics
    """
    print("Initializing Federal Regulatory Comment Bot database...")
    initialize_database()
    
    print("\nDatabase created successfully!")
    print(f"Location: {DB_PATH}")
    
    stats = get_stats()
    print(f"\nStatistics:")
    print(f"  Total periods: {stats['total_periods']}")
    print(f"  Open periods: {stats['open_periods']}")
    print(f"  Posted periods: {stats['posted_periods']}")
    print(f"  Total posts: {stats['total_posts']}")
    
    print("\nYou can inspect the database with:")
    print(f"  sqlite3 {DB_PATH}")
    print(f"  sqlite3 {DB_PATH} '.schema'")
    print(f"  sqlite3 {DB_PATH} 'SELECT * FROM agencies;'")


if __name__ == "__main__":
    main()
