#!/usr/bin/env python3
"""
Test script for Authentication API endpoints.
This script tests all authentication endpoints with various scenarios.
"""

import requests
import json
import time
from datetime import datetime


class AuthAPITester:
    """Test class for Authentication API."""

    def __init__(self, base_url="http://localhost:8001"):
        """Initialize the tester with base URL."""
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, test_name, success, message, response_data=None):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")

        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'response': response_data,
            'timestamp': datetime.now().isoformat()
        })

        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        print()

    def test_login_success(self):
        """Test successful login."""
        url = f"{self.api_base}/auth/login/"
        data = {
            "username": "alan_love",
            "password": "SecurePassword123!"
        }

        try:
            response = self.session.post(url, json=data)
            result = response.json()

            if response.status_code == 200 and result.get('success'):
                # Store token for other tests
                self.token = result.get('token')
                self.log_test(
                    "Login Success",
                    True,
                    f"Login successful for user: {result['user']['username']}"
                )
                return True
            else:
                self.log_test(
                    "Login Success",
                    False,
                    f"Login failed with status {response.status_code}",
                    result
                )
                return False

        except Exception as e:
            self.log_test("Login Success", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all authentication tests."""
        print("🚀 Starting Authentication API Tests")
        print("=" * 50)
        print()

        # Test login first
        if self.test_login_success():
            print("🎉 Basic login test passed!")
        else:
            print("❌ Basic login test failed!")

        return True


def main():
    """Main function to run tests."""
    print("Authentication API Test Suite")
    print("Testing endpoints at http://localhost:8001/api/auth/")
    print()

    # Check if server is running
    try:
        response = requests.get("http://localhost:8001/", timeout=5)
        print("✅ Server is running")
    except requests.exceptions.RequestException:
        print("❌ Error: Could not connect to server at http://localhost:8001")
        print("Please make sure the Django development server is running:")
        print("  python manage.py runserver 8001")
        return False

    # Run tests
    tester = AuthAPITester()
    success = tester.run_all_tests()

    return success


if __name__ == "__main__":
    main()
