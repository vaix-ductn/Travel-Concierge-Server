from django.db import models
import uuid

class Plan(models.Model):
    plan_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_uuid = models.ForeignKey('user_manager.User', on_delete=models.CASCADE, db_column='user_uuid', to_field='user_uuid', related_name='plans')
    title = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    itinerary = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    del_flg = models.BooleanField(default=False, help_text='Soft delete flag')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'plans'
        indexes = [
            models.Index(fields=['user_uuid']),
        ]

    def __str__(self):
        return f"{self.title} for {self.user_uuid}"