from django.apps import AppConfig


class UserManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_manager'
    verbose_name = 'User Manager'

    def ready(self):
        """Initialize app when Django starts"""
        pass