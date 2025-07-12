from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('user_manager', '0001_initial'),
    ]
    operations = [
        migrations.RemoveField(
            model_name='user',
            name='avatar_url',
        ),
        migrations.RemoveField(
            model_name='user',
            name='address',
        ),
        migrations.RemoveField(
            model_name='user',
            name='interests',
        ),
    ]