"""
Database migration to add authentication tables.

This migration adds:
- users table
- areas table  
- stakes table
- user_ward_assignments table (many-to-many)
- stake_id column to wards table
"""

import logging
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, text
from sqlalchemy.orm import Session

from database.models import Base, Ward

logger = logging.getLogger(__name__)


def check_table_exists(db: Session, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        result = db.execute(
            text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        )
        return result.fetchone() is not None
    except Exception:
        return False


def check_column_exists(db: Session, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        result = db.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]
        return column_name in columns
    except Exception:
        return False


def run_migration(db: Session) -> dict:
    """
    Run the authentication migration.
    
    Returns:
        dict with migration results
    """
    results = {
        "tables_created": [],
        "columns_added": [],
        "errors": [],
        "skipped": []
    }
    
    try:
        # Create areas table
        if not check_table_exists(db, "areas"):
            db.execute(text("""
                CREATE TABLE areas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            db.execute(text("CREATE INDEX ix_areas_name ON areas (name)"))
            results["tables_created"].append("areas")
            logger.info("Created areas table")
        else:
            results["skipped"].append("areas table already exists")
        
        # Create stakes table
        if not check_table_exists(db, "stakes"):
            db.execute(text("""
                CREATE TABLE stakes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    area_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (area_id) REFERENCES areas (id) ON DELETE SET NULL
                )
            """))
            db.execute(text("CREATE INDEX ix_stakes_name ON stakes (name)"))
            db.execute(text("CREATE INDEX ix_stakes_area_id ON stakes (area_id)"))
            results["tables_created"].append("stakes")
            logger.info("Created stakes table")
        else:
            results["skipped"].append("stakes table already exists")
        
        # Add stake_id column to wards table
        if check_table_exists(db, "wards"):
            if not check_column_exists(db, "wards", "stake_id"):
                db.execute(text("""
                    ALTER TABLE wards ADD COLUMN stake_id INTEGER 
                    REFERENCES stakes (id) ON DELETE SET NULL
                """))
                results["columns_added"].append("wards.stake_id")
                logger.info("Added stake_id column to wards table")
            else:
                results["skipped"].append("wards.stake_id column already exists")
        
        # Create users table
        if not check_table_exists(db, "users"):
            db.execute(text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(255) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    hashed_password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    role VARCHAR(50) NOT NULL DEFAULT 'ward_user',
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    area_id INTEGER,
                    stake_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (area_id) REFERENCES areas (id) ON DELETE SET NULL,
                    FOREIGN KEY (stake_id) REFERENCES stakes (id) ON DELETE SET NULL
                )
            """))
            db.execute(text("CREATE INDEX ix_users_username ON users (username)"))
            db.execute(text("CREATE INDEX ix_users_email ON users (email)"))
            results["tables_created"].append("users")
            logger.info("Created users table")
        else:
            results["skipped"].append("users table already exists")
        
        # Create user_ward_assignments table (many-to-many)
        if not check_table_exists(db, "user_ward_assignments"):
            db.execute(text("""
                CREATE TABLE user_ward_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    ward_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (ward_id) REFERENCES wards (id) ON DELETE CASCADE,
                    UNIQUE (user_id, ward_id)
                )
            """))
            db.execute(text("CREATE INDEX ix_user_ward_user_id ON user_ward_assignments (user_id)"))
            db.execute(text("CREATE INDEX ix_user_ward_ward_id ON user_ward_assignments (ward_id)"))
            results["tables_created"].append("user_ward_assignments")
            logger.info("Created user_ward_assignments table")
        else:
            results["skipped"].append("user_ward_assignments table already exists")
        
        db.commit()
        logger.info("Authentication migration completed successfully")
        
    except Exception as e:
        db.rollback()
        error_msg = f"Migration failed: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(error_msg)
        raise
    
    return results


def rollback_migration(db: Session) -> dict:
    """
    Rollback the authentication migration.
    
    WARNING: This will delete all authentication data!
    
    Returns:
        dict with rollback results
    """
    results = {
        "tables_dropped": [],
        "columns_removed": [],
        "errors": []
    }
    
    try:
        # Drop in reverse order due to foreign key constraints
        
        # Drop user_ward_assignments table
        if check_table_exists(db, "user_ward_assignments"):
            db.execute(text("DROP TABLE user_ward_assignments"))
            results["tables_dropped"].append("user_ward_assignments")
        
        # Drop users table
        if check_table_exists(db, "users"):
            db.execute(text("DROP TABLE users"))
            results["tables_dropped"].append("users")
        
        # Remove stake_id from wards (SQLite doesn't support DROP COLUMN easily)
        # Would need to recreate the table - skipping for now
        results["columns_removed"].append("wards.stake_id (manual removal may be needed)")
        
        # Drop stakes table
        if check_table_exists(db, "stakes"):
            db.execute(text("DROP TABLE stakes"))
            results["tables_dropped"].append("stakes")
        
        # Drop areas table
        if check_table_exists(db, "areas"):
            db.execute(text("DROP TABLE areas"))
            results["tables_dropped"].append("areas")
        
        db.commit()
        logger.info("Authentication migration rollback completed")
        
    except Exception as e:
        db.rollback()
        error_msg = f"Rollback failed: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(error_msg)
        raise
    
    return results


if __name__ == "__main__":
    """Run migration from command line."""
    import sys

    from database.database import get_db_manager
    
    logging.basicConfig(level=logging.INFO)
    
    db_manager = get_db_manager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("Rolling back authentication migration...")
        with db_manager.get_session_context() as db:
            results = rollback_migration(db)
    else:
        print("Running authentication migration...")
        with db_manager.get_session_context() as db:
            results = run_migration(db)
    
    print("\nMigration Results:")
    for key, value in results.items():
        if value:
            print(f"  {key}: {value}")
