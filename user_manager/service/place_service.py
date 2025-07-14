from user_manager.models import Place, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import logging

place_logger = logging.getLogger('place_logger')
place_handler = logging.FileHandler('logs/place.log')
place_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
if not place_logger.hasHandlers():
    place_logger.addHandler(place_handler)
place_logger.setLevel(logging.INFO)

class PlaceService:
    @staticmethod
    def create_place(data):
        try:
            user = User.objects.get(user_uuid=data.get('user_uuid'))
        except ObjectDoesNotExist as e:
            place_logger.error(f'User not found: {data.get("user_uuid")} - {e}')
            raise ValidationError('User not found')
        try:
            place = Place.objects.create(
                user_uuid=user,
                place_name=data.get('place_name'),
                address=data.get('address'),
                lat=data.get('lat'),
                long=data.get('long'),
                review_ratings=data.get('review_ratings'),
                highlights=data.get('highlights'),
                image_url=data.get('image_url'),
                map_url=data.get('map_url'),
                place_id=data.get('place_id')
            )
            place_logger.info(f'Created place {place.place_uuid} for user {user.user_uuid}')
            return place
        except Exception as e:
            place_logger.error(f'Error creating place for user {user.user_uuid}: {e}')
            raise

    @staticmethod
    def get_place(place_uuid):
        try:
            return Place.objects.get(place_uuid=place_uuid, del_flg=False)
        except Place.DoesNotExist as e:
            place_logger.error(f'Place not found: {place_uuid} - {e}')
            raise ValidationError('Place not found')
        except Exception as e:
            place_logger.error(f'Error getting place {place_uuid}: {e}')
            raise

    @staticmethod
    def update_place(place_uuid, data):
        try:
            place = PlaceService.get_place(place_uuid)
            for field, value in data.items():
                if hasattr(place, field):
                    setattr(place, field, value)
            place.save()
            place_logger.info(f'Updated place {place_uuid}')
            return place
        except Exception as e:
            place_logger.error(f'Error updating place {place_uuid}: {e}')
            raise

    @staticmethod
    def delete_place(place_uuid):
        try:
            place = PlaceService.get_place(place_uuid)
            place.del_flg = True
            place.save()
            place_logger.info(f'Soft deleted place {place_uuid}')
            return True
        except Exception as e:
            place_logger.error(f'Error soft deleting place {place_uuid}: {e}')
            raise

    @staticmethod
    def list_places(user_uuid):
        try:
            return Place.objects.filter(user_uuid=user_uuid, del_flg=False).order_by('-created_at')
        except Exception as e:
            place_logger.error(f'Error listing places for user {user_uuid}: {e}')
            raise