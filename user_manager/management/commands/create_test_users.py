"""Management command to create test users for authentication testing."""

from django.core.management.base import BaseCommand
from django.db import transaction
from user_manager.service import AuthService


class Command(BaseCommand):
    """Create test users for authentication testing."""

    help = 'Create test users for authentication testing'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing test users and create new ones',
        )

    def handle(self, *args, **options):
        """Handle the command execution."""
        self.stdout.write('Creating test users for authentication...')

        # Test users data
        test_users = [
            {
                'username': 'alan_love',
                'email': 'alanlovelq@gmail.com',
                'password': 'SecurePassword123!',
                'full_name': 'Alan Love',
                'avatar_url': 'https://example.com/avatars/alan_love.jpg',
                'address': 'Ha Noi, Viet Nam',
                'interests': ['Travel', 'Photography', 'Food']
            },
            {
                'username': 'test_user',
                'email': 'test@example.com',
                'password': 'TestPassword123!',
                'full_name': 'Test User',
                'avatar_url': 'https://example.com/avatars/test_user.jpg',
                'address': 'Ho Chi Minh City, Viet Nam',
                'interests': ['Technology', 'Gaming', 'Music']
            },
            {
                'username': 'demo_user',
                'email': 'demo@example.com',
                'password': 'DemoPassword123!',
                'full_name': 'Demo User',
                'avatar_url': 'https://example.com/avatars/demo_user.jpg',
                'address': 'Da Nang, Viet Nam',
                'interests': ['Art', 'Culture', 'History']
            }
        ]

        if options['reset']:
            self.stdout.write('Resetting existing test users...')
            from user_manager.models import User
            for user_data in test_users:
                try:
                    user = User.objects.get(username=user_data['username'])
                    user.delete()
                    self.stdout.write(
                        self.style.WARNING(f'Deleted existing user: {user_data["username"]}')
                    )
                except User.DoesNotExist:
                    pass

        # Create test users
        created_count = 0
        for user_data in test_users:
            try:
                with transaction.atomic():
                    user = AuthService.create_user(**user_data)
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created user: {user.username} ({user.email})'
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to create user {user_data["username"]}: {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} test users')
        )

        # Display login instructions
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TEST USER LOGIN CREDENTIALS:')
        self.stdout.write('='*50)
        for user_data in test_users:
            self.stdout.write(f'Username: {user_data["username"]}')
            self.stdout.write(f'Password: {user_data["password"]}')
            self.stdout.write(f'Email: {user_data["email"]}')
            self.stdout.write('-'*30)

        self.stdout.write('\nYou can now test the authentication APIs with these credentials.')
        self.stdout.write('Example API endpoints:')
        self.stdout.write('- POST /api/auth/login/')
        self.stdout.write('- GET /api/auth/verify/')
        self.stdout.write('- POST /api/auth/logout/')
        self.stdout.write('\nAPI Documentation available at: /swagger/')