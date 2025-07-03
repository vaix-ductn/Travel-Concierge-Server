"""Tests for authentication system."""

import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache

from ..models import User, UserToken
from ..service import AuthService, TokenService


class AuthenticationTestCase(TestCase):
    """Test case for authentication functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        cache.clear()  # Clear cache before each test

        # Create test user
        self.test_user = AuthService.create_user(
            username='alan_love',
            email='alanlovelq@gmail.com',
            password='SecurePassword123!',
            full_name='Alan Love',
            address='Ha Noi, Viet Nam',
            interests=['Travel', 'Photography', 'Food']
        )

        # URLs
        self.login_url = '/api/auth/login/'
        self.verify_url = '/api/auth/verify/'
        self.logout_url = '/api/auth/logout/'

    def test_login_success(self):
        """Test successful login."""
        data = {
            'username': 'alan_love',
            'password': 'SecurePassword123!'
        }

        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Login successful')
        self.assertIn('token', response_data)
        self.assertIn('user', response_data)

        # Check user data
        user_data = response_data['user']
        self.assertEqual(user_data['username'], 'alan_love')
        self.assertEqual(user_data['email'], 'alanlovelq@gmail.com')
        self.assertEqual(user_data['full_name'], 'Alan Love')

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            'username': 'alan_love',
            'password': 'wrongpassword'
        }

        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        response_data = response.json()

        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], 'Invalid username or password')

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        data = {
            'username': 'alan_love'
            # Missing password
        }

        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        response_data = response.json()

        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], 'Invalid input data')

    def test_login_invalid_username_format(self):
        """Test login with invalid username format."""
        data = {
            'username': 'ab',  # Too short
            'password': 'SecurePassword123!'
        }

        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_token_verification_success(self):
        """Test successful token verification."""
        # First login to get token
        token = TokenService.generate_token(self.test_user)

        response = self.client.get(
            self.verify_url,
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Token is valid')
        self.assertIn('user', response_data)

    def test_token_verification_invalid_token(self):
        """Test token verification with invalid token."""
        response = self.client.get(
            self.verify_url,
            HTTP_AUTHORIZATION='Bearer invalid.token.here'
        )

        self.assertEqual(response.status_code, 401)
        response_data = response.json()

        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], 'Invalid or expired token')

    def test_token_verification_missing_header(self):
        """Test token verification without authorization header."""
        response = self.client.get(self.verify_url)

        self.assertEqual(response.status_code, 401)
        response_data = response.json()

        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], 'Authorization header is required')

    def test_logout_success(self):
        """Test successful logout."""
        # First login to get token
        token = TokenService.generate_token(self.test_user)

        response = self.client.post(
            self.logout_url,
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Logout successful')

        # Verify token is invalidated
        verify_response = self.client.get(
            self.verify_url,
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        self.assertEqual(verify_response.status_code, 401)

    def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        response = self.client.post(
            self.logout_url,
            HTTP_AUTHORIZATION='Bearer invalid.token.here'
        )

        self.assertEqual(response.status_code, 401)
        response_data = response.json()

        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], 'Invalid or expired token')

    def test_account_lockout(self):
        """Test account lockout after multiple failed attempts."""
        data = {
            'username': 'alan_love',
            'password': 'wrongpassword'
        }

        # Make 5 failed attempts
        for i in range(5):
            response = self.client.post(
                self.login_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 401)

        # 6th attempt should result in account lockout
        response = self.client.post(
            self.login_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('locked', response_data['message'].lower())

    def test_rate_limiting(self):
        """Test rate limiting for login attempts."""
        data = {
            'username': 'nonexistent',
            'password': 'wrongpassword'
        }

        # Make multiple failed attempts from same IP
        for i in range(6):  # Exceed rate limit
            response = self.client.post(
                self.login_url,
                data=json.dumps(data),
                content_type='application/json',
                REMOTE_ADDR='192.168.1.100'
            )

            if i < 5:
                self.assertEqual(response.status_code, 401)
            else:
                # Should get rate limited
                self.assertEqual(response.status_code, 429)
                response_data = response.json()
                self.assertIn('too many', response_data['message'].lower())


class UserModelTestCase(TestCase):
    """Test case for User model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User(
            username='testuser',
            email='test@example.com'
        )
        self.user.set_password('testpassword123')
        self.user.save()

    def test_password_hashing(self):
        """Test password hashing and verification."""
        # Password should be hashed
        self.assertNotEqual(self.user.password_hash, 'testpassword123')

        # Should be able to verify correct password
        self.assertTrue(self.user.check_password('testpassword123'))

        # Should reject incorrect password
        self.assertFalse(self.user.check_password('wrongpassword'))

    def test_account_locking(self):
        """Test account locking functionality."""
        # Initially not locked
        self.assertFalse(self.user.is_locked())

        # Lock account
        self.user.lock_account(duration_minutes=30)
        self.assertTrue(self.user.is_locked())

        # Unlock account
        self.user.unlock_account()
        self.assertFalse(self.user.is_locked())

    def test_failed_attempts_tracking(self):
        """Test failed login attempts tracking."""
        self.assertEqual(self.user.failed_login_attempts, 0)

        # Increment failed attempts
        self.user.increment_failed_attempts()
        self.assertEqual(self.user.failed_login_attempts, 1)

        # Reset on successful login
        self.user.reset_failed_attempts()
        self.assertEqual(self.user.failed_login_attempts, 0)

    def test_to_dict(self):
        """Test user to_dict method."""
        user_dict = self.user.to_dict()

        expected_fields = ['id', 'username', 'email', 'full_name', 'avatar_url', 'address', 'interests']
        for field in expected_fields:
            self.assertIn(field, user_dict)

        self.assertEqual(user_dict['username'], 'testuser')
        self.assertEqual(user_dict['email'], 'test@example.com')


class TokenServiceTestCase(TestCase):
    """Test case for TokenService functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User(
            username='testuser',
            email='test@example.com'
        )
        self.user.set_password('testpassword123')
        self.user.save()

    def test_token_generation(self):
        """Test JWT token generation."""
        token = TokenService.generate_token(self.user)

        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split('.')), 3)  # JWT has 3 parts

        # Should create UserToken record
        user_token = UserToken.objects.get(user=self.user)
        self.assertTrue(user_token.is_active)

    def test_token_verification(self):
        """Test JWT token verification."""
        token = TokenService.generate_token(self.user)

        user, payload = TokenService.verify_token(token)

        self.assertEqual(user.id, self.user.id)
        self.assertEqual(payload['username'], self.user.username)

    def test_token_invalidation(self):
        """Test token invalidation."""
        token = TokenService.generate_token(self.user)

        # Token should be valid initially
        user, payload = TokenService.verify_token(token)
        self.assertEqual(user.id, self.user.id)

        # Invalidate token
        TokenService.invalidate_token(token)

        # Token should now be invalid
        with self.assertRaises(Exception):
            TokenService.verify_token(token)

    def test_cleanup_expired_tokens(self):
        """Test cleanup of expired tokens."""
        # Create expired token
        expired_token = UserToken.objects.create(
            user=self.user,
            token_hash='expired_hash',
            expires_at=timezone.now() - timedelta(hours=1)
        )

        # Create valid token
        valid_token = UserToken.objects.create(
            user=self.user,
            token_hash='valid_hash',
            expires_at=timezone.now() + timedelta(hours=1)
        )

        # Cleanup should remove expired token
        count = TokenService.cleanup_expired_tokens()
        self.assertEqual(count, 1)

        # Valid token should still exist
        self.assertTrue(UserToken.objects.filter(id=valid_token.id).exists())

        # Expired token should be removed
        self.assertFalse(UserToken.objects.filter(id=expired_token.id).exists())