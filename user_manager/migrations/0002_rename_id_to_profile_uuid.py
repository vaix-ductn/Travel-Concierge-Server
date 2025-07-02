# Generated migration to rename id field to profile_uuid

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_manager', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='id',
            new_name='profile_uuid',
        ),
    ]