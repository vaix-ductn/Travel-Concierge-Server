import logging
from user_manager.models import Plan, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from datetime import datetime

plan_logger = logging.getLogger('plan_logger')
plan_handler = logging.FileHandler('logs/plan.log')
plan_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
if not plan_logger.hasHandlers():
    plan_logger.addHandler(plan_handler)
plan_logger.setLevel(logging.INFO)

def _convert_datetime_to_str(obj):
    if isinstance(obj, dict):
        return {k: _convert_datetime_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_datetime_to_str(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

class PlanService:
    @staticmethod
    def create_plan(user_uuid, data):
        try:
            user = User.objects.get(user_uuid=user_uuid)
        except ObjectDoesNotExist as e:
            plan_logger.error(f'User not found: {user_uuid} - {e}')
            raise ValidationError('User not found')
        try:
            itinerary = _convert_datetime_to_str(data.get('itinerary', []))
            metadata = _convert_datetime_to_str(data.get('metadata', {}))
            plan = Plan.objects.create(
                user_uuid=user,
                title=data.get('title'),
                destination=data.get('destination'),
                itinerary=itinerary,
                metadata=metadata
            )
            plan_logger.info(f'Created plan {plan.plan_uuid} for user {user_uuid}')
            return plan
        except Exception as e:
            plan_logger.error(f'Error creating plan for user {user_uuid}: {e}')
            raise

    @staticmethod
    def get_plan(plan_uuid):
        try:
            return Plan.objects.get(plan_uuid=plan_uuid, del_flg=False)
        except Plan.DoesNotExist as e:
            plan_logger.error(f'Plan not found: {plan_uuid} - {e}')
            raise ValidationError('Plan not found')
        except Exception as e:
            plan_logger.error(f'Error getting plan {plan_uuid}: {e}')
            raise

    @staticmethod
    def update_plan(plan_uuid, data):
        try:
            plan = PlanService.get_plan(plan_uuid)
            for field, value in data.items():
                if field in ['itinerary', 'metadata']:
                    value = _convert_datetime_to_str(value)
                if hasattr(plan, field):
                    setattr(plan, field, value)
            plan.save()
            plan_logger.info(f'Updated plan {plan_uuid}')
            return plan
        except Exception as e:
            plan_logger.error(f'Error updating plan {plan_uuid}: {e}')
            raise

    @staticmethod
    def delete_plan(plan_uuid):
        try:
            plan = PlanService.get_plan(plan_uuid)
            plan.del_flg = True
            plan.save()
            plan_logger.info(f'Soft deleted plan {plan_uuid}')
            return True
        except Exception as e:
            plan_logger.error(f'Error soft deleting plan {plan_uuid}: {e}')
            raise

    @staticmethod
    def list_plans(user_uuid):
        try:
            return Plan.objects.filter(user_uuid=user_uuid, del_flg=False).order_by('-created_at')
        except Exception as e:
            plan_logger.error(f'Error listing plans for user {user_uuid}: {e}')
            raise