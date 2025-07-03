# Generated migration for authentication models

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('user_manager', '0002_rename_id_to_profile_uuid'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.CharField(default=lambda: f"user_{uuid.uuid4().hex[:10]}", max_length=50, primary_key=True, serialize=False)),
                ('username', models.CharField(db_index=True, max_length=50, unique=True)),
                ('email', models.CharField(db_index=True, max_length=255, unique=True)),
                ('password_hash', models.CharField(max_length=255)),
                ('full_name', models.CharField(blank=True, max_length=255, null=True)),
                ('avatar_url', models.TextField(blank=True, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('interests', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('failed_login_attempts', models.IntegerField(default=0)),
                ('locked_until', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='UserToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_hash', models.CharField(db_index=True, max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tokens', to='user_manager.user')),
            ],
            options={
                'db_table': 'user_tokens',
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['username'], name='users_usernam_c5a8b5_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_email_7c7b34_idx'),
        ),
        migrations.AddIndex(
            model_name='usertoken',
            index=models.Index(fields=['token_hash'], name='user_tokens_token_h_8a2b1e_idx'),
        ),
        migrations.AddIndex(
            model_name='usertoken',
            index=models.Index(fields=['user', 'is_active'], name='user_tokens_user_id_3f9c8d_idx'),
        ),
    ]