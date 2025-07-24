#!/usr/bin/env python3
"""
Database Connection Test Script
Tests MySQL database connectivity and PyMySQL installation
"""
import os
import sys
import traceback

def test_pymysql_import():
    """Test if pymysql can be imported"""
    try:
        import pymysql
        print(f"✅ PyMySQL imported successfully - version: {pymysql.__version__}")
        return True
    except ImportError as e:
        print(f"❌ PyMySQL import failed: {e}")
        return False

def test_database_connection():
    """Test database connection using environment variables"""
    try:
        import pymysql

        # Get database configuration from environment
        db_config = {
            'host': os.getenv('DB_HOST', '104.198.165.249'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'travel_concierge'),
            'password': os.getenv('DB_PASSWORD', 'TravelConcierge2024!'),
            'database': os.getenv('DB_NAME', 'travel_concierge'),
            'charset': 'utf8mb4'
        }

        print(f"🔌 Testing connection to: {db_config['host']}:{db_config['port']}")
        print(f"📊 Database: {db_config['database']}")
        print(f"👤 User: {db_config['user']}")

        # Attempt connection
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # Test query
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()

        print(f"✅ Database connection successful!")
        print(f"🔧 MySQL version: {version[0]}")

        # Test if user_manager tables exist
        cursor.execute("SHOW TABLES LIKE 'user_manager_%'")
        tables = cursor.fetchall()
        print(f"📋 User manager tables found: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")

        cursor.close()
        connection.close()
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def test_django_settings():
    """Test Django settings import"""
    try:
        # Add project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)

        # Set Django settings module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

        import django
        django.setup()

        from django.conf import settings
        print(f"✅ Django settings loaded successfully")
        print(f"🔧 Database engine: {settings.DATABASES['default']['ENGINE']}")
        print(f"🏠 Database host: {settings.DATABASES['default']['HOST']}")
        print(f"📊 Database name: {settings.DATABASES['default']['NAME']}")

        return True

    except Exception as e:
        print(f"❌ Django settings failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 DATABASE CONNECTION TEST")
    print("=" * 60)

    # Test 1: PyMySQL import
    print("\n📦 Test 1: PyMySQL Import")
    pymysql_ok = test_pymysql_import()

    # Test 2: Database connection
    print("\n🔌 Test 2: Database Connection")
    db_ok = test_database_connection()

    # Test 3: Django settings
    print("\n⚙️  Test 3: Django Settings")
    django_ok = test_django_settings()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"PyMySQL Import: {'✅ PASS' if pymysql_ok else '❌ FAIL'}")
    print(f"Database Connection: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"Django Settings: {'✅ PASS' if django_ok else '❌ FAIL'}")

    all_tests_passed = pymysql_ok and db_ok and django_ok
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")

    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())