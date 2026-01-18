"""
Migrate database to make docket_id optional
"""

import sqlite3

db_path = "database/comment_periods.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Creating new table with optional docket_id...")

# Create new table with optional docket_id - include all 24 columns
cursor.execute("""
CREATE TABLE comment_periods_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL UNIQUE,
    docket_id TEXT,
    title TEXT NOT NULL,
    agency_id TEXT NOT NULL,
    agency_name TEXT NOT NULL,
    document_type TEXT,
    posted_date DATE NOT NULL,
    comment_start_date DATE,
    comment_end_date DATE NOT NULL,
    abstract TEXT,
    summary TEXT,
    regulations_url TEXT NOT NULL,
    federal_register_url TEXT,
    details_url TEXT,
    topics TEXT,
    keywords TEXT,
    posted_new BOOLEAN DEFAULT 0,
    posted_7day_reminder BOOLEAN DEFAULT 0,
    posted_3day_reminder BOOLEAN DEFAULT 0,
    posted_last_day BOOLEAN DEFAULT 0,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (comment_end_date >= posted_date)
)
""")

print("Copying data...")
cursor.execute("INSERT INTO comment_periods_new SELECT * FROM comment_periods")

print("Dropping old table...")
cursor.execute("DROP TABLE comment_periods")

print("Renaming new table...")
cursor.execute("ALTER TABLE comment_periods_new RENAME TO comment_periods")

print("Creating indexes...")
cursor.execute("CREATE UNIQUE INDEX idx_document_id ON comment_periods(document_id)")
cursor.execute("CREATE INDEX idx_posted_date ON comment_periods(posted_date)")
cursor.execute("CREATE INDEX idx_comment_end_date ON comment_periods(comment_end_date)")
cursor.execute("CREATE INDEX idx_agency_id ON comment_periods(agency_id)")

conn.commit()
conn.close()

print("✅ Migration complete! docket_id is now optional.")
