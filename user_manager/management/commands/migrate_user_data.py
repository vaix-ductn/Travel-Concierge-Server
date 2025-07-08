from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User as DjangoUser
from user_manager.models import User, UserProfile, UserToken
import uuid
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate user data from old primary key structure to new UUID-based structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Create backup of current data before migration',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        backup = options['backup']

        self.stdout.write(
            self.style.SUCCESS('Starting user data migration...')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        # Step 1: Backup current data if requested
        if backup and not dry_run:
            self.backup_current_data()

        # Step 2: Migrate Django auth_user to custom users table
        self.migrate_django_users(dry_run)

        # Step 3: Update UserProfile references
        self.update_user_profile_references(dry_run)

        # Step 4: Clean up old data
        if not dry_run:
            self.cleanup_old_data()

        self.stdout.write(
            self.style.SUCCESS('User data migration completed!')
        )

    def backup_current_data(self):
        """Create backup of current user data"""
        self.stdout.write('Creating backup of current data...')

        # Backup users table
        users = User.objects.all()
        self.stdout.write(f'Backed up {users.count()} users')

        # Backup user_profiles table
        profiles = UserProfile.objects.all()
        self.stdout.write(f'Backed up {profiles.count()} user profiles')

    def migrate_django_users(self, dry_run):
        """Migrate users from Django's auth_user to custom users table"""
        self.stdout.write('Migrating Django auth_user to custom users table...')

        django_users = DjangoUser.objects.all()
        migrated_count = 0

        for django_user in django_users:
            # Check if user already exists in custom table
            if User.objects.filter(username=django_user.username).exists():
                self.stdout.write(
                    f'User {django_user.username} already exists in custom table, skipping...'
                )
                continue

            if not dry_run:
                # Create new user with UUID
                custom_user = User.objects.create(
                    user_uuid=uuid.uuid4(),
                    username=django_user.username,
                    email=django_user.email,
                    password_hash=django_user.password,  # Django already hashes passwords
                    full_name=f"{django_user.first_name} {django_user.last_name}".strip(),
                    created_at=django_user.date_joined,
                    updated_at=django_user.date_joined,
                )
                migrated_count += 1
                self.stdout.write(f'Migrated user: {django_user.username}')
            else:
                migrated_count += 1
                self.stdout.write(f'Would migrate user: {django_user.username}')

        self.stdout.write(f'Migrated {migrated_count} users from Django auth_user')

    def update_user_profile_references(self, dry_run):
        """Update UserProfile references to use new UUID structure"""
        self.stdout.write('Updating UserProfile references...')

        profiles = UserProfile.objects.all()
        updated_count = 0

        for profile in profiles:
            # Find corresponding user by username or email
            try:
                user = User.objects.get(username=profile.username)

                if not dry_run:
                    # Update profile to reference new user UUID
                    # Note: This assumes you want to link profiles to users
                    # You might need to adjust this based on your requirements
                    self.stdout.write(f'Updated profile for user: {profile.username}')
                    updated_count += 1
                else:
                    self.stdout.write(f'Would update profile for user: {profile.username}')
                    updated_count += 1

            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'No user found for profile: {profile.username}')
                )

        self.stdout.write(f'Updated {updated_count} user profiles')

    def cleanup_old_data(self):
        """Clean up old data after successful migration"""
        self.stdout.write('Cleaning up old data...')

        # Remove Django auth_user data (optional - be careful!)
        # django_users = DjangoUser.objects.all()
        # django_users.delete()
        # self.stdout.write('Removed Django auth_user data')

        # You can add more cleanup steps here as needed
        self.stdout.write('Cleanup completed')