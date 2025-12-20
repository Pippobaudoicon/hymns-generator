"""Migration script to add updated_at column to hymn_selections table.

This migration adds the updated_at column to track when records are modified,
since selection_date now represents the Sunday date (future date) rather than
the creation timestamp.

Run this migration after updating the code to ensure the database schema matches.
"""

import sqlite3
from pathlib import Path


def migrate_database(db_path: str = "data/hymns_history.db"):
    """
    Add updated_at column to hymn_selections table.

    Args:
        db_path: Path to the SQLite database file
    """
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"Database file not found: {db_path}")
        print("No migration needed - database will be created with the new schema.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if updated_at column already exists
        cursor.execute("PRAGMA table_info(hymn_selections)")
        columns = [row[1] for row in cursor.fetchall()]

        if "updated_at" in columns:
            print("✓ Column 'updated_at' already exists. No migration needed.")
            return

        print("Adding 'updated_at' column to hymn_selections table...")

        # Add the updated_at column with default value
        # SQLite doesn't support adding columns with DEFAULT that uses functions,
        # so we add it as NULL first, then update
        cursor.execute(
            """
            ALTER TABLE hymn_selections
            ADD COLUMN updated_at TIMESTAMP
        """
        )

        # Set updated_at to created_at for existing records
        cursor.execute(
            """
            UPDATE hymn_selections
            SET updated_at = created_at
            WHERE updated_at IS NULL
        """
        )

        conn.commit()
        print("✓ Successfully added 'updated_at' column")
        print("✓ Initialized existing records with created_at values")

        # Show statistics
        cursor.execute("SELECT COUNT(*) FROM hymn_selections")
        count = cursor.fetchone()[0]
        print(f"✓ Updated {count} existing records")

    except sqlite3.Error as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


def verify_migration(db_path: str = "data/hymns_history.db"):
    """
    Verify that the migration was successful.

    Args:
        db_path: Path to the SQLite database file
    """
    db_file = Path(db_path)

    if not db_file.exists():
        print("Database file not found. Cannot verify migration.")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if updated_at column exists
        cursor.execute("PRAGMA table_info(hymn_selections)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        if "updated_at" not in columns:
            print("✗ Verification failed: 'updated_at' column not found")
            return False

        print("✓ Column 'updated_at' exists")
        print(f"  Type: {columns['updated_at']}")

        # Check if existing records have updated_at values
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM hymn_selections
            WHERE updated_at IS NULL
        """
        )
        null_count = cursor.fetchone()[0]

        if null_count > 0:
            print(f"⚠ Warning: {null_count} records have NULL updated_at values")
            return False

        cursor.execute("SELECT COUNT(*) FROM hymn_selections")
        total_count = cursor.fetchone()[0]
        print(f"✓ All {total_count} records have updated_at values")

        return True

    except sqlite3.Error as e:
        print(f"✗ Verification failed: {e}")
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/hymns_history.db"

    print("=" * 60)
    print("Database Migration: Add updated_at column")
    print("=" * 60)
    print(f"Database: {db_path}")
    print()

    # Run migration
    migrate_database(db_path)
    print()

    # Verify migration
    print("Verifying migration...")
    if verify_migration(db_path):
        print()
        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("✗ Migration verification failed!")
        print("=" * 60)
        sys.exit(1)
