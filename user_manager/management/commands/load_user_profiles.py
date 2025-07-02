from django.core.management.base import BaseCommand
from django.conf import settings
import json
import os
from user_manager.models import UserProfile


class Command(BaseCommand):
    help = 'Load sample user profiles from fixture data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload of profiles even if they already exist',
        )

    def handle(self, *args, **options):
        """Load sample user profiles from JSON fixture file"""

        fixture_path = os.path.join(
            settings.BASE_DIR,
            'travel_concierge',
            'fixtures',
            'sample_profiles.json'
        )

        try:
            with open(fixture_path, 'r') as f:
                profiles_data = json.load(f)

            for profile_data in profiles_data:
                fields = profile_data['fields']
                email = fields['email']

                # Check if profile already exists
                if UserProfile.objects.filter(email=email).exists():
                    if options['force']:
                        UserProfile.objects.filter(email=email).delete()
                        self.stdout.write(
                            self.style.WARNING(f'Deleted existing profile for {email}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Profile for {email} already exists, skipping...')
                        )
                        continue

                # Create new profile
                profile = UserProfile(
                    username=fields['username'],
                    email=fields['email'],
                    address=fields['address'],
                    interests=fields['interests'],
                    avatar_url=fields.get('avatar_url'),
                    passport_nationality=fields.get('passport_nationality'),
                    seat_preference=fields.get('seat_preference'),
                    food_preference=fields.get('food_preference'),
                    allergies=fields.get('allergies', []),
                    likes=fields.get('likes', []),
                    dislikes=fields.get('dislikes', []),
                    price_sensitivity=fields.get('price_sensitivity', []),
                    home_address=fields.get('home_address'),
                    local_prefer_mode=fields.get('local_prefer_mode')
                )

                # Set password
                profile.set_password(fields['password_hash'])
                profile.save()

                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created profile for {profile.username}')
                )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Fixture file not found: {fixture_path}')
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR('Invalid JSON in fixture file')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading profiles: {str(e)}')
            )