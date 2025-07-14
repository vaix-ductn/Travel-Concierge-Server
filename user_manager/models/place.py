from django.db import models
import uuid

class Place(models.Model):
    place_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_uuid = models.ForeignKey('user_manager.User', on_delete=models.CASCADE, db_column='user_uuid', to_field='user_uuid', related_name='places')
    place_name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    lat = models.CharField(max_length=50)
    long = models.CharField(max_length=50)
    review_ratings = models.CharField(max_length=20)
    highlights = models.CharField(max_length=1000)
    image_url = models.CharField(max_length=500)
    map_url = models.CharField(max_length=500)
    place_id = models.CharField(max_length=100)
    del_flg = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'places'
        indexes = [
            models.Index(fields=['user_uuid']),
            models.Index(fields=['place_id']),
        ]

    def __str__(self):
        return f"{self.place_name} ({self.place_id})"