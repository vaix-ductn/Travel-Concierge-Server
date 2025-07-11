from typing import Any
from functools import cached_property
from uuid import UUID
import base64
from datetime import datetime

from django.apps import apps
from django.db.models import Model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

# Nếu có các constant, exception nội bộ, import lại cho đúng travel_concierge
# from travel_concierge.base.enum.constant import Constant
# from travel_concierge.base.exception.rest_framework.unique_exception import UniqueException
# from travel_concierge.base.exception.rest_framework.not_found import NotFound as NotFoundException

class Validation(serializers.Serializer):
    class Meta:
        validators = []

    @cached_property
    def model_info(self) -> list:
        raise Exception("Please define method before using the class")

    def get_model(self, other_model_info: list|None) -> Model:
        model_information = self.model_info if other_model_info is None else other_model_info
        return apps.get_model(app_label=model_information[0], model_name=model_information[-1])

    def validate_unique(self, value: Any, column: str, other_model_info: list = None) -> bool:
        model = self.get_model(other_model_info=other_model_info)
        instance = model.objects.filter(**{column: value}).first()
        if instance is not None:
            raise serializers.ValidationError(_(f"{column} must be unique."))
        return True

    def validate_exist(self, value: Any, column: str, other_model_info: list | None) -> bool:
        model = self.get_model(other_model_info=other_model_info)
        instance = model.objects.filter(**{column: value}).first()
        if instance is None:
            raise serializers.ValidationError(_(f"{column} does not exist."))
        return True

    def check_is_valid_number(self, value, field_name, allow_hyphen=False) -> bool:
        cleaned_value = value.replace('-', '') if allow_hyphen else value
        if not cleaned_value.isdigit() and value != "":
            raise serializers.ValidationError(_(f"{field_name} must be a number."))
        return True

    def validate_datetime_format(self, value) -> bool:
        if value:
            if len(value) != 14:
                raise serializers.ValidationError(_('The format of datetime must be YYYYMMDDhhmmss'))
            try:
                datetime.strptime(value, '%Y%m%d%H%M%S')
            except ValueError:
                raise serializers.ValidationError(_('The format of datetime must be YYYYMMDDhhmmss'))
        return True

    def is_valid_tags(self, tag_list: list) -> bool:
        if tag_list:
            key_list = []
            for tag in tag_list:
                if 'key' not in tag or 'value' not in tag:
                    raise serializers.ValidationError(_('Tag object must contain both key and value'))
                if tag['key'] in key_list:
                    msg = _(f"Tag key is duplicated - key = {tag['key']}")
                    raise serializers.ValidationError(msg)
                else:
                    key_list.append(tag['key'])
        return True

    def check_max_length(self, str_input, max_length:int = 255, field_name:str = 'field') -> bool:
        if str_input:
            byte_count = len(str_input.encode('utf-8'))
            if byte_count > max_length:
                raise serializers.ValidationError(_(f"The length of {field_name} cannot exceed {max_length} bytes"))
        return True

    def is_valid_uuid(self, uuid_to_test, version=7):
        try:
            uuid_obj = UUID(uuid_to_test, version=version)
            return str(uuid_obj) == uuid_to_test
        except ValueError:
            return False

    def is_valid_base64(self, encoded_string):
        try:
            base64.b64decode(encoded_string)
            return True
        except base64.binascii.Error:
            return False