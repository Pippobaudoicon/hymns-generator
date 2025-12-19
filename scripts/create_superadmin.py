#!/usr/bin/env python3
"""
Script to create the initial superadmin user.

Run this script after setting up the database to create the first admin account.

Usage:
    python scripts/create_superadmin.py
    
Or with arguments:
    python scripts/create_superadmin.py --username admin --email admin@example.com --password secretpassword
"""

import argparse
import getpass
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from auth.models import User, UserRole
from auth.utils import get_password_hash
from database.database import get_db_manager


def create_superadmin(username: str, email: str, password: str, full_name: str = None) -> dict:
    """Create a superadmin user."""
    db_manager = get_db_manager()
    
    with db_manager.get_session_context() as db:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return {"error": f"Username '{username}' already exists"}
            else:
                return {"error": f"Email '{email}' already exists"}
        
        # Create superadmin user
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=UserRole.SUPERADMIN.value,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }


def main():
    parser = argparse.ArgumentParser(description="Create the initial superadmin user")
    parser.add_argument("--username", "-u", help="Admin username")
    parser.add_argument("--email", "-e", help="Admin email")
    parser.add_argument("--password", "-p", help="Admin password (will prompt if not provided)")
    parser.add_argument("--full-name", "-n", help="Admin full name (optional)")
    
    args = parser.parse_args()
    
    # Interactive mode if arguments not provided
    username = args.username
    if not username:
        username = input("Enter superadmin username: ").strip()
        if not username:
            print("Error: Username is required")
            sys.exit(1)
    
    email = args.email
    if not email:
        email = input("Enter superadmin email: ").strip()
        if not email:
            print("Error: Email is required")
            sys.exit(1)
    
    password = args.password
    if not password:
        password = getpass.getpass("Enter superadmin password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match")
            sys.exit(1)
    
    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)
    
    full_name = args.full_name
    if not full_name:
        full_name = input("Enter full name (optional, press Enter to skip): ").strip() or None
    
    print(f"\nCreating superadmin user '{username}'...")
    
    result = create_superadmin(username, email, password, full_name)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    print(f"\n✅ Superadmin user created successfully!")
    print(f"   User ID: {result['user_id']}")
    print(f"   Username: {result['username']}")
    print(f"   Email: {result['email']}")
    print(f"   Role: {result['role']}")
    print(f"\nYou can now login with these credentials at POST /api/v1/auth/login")


if __name__ == "__main__":
    main()
