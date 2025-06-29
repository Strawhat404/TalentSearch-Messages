#!/usr/bin/env python3
"""
Database connection test script
Run this to test if your database connection is working properly
"""

import os
import sys
import django
from urllib.parse import urlparse

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talentsearch.settings.prod')
django.setup()

from django.conf import settings
from django.db import connection
from django.db.utils import OperationalError

def test_database_connection():
    """Test the database connection and show configuration details"""
    print("=== Database Connection Test ===")
    
    # Check environment variables
    database_url = os.environ.get('DATABASE_URL')
    print(f"DATABASE_URL set: {bool(database_url)}")
    
    if database_url:
        # Parse the URL to show details (without password)
        try:
            parsed = urlparse(database_url)
            print(f"Database URL format: {parsed.scheme}://{parsed.username}@{parsed.hostname}:{parsed.port}{parsed.path}")
            print(f"Username: {parsed.username}")
            print(f"Host: {parsed.hostname}")
            print(f"Port: {parsed.port}")
            print(f"Database: {parsed.path[1:] if parsed.path else 'None'}")
            print(f"Password provided: {'Yes' if parsed.password else 'No'}")
        except Exception as e:
            print(f"Error parsing DATABASE_URL: {e}")
    
    # Show Django database configuration
    print(f"\nDjango Database Configuration:")
    db_config = settings.DATABASES['default']
    print(f"Engine: {db_config.get('ENGINE')}")
    print(f"Name: {db_config.get('NAME')}")
    print(f"Host: {db_config.get('HOST')}")
    print(f"Port: {db_config.get('PORT')}")
    print(f"User: {db_config.get('USER')}")
    print(f"Password: {'Set' if db_config.get('PASSWORD') else 'Not set'}")
    print(f"SSL Mode: {db_config.get('OPTIONS', {}).get('sslmode', 'Not set')}")
    
    # Test connection
    print(f"\nTesting connection...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Connection successful! Test query result: {result}")
            return True
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1) 