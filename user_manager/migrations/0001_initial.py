# Generated migration for UserProfile model - Clean version

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password_hash', models.CharField(max_length=255)),
                ('address', models.TextField()),
                ('interests', models.TextField()),
                ('avatar_url', models.URLField(blank=True, max_length=500, null=True)),
                ('passport_nationality', models.CharField(blank=True, max_length=100, null=True)),
                ('seat_preference', models.CharField(blank=True, max_length=50, null=True)),
                ('food_preference', models.TextField(blank=True, null=True)),
                ('allergies', models.JSONField(blank=True, default=list, null=True)),
                ('likes', models.JSONField(blank=True, default=list, null=True)),
                ('dislikes', models.JSONField(blank=True, default=list, null=True)),
                ('price_sensitivity', models.JSONField(blank=True, default=list, null=True)),
                ('home_address', models.TextField(blank=True, null=True)),
                ('local_prefer_mode', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'user_profiles',
            },
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['email'], name='user_profiles_email_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['username'], name='user_profiles_username_idx'),
        ),
    ]