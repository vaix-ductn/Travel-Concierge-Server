# UserProfile cleanup migration (no longer needed as UserProfile moved to user_manager)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('travel_concierge', '0001_initial'),
        ('user_manager', '0001_initial'),  # Ensure user_manager migration runs first
    ]

    operations = [
        # NOTE: No operations needed since UserProfile was never created in travel_concierge
        # after refactor. This migration exists only for dependency management.
    ]