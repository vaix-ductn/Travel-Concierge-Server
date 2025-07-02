import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from user_manager.models import UserProfile


class Command(BaseCommand):
    help = 'Create seed data for system testing - Django users and user profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate users even if they exist',
        )

    def handle(self, *args, **options):
        """Create seed data for testing"""

        try:
            # Define test users data with hard-coded values from itinerary_custom.json
            test_users = [
                {
                    'django_user': {
                        'username': 'admin',
                        'email': 'admin@travelconcierge.com',
                        'password': 'TravelAdmin@2024',
                        'first_name': 'System',
                        'last_name': 'Administrator',
                        'is_staff': True,
                        'is_superuser': True,
                    },
                    'user_profile': {
                        'username': 'System Administrator',
                        'email': 'admin@travelconcierge.com',
                        'address': 'Travel Concierge HQ, Tokyo, Japan',
                        'interests': 'System administration, Travel technology',
                        'passport_nationality': 'Japanese',
                        'seat_preference': 'aisle',
                        'food_preference': 'No preference',
                        'allergies': [],
                        'likes': ['efficiency', 'technology', 'travel'],
                        'dislikes': ['system downtime'],
                        'price_sensitivity': ['cost-effective'],
                        'home_address': 'Tokyo, Japan',
                        'local_prefer_mode': 'train',
                    }
                },
                {
                    'django_user': {
                        'username': 'nero',
                        'email': 'tranamynero@gmail.com',
                        'password': '1234@pass',
                        'first_name': 'Nero',
                        'last_name': 'Tran',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    'user_profile': {
                        'username': 'Nero Tran',
                        'email': 'tranamynero@gmail.com',
                        'address': 'Ha Noi, Viet Nam',
                        'interests': 'Travel, Photography, Food',
                        # Hard-coded data from itinerary_custom.json
                        'passport_nationality': 'Vietnamese',
                        'seat_preference': 'window',
                        'food_preference': 'Japanese cuisine - Ramen, Sushi, Sashimi',
                        'allergies': [],
                        'likes': ['temples', 'beaches', 'mountains', 'museums', 'nightlife', 'hiking', 'hot springs', 'beautiful scenery'],
                        'dislikes': ['remote locations', 'dangerous areas', 'places unsuitable for families with small children'],
                        'price_sensitivity': ['mid-range'],
                        'home_address': '2-chōme-40-2 Harayama, Midori Ward, Saitama, 336-0931',
                        'local_prefer_mode': 'drive',
                    }
                },
                {
                    'django_user': {
                        'username': 'test_user',
                        'email': 'testuser@example.com',
                        'password': 'TestUser@2024',
                        'first_name': 'Test',
                        'last_name': 'User',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    'user_profile': {
                        'username': 'Test User',
                        'email': 'testuser@example.com',
                        'address': 'San Francisco, CA, USA',
                        'interests': 'Technology, Travel, Food, Music',
                        'passport_nationality': 'American',
                        'seat_preference': 'window',
                        'food_preference': 'Mediterranean cuisine, Vegetarian options',
                        'allergies': ['nuts'],
                        'likes': ['beaches', 'museums', 'nightlife', 'hiking'],
                        'dislikes': ['crowded places', 'extreme weather'],
                        'price_sensitivity': ['budget-friendly', 'mid-range'],
                        'home_address': 'San Francisco, CA, USA',
                        'local_prefer_mode': 'public_transport',
                    }
                },
                {
                    'django_user': {
                        'username': 'demo_traveler',
                        'email': 'demo@travelconcierge.com',
                        'password': 'DemoTravel@2024',
                        'first_name': 'Demo',
                        'last_name': 'Traveler',
                        'is_staff': False,
                        'is_superuser': False,
                    },
                    'user_profile': {
                        'username': 'Demo Traveler',
                        'email': 'demo@travelconcierge.com',
                        'address': 'London, UK',
                        'interests': 'History, Culture, Architecture, Fine Dining',
                        'passport_nationality': 'British',
                        'seat_preference': 'aisle',
                        'food_preference': 'International cuisine, Local specialties',
                        'allergies': ['shellfish'],
                        'likes': ['historical sites', 'art galleries', 'fine dining', 'luxury hotels'],
                        'dislikes': ['budget accommodations', 'street food'],
                        'price_sensitivity': ['luxury', 'premium'],
                        'home_address': 'London, UK',
                        'local_prefer_mode': 'taxi',
                    }
                }
            ]

            # Create test users
            created_count = 0
            for user_data in test_users:
                django_user_data = user_data['django_user']
                profile_data = user_data['user_profile']

                email = django_user_data['email']
                username = django_user_data['username']

                # Check if Django user already exists
                if User.objects.filter(email=email).exists() or User.objects.filter(username=username).exists():
                    if not options['force']:
                        self.stdout.write(
                            self.style.WARNING(f'User {username} ({email}) already exists. Use --force to recreate.')
                        )
                        continue
                    else:
                        # Delete existing users
                        User.objects.filter(email=email).delete()
                        User.objects.filter(username=username).delete()
                        UserProfile.objects.filter(email=email).delete()
                        self.stdout.write(f'Deleted existing user: {username}')

                # Create Django User
                django_user = User.objects.create_user(
                    username=django_user_data['username'],
                    email=django_user_data['email'],
                    password=django_user_data['password'],
                    first_name=django_user_data['first_name'],
                    last_name=django_user_data['last_name'],
                    is_staff=django_user_data['is_staff'],
                    is_superuser=django_user_data['is_superuser'],
                )

                # Create UserProfile
                user_profile = UserProfile.objects.create(**profile_data)
                user_profile.set_password(django_user_data['password'])  # Set same password
                user_profile.save()

                created_count += 1

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created user: {username} ({email})')
                )
                self.stdout.write(f'   Profile UUID: {user_profile.profile_uuid}')
                self.stdout.write(f'   Django User ID: {django_user.id}')
                self.stdout.write(f'   Passport: {user_profile.passport_nationality}')
                self.stdout.write(f'   Preferences: {user_profile.likes}')
                self.stdout.write('')

            # Summary
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 Successfully created {created_count} test users!')
            )
            self.stdout.write(
                self.style.SUCCESS(f'📝 Total Django users: {User.objects.count()}')
            )
            self.stdout.write(
                self.style.SUCCESS(f'👤 Total User profiles: {UserProfile.objects.count()}')
            )

            # Login instructions
            self.stdout.write(
                self.style.WARNING('\n🔐 Login credentials for testing:')
            )
            for user_data in test_users:
                self.stdout.write(f"   Username: {user_data['django_user']['username']}")
                self.stdout.write(f"   Password: {user_data['django_user']['password']}")
                self.stdout.write(f"   Email: {user_data['django_user']['email']}")
                self.stdout.write('')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating seed data: {e}')
            )