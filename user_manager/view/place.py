from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from user_manager.service.place_service import PlaceService
from user_manager.serializers.place_serializers import PlaceCreateSerializer, PlaceReadSerializer, PlaceUpdateSerializer
from django.core.exceptions import ValidationError

@api_view(['POST'])
def create_place(request, user_uuid):
    data = request.data.copy()
    data['user_uuid'] = user_uuid
    serializer = PlaceCreateSerializer(data=data)
    if not serializer.is_valid():
        return Response({'success': False, 'message': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    try:
        place = PlaceService.create_place(serializer.validated_data)
        return Response({'success': True, 'place_uuid': str(place.place_uuid), 'message': 'Place created successfully'}, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_place(request, place_uuid):
    try:
        place = PlaceService.get_place(place_uuid)
        serializer = PlaceReadSerializer(place)
        return Response({'success': True, 'data': serializer.data})
    except ValidationError as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
def update_place(request, place_uuid):
    serializer = PlaceUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'success': False, 'message': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    try:
        place = PlaceService.update_place(place_uuid, serializer.validated_data)
        read_serializer = PlaceReadSerializer(place)
        return Response({'success': True, 'data': read_serializer.data, 'message': 'Place updated successfully'})
    except ValidationError as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def delete_place(request, place_uuid):
    try:
        PlaceService.delete_place(place_uuid)
        return Response({'success': True, 'message': 'Place deleted (soft) successfully'})
    except ValidationError as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def list_places(request, user_uuid):
    try:
        places = PlaceService.list_places(user_uuid)
        serializer = PlaceReadSerializer(places, many=True)
        return Response({'success': True, 'data': serializer.data})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)