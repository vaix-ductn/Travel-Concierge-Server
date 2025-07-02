from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json
import uuid

from .models import UserProfile


class UserProfileModelTest(TestCase):
    """Test UserProfile model functionality"""

    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'address': 'Test Address',
            'interests': 'Travel, Food',
            'passport_nationality': 'American',
            'seat_preference': 'aisle',
            'food_preference': 'No restrictions',
            'allergies': ['peanuts'],
            'likes': ['beaches', 'mountains'],
            'dislikes': ['crowded places'],
            'price_sensitivity': ['mid-range'],
            'home_address': 'Home Address',
            'local_prefer_mode': 'car'
        }

    def test_create_user_profile(self):
        """Test creating a user profile"""
        profile = UserProfile.objects.create(**self.user_data)
        profile.set_password('testpass123')
        profile.save()

        self.assertEqual(profile.username, 'testuser')
        self.assertEqual(profile.email, 'test@example.com')
        self.assertIsInstance(profile.profile_uuid, uuid.UUID)
        self.assertTrue(profile.check_password('testpass123'))

    def test_user_profile_str(self):
        """Test string representation"""
        profile = UserProfile.objects.create(**self.user_data)
        expected = f"{profile.username} ({profile.email})"
        self.assertEqual(str(profile), expected)

    def test_to_dict_method(self):
        """Test to_dict conversion"""
        profile = UserProfile.objects.create(**self.user_data)
        profile_dict = profile.to_dict()

        self.assertIn('profile_uuid', profile_dict)
        self.assertEqual(profile_dict['username'], 'testuser')
        self.assertEqual(profile_dict['email'], 'test@example.com')
        self.assertEqual(profile_dict['likes'], ['beaches', 'mountains'])

    def test_password_hashing(self):
        """Test password hashing and checking"""
        profile = UserProfile.objects.create(**self.user_data)
        profile.set_password('mypassword123')

        # Password should be hashed
        self.assertNotEqual(profile.password_hash, 'mypassword123')
        # But should verify correctly
        self.assertTrue(profile.check_password('mypassword123'))
        # Wrong password should fail
        self.assertFalse(profile.check_password('wrongpassword'))

    def test_get_ai_context(self):
        """Test AI context generation"""
        profile = UserProfile.objects.create(**self.user_data)
        ai_context = profile.get_ai_context()

        self.assertIn('user_scenario', ai_context)
        self.assertEqual(ai_context['user_scenario']['user_uuid'], str(profile.profile_uuid))
        self.assertEqual(ai_context['user_scenario']['user_name'], 'testuser')
        self.assertIn('user_preferences', ai_context['user_scenario'])


class UserProfileAPITest(TestCase):
    """Test UserProfile API endpoints"""

    def setUp(self):
        """Set up test client and data"""
        self.client = Client()

        # Create test profile
        self.profile = UserProfile.objects.create(
            username='apitest',
            email='apitest@example.com',
            address='API Test Address',
            interests='API Testing',
            passport_nationality='Canadian',
            seat_preference='window',
            food_preference='Vegetarian',
            allergies=['shellfish'],
            likes=['technology', 'innovation'],
            dislikes=['bugs'],
            price_sensitivity=['budget'],
            home_address='Home Test Address',
            local_prefer_mode='bike'
        )
        self.profile.set_password('apitest123')
        self.profile.save()

    def test_list_profiles_api(self):
        """Test list profiles endpoint"""
        url = reverse('user_manager:list_profiles')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['username'], 'apitest')

    def test_get_profile_api(self):
        """Test get specific profile endpoint"""
        url = reverse('user_manager:get_profile', kwargs={'profile_uuid': self.profile.profile_uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['username'], 'apitest')
        self.assertEqual(data['data']['profile_uuid'], str(self.profile.profile_uuid))

    def test_get_profile_not_found(self):
        """Test get profile with invalid UUID"""
        invalid_uuid = uuid.uuid4()
        url = reverse('user_manager:get_profile', kwargs={'profile_uuid': invalid_uuid})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_update_profile_api(self):
        """Test update profile endpoint"""
        url = reverse('user_manager:update_profile', kwargs={'profile_uuid': self.profile.profile_uuid})
        update_data = {
            'username': 'apitest_updated',
            'interests': 'Updated API Testing',
            'likes': ['technology', 'innovation', 'testing']
        }

        response = self.client.put(
            url,
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['username'], 'apitest_updated')
        self.assertEqual(data['data']['interests'], 'Updated API Testing')

        # Verify database was updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.username, 'apitest_updated')

    def test_change_password_api(self):
        """Test change password endpoint"""
        url = reverse('user_manager:change_password', kwargs={'profile_uuid': self.profile.profile_uuid})
        password_data = {
            'current_password': 'apitest123',
            'new_password': 'NewPassword@2024',
            'confirm_password': 'NewPassword@2024'
        }

        response = self.client.put(
            url,
            data=json.dumps(password_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Verify password was changed
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.check_password('NewPassword@2024'))
        self.assertFalse(self.profile.check_password('apitest123'))

    def test_change_password_wrong_current(self):
        """Test change password with wrong current password"""
        url = reverse('user_manager:change_password', kwargs={'profile_uuid': self.profile.profile_uuid})
        password_data = {
            'current_password': 'wrongpassword',
            'new_password': 'NewPassword@2024',
            'confirm_password': 'NewPassword@2024'
        }

        response = self.client.put(
            url,
            data=json.dumps(password_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Current password is incorrect', data['error'])

    def test_create_profile_api(self):
        """Test create profile endpoint"""
        url = reverse('user_manager:create_profile')
        profile_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewUser@2024',
            'address': 'New User Address',
            'interests': 'New Interests',
            'passport_nationality': 'British',
            'seat_preference': 'aisle',
            'food_preference': 'No preference',
            'allergies': [],
            'likes': ['culture', 'history'],
            'dislikes': ['noise'],
            'price_sensitivity': ['luxury'],
            'home_address': 'New Home Address',
            'local_prefer_mode': 'walk'
        }

        response = self.client.post(
            url,
            data=json.dumps(profile_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['username'], 'newuser')
        self.assertIn('profile_uuid', data['data'])

        # Verify profile was created in database
        new_profile = UserProfile.objects.get(email='newuser@example.com')
        self.assertEqual(new_profile.username, 'newuser')
        self.assertTrue(new_profile.check_password('NewUser@2024'))

    def test_create_profile_duplicate_email(self):
        """Test create profile with duplicate email"""
        url = reverse('user_manager:create_profile')
        profile_data = {
            'username': 'duplicate',
            'email': 'apitest@example.com',  # Same as existing profile
            'password': 'Duplicate@2024',
            'address': 'Duplicate Address',
            'interests': 'Duplicate Interests'
        }

        response = self.client.post(
            url,
            data=json.dumps(profile_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('errors', data)


class UserProfileURLTest(TestCase):
    """Test URL routing for user profile endpoints"""

    def setUp(self):
        """Set up test profile"""
        self.profile = UserProfile.objects.create(
            username='urltest',
            email='urltest@example.com',
            address='URL Test Address',
            interests='URL Testing'
        )

    def test_profile_urls_resolve(self):
        """Test that all profile URLs resolve correctly"""
        # Test list profiles URL
        url = reverse('user_manager:list_profiles')
        self.assertEqual(url, '/api/user_manager/profiles/')

        # Test get profile URL
        url = reverse('user_manager:get_profile', kwargs={'profile_uuid': self.profile.profile_uuid})
        expected = f'/api/user_manager/profile/{self.profile.profile_uuid}/'
        self.assertEqual(url, expected)

        # Test update profile URL
        url = reverse('user_manager:update_profile', kwargs={'profile_uuid': self.profile.profile_uuid})
        expected = f'/api/user_manager/profile/{self.profile.profile_uuid}/update/'
        self.assertEqual(url, expected)

        # Test change password URL
        url = reverse('user_manager:change_password', kwargs={'profile_uuid': self.profile.profile_uuid})
        expected = f'/api/user_manager/profile/{self.profile.profile_uuid}/change-password/'
        self.assertEqual(url, expected)

        # Test create profile URL
        url = reverse('user_manager:create_profile')
        self.assertEqual(url, '/api/user_manager/profile/create/')