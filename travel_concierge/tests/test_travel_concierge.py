"""
Tests for Travel Concierge app
Updated to work with refactored structure
"""

from django.test import TestCase, Client
from django.urls import reverse
import json

from ..service.agent_service import AgentService
from ..service.travel_service import TravelService


class TravelConciergeServiceTest(TestCase):
    """Test Travel Concierge service functionality"""

    def setUp(self):
        """Set up test data"""
        self.agent_service = AgentService()
        self.travel_service = TravelService()

    def test_agent_service_initialization(self):
        """Test that AgentService initializes correctly"""
        self.assertIsNotNone(self.agent_service)
        self.assertIsNotNone(self.agent_service.root_agent)

    def test_agent_status(self):
        """Test getting agent status"""
        status = self.agent_service.get_agent_status()
        self.assertIsInstance(status, dict)
        self.assertIn('status', status)

    def test_sub_agents_list(self):
        """Test getting sub-agents list"""
        sub_agents = self.agent_service.get_available_sub_agents()
        self.assertIsInstance(sub_agents, list)

    def test_agent_configuration_validation(self):
        """Test agent configuration validation"""
        validation = self.agent_service.validate_agent_configuration()
        self.assertIsInstance(validation, dict)
        self.assertIn('configuration_valid', validation)

    def test_travel_service_initialization(self):
        """Test that TravelService initializes correctly"""
        self.assertIsNotNone(self.travel_service)

    def test_travel_tools_status(self):
        """Test getting travel tools status"""
        status = self.travel_service.get_travel_tools_status()
        self.assertIsInstance(status, dict)
        self.assertIn('overall_status', status)


class TravelConciergeAPITest(TestCase):
    """Test Travel Concierge API endpoints"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_agent_status_endpoint(self):
        """Test agent status API endpoint"""
        url = reverse('travel_concierge:agent_status')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_sub_agents_list_endpoint(self):
        """Test sub-agents list API endpoint"""
        url = reverse('travel_concierge:sub_agents')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_tools_status_endpoint(self):
        """Test tools status API endpoint"""
        url = reverse('travel_concierge:tools_status')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_health_check_endpoint(self):
        """Test health check API endpoint"""
        url = reverse('travel_concierge:health_check')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_chat_with_agent_endpoint(self):
        """Test chat with agent API endpoint"""
        url = reverse('travel_concierge:chat')
        payload = {
            'message': 'I want to travel to Japan',
            'user_id': 'test_user_123'
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_travel_recommendations_endpoint(self):
        """Test travel recommendations API endpoint"""
        url = reverse('travel_concierge:recommendations')
        payload = {
            'destination_type': 'beach',
            'budget_range': 'mid-range',
            'group_size': 2,
            'interests': ['relaxation', 'culture']
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_chat_validation_error(self):
        """Test chat endpoint with invalid data"""
        url = reverse('travel_concierge:chat')
        payload = {
            'message': '',  # Empty message should fail validation
            'user_id': 'test_user_123'
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_recommendations_validation_error(self):
        """Test recommendations endpoint with invalid data"""
        url = reverse('travel_concierge:recommendations')
        payload = {
            'destination_type': 'invalid_type',  # Should fail validation
            'budget_range': 'mid-range'
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])