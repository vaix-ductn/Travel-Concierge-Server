import json
import os
from django.core.management.base import BaseCommand
from ...models import User, UserProfile


class Command(BaseCommand):
    help = 'Create seed data for system testing - custom users and user profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate users even if they exist',
        )

    def handle(self, *args, **options):
        """Create seed data for testing"""

        try:
            # Define test users data
            test_users = [
                {
                    'user': {
                        'username': 'admin',
                        'email': 'admin@travelconcierge.com',
                        'password': 'TravelAdmin@2024',
                        'full_name': 'System Administrator',
                    },
                    'user_profile': {
                        'address': 'Travel Concierge HQ, Tokyo, Japan',
                        'interests': 'System administration, Travel technology',
                        'avatar_url': '',
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
                    'user': {
                        'username': 'nero',
                        'email': 'tranamynero@gmail.com',
                        'password': '1234@pass',
                        'full_name': 'Nero Tran',
                    },
                    'user_profile': {
                        'address': 'Ha Noi, Viet Nam',
                        'interests': 'Travel, Photography, Food',
                        'avatar_url': '',
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
                    'user': {
                        'username': 'test_user',
                        'email': 'testuser@example.com',
                        'password': 'TestUser@2024',
                        'full_name': 'Test User',
                    },
                    'user_profile': {
                        'address': 'San Francisco, CA, USA',
                        'interests': 'Technology, Travel, Food, Music',
                        'avatar_url': '',
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
                    'user': {
                        'username': 'demo_traveler',
                        'email': 'demo@travelconcierge.com',
                        'password': 'DemoTravel@2024',
                        'full_name': 'Demo Traveler',
                    },
                    'user_profile': {
                        'address': 'London, UK',
                        'interests': 'History, Culture, Architecture, Fine Dining',
                        'avatar_url': '',
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

            created_count = 0
            for user_data in test_users:
                user_info = user_data['user']
                profile_info = user_data['user_profile']

                email = user_info['email']
                username = user_info['username']

                # Check if user exists
                user_qs = User.objects.filter(email=email)
                if user_qs.exists():
                    if not options['force']:
                        self.stdout.write(self.style.WARNING(f'User {username} ({email}) already exists. Use --force to recreate.'))
                        continue
                    else:
                        user_qs.delete()
                        User.objects.filter(username=username).delete()
                        UserProfile.objects.filter(user_uuid__email=email).delete()
                        self.stdout.write(f'Deleted existing user: {username}')

                # Create User
                user = User(
                    username=user_info['username'],
                    email=user_info['email'],
                    full_name=user_info.get('full_name', ''),
                )
                user.set_password(user_info['password'])
                user.save()

                # Create UserProfile
                profile = UserProfile(
                    user_uuid=user,
                    address=profile_info.get('address', ''),
                    interests=profile_info.get('interests', ''),
                    avatar_url=profile_info.get('avatar_url', ''),
                    passport_nationality=profile_info.get('passport_nationality', ''),
                    seat_preference=profile_info.get('seat_preference', ''),
                    food_preference=profile_info.get('food_preference', ''),
                    allergies=profile_info.get('allergies', []),
                    likes=profile_info.get('likes', []),
                    dislikes=profile_info.get('dislikes', []),
                    price_sensitivity=profile_info.get('price_sensitivity', []),
                    home_address=profile_info.get('home_address', ''),
                    local_prefer_mode=profile_info.get('local_prefer_mode', ''),
                )
                profile.save()

                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Created user: {username} ({email})'))
                self.stdout.write(f'   Profile UUID: {profile.user_profile_uuid}')
                self.stdout.write(f'   User UUID: {user.user_uuid}')
                self.stdout.write(f'   Passport: {profile.passport_nationality}')
                self.stdout.write(f'   Preferences: {profile.likes}')
                self.stdout.write('')

            # Summary
            self.stdout.write(self.style.SUCCESS(f'\n🎉 Successfully created {created_count} test users!'))
            self.stdout.write(self.style.SUCCESS(f'📝 Total users: {User.objects.count()}'))
            self.stdout.write(self.style.SUCCESS(f'👤 Total User profiles: {UserProfile.objects.count()}'))

            # Login instructions
            self.stdout.write(self.style.WARNING('\n🔐 Login credentials for testing:'))
            for user_data in test_users:
                self.stdout.write(f"   Username: {user_data['user']['username']}")
                self.stdout.write(f"   Password: {user_data['user']['password']}")
                self.stdout.write(f"   Email: {user_data['user']['email']}")
                self.stdout.write('')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating seed data: {e}'))