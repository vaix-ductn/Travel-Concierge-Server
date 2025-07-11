import inspect
from functools import cached_property
from typing import Any
from django.apps import apps
from rest_framework.permissions import BasePermission as Permission
from rest_framework.request import Request
# from travel_concierge.base.exception.rest_framework.not_support_function import NotSupportFunction
# from travel_concierge.base.exception.rest_framework.not_found import NotFound
# from travel_concierge.base.database.models.custom.model import BaseModel
# from travel_concierge.base.decorator.logging import logging
# from travel_concierge.user_manager.models import CompanyConnect
# from travel_concierge.user_manager.enum.permission.user import UserType

class BasePermission(Permission):
    @cached_property
    def for_model(self) -> list:
        raise NotImplementedError()
    @property
    def field_name(self) -> str:
        raise NotImplementedError()
    def get_object(self, value: Any):
        model = apps.get_model(app_label=self.for_model[0], model_name=self.for_model[-1])
        object = model.objects.filter(**{self.field_name: value}).first()
        if object is None:
            raise Exception('NotFound')
        return object
    def has_permission(self, request: Request, view: str) -> bool:
        if self.before_check_perm(request=request, view=view):
            return True
        # if request.user.user_type == UserType.SNC_USER:
        #     return True
        # if request.user.user_type == UserType.CADEWA_USER:
        #     return True
        if self.check_company(request=request) is False:
            return False
        return self.has_perm_on_view(request=request, view=view)
    def check_company(self, request: Request) -> bool:
        company_uuid = request.parser_context.get('kwargs').get('company_uuid')
        if company_uuid is None:
            return True
        # company_connect = CompanyConnect.objects.filter(user_uuid=request.user.user_uuid, company_uuid=company_uuid).first()
        # return True if company_connect else False
        return True
    def before_check_perm(self, request: Request, view: str) -> bool:
        return self.has_all_permission(request=request)
    def has_all_permission(self, request: Request) ->bool:
        raise NotImplementedError()
    def has_perm_on_view(self, request: Request, view: str) -> bool:
        view_method = self.get_view_method(request=request, view=view)
        if self.has_method(view_method=view_method) is False:
            return True
        return self.call_check_perm_method(view_method=view_method, request=request)
    def call_check_perm_method(self, view_method: str, request: Request):
        method = getattr(self, view_method)
        method_args = inspect.getfullargspec(method).args
        number_args = len(method_args)
        if number_args > 3:
            raise Exception('NotSupportFunction')
        args = list()
        if number_args >= 2:
            args.append(request.user)
        if number_args == 3:
            object_field = request.parser_context.get('kwargs').get(self.field_name)
            if object_field is None:
                raise Exception('NotSupportFunction')
            args.append(self.get_object(object_field))
        return method(*args)
    def get_view_method(self, request: Request, view: str) -> str:
        raise NotImplementedError()
    def has_method(self, view_method: str) -> bool:
        return hasattr(self, view_method) and callable(getattr(self, view_method))