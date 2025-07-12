from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from user_manager.service.plan_service import PlanService
from django.core.exceptions import ValidationError
from user_manager.serializers.plan_serializers import PlanCreateSerializer, PlanReadSerializer, PlanUpdateSerializer

@api_view(['POST'])
def create_plan(request, user_uuid):
    serializer = PlanCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'success': False, 'message': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    try:
        plan = PlanService.create_plan(user_uuid, serializer.validated_data)
        return Response({
            'success': True,
            'plan_uuid': str(plan.plan_uuid),
            'message': 'Plan created successfully'
        }, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_plan(request, plan_uuid):
    try:
        plan = PlanService.get_plan(plan_uuid)
        serializer = PlanReadSerializer(plan)
        return Response({'success': True, 'data': serializer.data})
    except ValidationError as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
def update_plan(request, plan_uuid):
    serializer = PlanUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'success': False, 'message': 'Validation error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    try:
        plan = PlanService.update_plan(plan_uuid, serializer.validated_data)
        read_serializer = PlanReadSerializer(plan)
        return Response({'success': True, 'data': read_serializer.data, 'message': 'Plan updated successfully'})
    except ValidationError as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def delete_plan(request, plan_uuid):
    try:
        PlanService.delete_plan(plan_uuid)
        return Response({'success': True, 'message': 'Plan deleted (soft) successfully'})
    except ValidationError as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def list_plans(request, user_uuid):
    try:
        plans = PlanService.list_plans(user_uuid)
        serializer = PlanReadSerializer(plans, many=True)
        return Response({'success': True, 'data': serializer.data})
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)