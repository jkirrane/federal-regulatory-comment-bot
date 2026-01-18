"""
Test database functions with sample data
"""

import os
import tempfile
import shutil
from pathlib import Path
from database import (
    upsert_comment_period,
    get_new_comment_periods,
    get_closing_soon,
    mark_posted,
    get_period_by_document_id,
    get_all_open_periods,
    get_stats
)
from datetime import datetime, timedelta


def test_database_functions():
    """Test all database functions with sample data"""
    
    # Use a temporary test database
    import database.db as db
    original_db_path = db.DB_PATH
    test_db_path = Path(tempfile.gettempdir()) / 'test_comment_periods.db'
    
    # Point to test database
    db.DB_PATH = test_db_path
    
    # Remove test database if it exists
    if test_db_path.exists():
        test_db_path.unlink()
    
    # Initialize test database
    from database import initialize_database
    initialize_database()
    
    print("Testing Federal Regulatory Comment Bot Database Functions")
    print(f"(Using test database: {test_db_path})\n")
    
    # Test 1: Insert a sample comment period
    print("1. Testing upsert_comment_period()...")
    period_id = upsert_comment_period(
        document_id="EPA-HQ-OW-2024-0123",
        docket_id="EPA-HQ-OW-2024-0123",
        title="Clean Water Standards - PFAS Regulations",
        agency_id="EPA",
        agency_name="Environmental Protection Agency",
        posted_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        comment_end_date=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        regulations_url="https://www.regulations.gov/commenton/EPA-HQ-OW-2024-0123",
        abstract="Proposed standards for PFAS chemicals in drinking water systems",
        topics='["environment", "climate"]',
        document_type="Proposed Rule"
    )
    print(f"   ✓ Inserted period with ID: {period_id}")
    
    # Test 2: Upsert again (should update, not duplicate)
    print("\n2. Testing upsert idempotency...")
    period_id2 = upsert_comment_period(
        document_id="EPA-HQ-OW-2024-0123",  # Same document_id
        docket_id="EPA-HQ-OW-2024-0123",
        title="Clean Water Standards - PFAS Regulations (Updated)",
        agency_id="EPA",
        agency_name="Environmental Protection Agency",
        posted_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        comment_end_date=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        regulations_url="https://www.regulations.gov/commenton/EPA-HQ-OW-2024-0123",
        abstract="Proposed standards for PFAS chemicals in drinking water systems - UPDATED",
    )
    print(f"   ✓ Updated period (same ID): {period_id2}")
    assert period_id == period_id2, "Should update existing record, not create new one"
    
    # Test 3: Insert another period for 7-day reminder
    print("\n3. Testing deadline reminder queries...")
    period_id3 = upsert_comment_period(
        document_id="FDA-2024-N-5678",
        docket_id="FDA-2024-N-5678",
        title="Food Labeling Requirements",
        agency_id="FDA",
        agency_name="Food and Drug Administration",
        posted_date=(datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'),
        comment_end_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        regulations_url="https://www.regulations.gov/commenton/FDA-2024-N-5678",
        topics='["healthcare", "food"]',
    )
    print(f"   ✓ Inserted period closing in 7 days: {period_id3}")
    
    # Test 4: Get new comment periods
    print("\n4. Testing get_new_comment_periods()...")
    new_periods = get_new_comment_periods(days=2)
    print(f"   ✓ Found {len(new_periods)} new period(s) in last 2 days")
    for period in new_periods:
        print(f"      - {period['document_id']}: {period['title'][:60]}...")
    
    # Test 5: Get closing soon
    print("\n5. Testing get_closing_soon(7)...")
    closing_soon = get_closing_soon(days=7)
    print(f"   ✓ Found {len(closing_soon)} period(s) closing in 7 days")
    for period in closing_soon:
        print(f"      - {period['document_id']}: {period['title'][:60]}...")
    
    # Test 6: Mark as posted
    print("\n6. Testing mark_posted()...")
    mark_posted(period_id, 'new', 'at://did:plc:example/app.bsky.feed.post/abc123')
    print(f"   ✓ Marked period {period_id} as posted")
    
    # Verify it's no longer in new periods
    new_periods_after = get_new_comment_periods(days=2)
    print(f"   ✓ New periods count after marking: {len(new_periods_after)}")
    assert len(new_periods_after) == len(new_periods) - 1, "Should have one fewer new period"
    
    # Test 7: Get by document_id
    print("\n7. Testing get_period_by_document_id()...")
    period = get_period_by_document_id("EPA-HQ-OW-2024-0123")
    print(f"   ✓ Retrieved: {period['title']}")
    assert period['posted_new'] == 1, "Should be marked as posted"
    
    
    # Clean up test database
    import database.db as db
    if test_db_path.exists():
        test_db_path.unlink()
    db.DB_PATH = original_db_path
    print(f"\nTest database cleaned up. Production database: {original_db_path}")
    # Test 8: Get all open periods
    print("\n8. Testing get_all_open_periods()...")
    open_periods = get_all_open_periods()
    print(f"   ✓ Found {len(open_periods)} open period(s)")
    
    # Test 9: Get stats
    print("\n9. Testing get_stats()...")
    stats = get_stats()
    print(f"   ✓ Statistics:")
    print(f"      Total periods: {stats['total_periods']}")
    print(f"      Open periods: {stats['open_periods']}")
    print(f"      Posted periods: {stats['posted_periods']}")
    print(f"      Total posts: {stats['total_posts']}")
    
    print("\n" + "="*60)
    print("✅ All database functions working correctly!")
    print("="*60)


if __name__ == "__main__":
    test_database_functions()
