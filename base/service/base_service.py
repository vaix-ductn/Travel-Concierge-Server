import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from django.utils.timezone import now
from django.apps import apps
from django.db.models import Model, Q
from django.db import connections
from django.core.cache import cache
from django.conf import settings

# Nếu có các constant, enum, middleware nội bộ, import lại cho đúng travel_concierge
# from travel_concierge.base.enum.constant import DelFlag, WithTrash
# from travel_concierge.base.middleware.cache_company import COMPANY_UUID

logger = logging.getLogger(__name__)

class AbstractBaseService(ABC):
    def __init__(self):
        self.__model = apps.get_model(app_label=self._set_model()[0], model_name=self._set_model()[-1])
    @abstractmethod
    def _set_model(self) -> list:
        pass
    @property
    def model(self) -> Model:
        return self.__model
    def get(self, pk: str, with_trashed = 2) -> Model|None:
        condition = {"pk": pk}
        # Logic with_trashed có thể mở rộng nếu cần
        query = self.__model.objects.filter(**condition)
        return query.first()
    def store(self, data: dict, id: str = None) -> Model:
        if id is None:
            return self.create(data=data)
        return self.update(data=data, id=id)
    def create(self, data: dict) -> Model:
        return self.__model.objects.create(**data)
    def bulk_create(self, records:list) -> list:
        current_time = now().strftime("%Y%m%d%H%M%S")
        for record in records:
            record.create_dt = current_time
        return self.__model.objects.bulk_create(records)
    def update(self, data: dict, id: str) -> Model:
        instance = self.get(id)
        for k, v in data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
    def bulk_update(self, records:list, fields:list):
        current_time = now().strftime("%Y%m%d%H%M%S")
        for record in records:
            record.update_dt = current_time
        return self.__model.objects.bulk_update(records, fields)
    def delete(self, id: str) -> bool:
        instance = self.get(id)
        instance.delete()
        return True
    def force_delete(self, id: str) -> bool:
        instance = self.get(id)
        if instance is not None:
            instance.delete()
        return True
    def search(self, data: dict):
        pass
    def restore(self, id: str) -> bool:
        # Logic restore nếu có
        return True
    def add_query(self, data: dict, key: str, query: Q, condition: str, field: str = None) -> Q:
        field = field or key
        if data.get(key):
            new_query = query & Q(**{f'{field}__{condition}': data.get(key)})
            return new_query
        return query
    def add_date_query(self, data: dict, key: str, query: Q, field: str = None) -> Q:
        field = field or key
        if data.get(key):
            new_query = query
            if data[key].get('start'):
                new_query &= Q(**{f'{field}__gte': data[key].get('start')})
            if data[key].get('end'):
                new_query &= Q(**{f'{field}__lte': data[key].get('end')})
            return new_query
        return query
    def _execute_raw_sql_query(self, sql_query):
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return rows, columns
    def _convert_raw_query_to_dict(self, rows, columns):
        result = []
        for row in rows:
            row_dict = {}
            for idx, value in enumerate(row):
                col_name = columns[idx]
                if col_name.endswith('_uuid') and value:
                    try:
                        row_dict[col_name] = str(uuid.UUID(value))
                    except ValueError:
                        row_dict[col_name] = value
                else:
                    row_dict[col_name] = value
            result.append(row_dict)
        return result