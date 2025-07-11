from rest_framework.viewsets import ViewSet
from rest_framework.request import Request

# Nếu có các service hoặc utils nội bộ, import lại cho đúng travel_concierge
# from travel_concierge.base.database.connection.setup import SetupConnection
# from travel_concierge.base.exception.rest_framework.connection_error import ConnectionError
# from travel_concierge.base.exception.rest_framework.not_found import NotFound
# from travel_concierge.base.utils.common import USER_LOGIN
# from travel_concierge.user_manager.service.storage_connect import StorageConnectService

class CustomViewSet(ViewSet):
    def initial(self, request: Request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # self.init_connection(request=request)
        # USER_LOGIN.set(str(request.user.user_name))

    # def init_connection(self, request: Request) -> bool:
    #     # company is checked in step auth
    #     company_uuid = request.parser_context.get('kwargs').get('company_uuid')
    #     database = StorageConnectService().get(company_uuid)
    #     if database is None:
    #         raise NotFound()
    #     connection = SetupConnection(database.info)
    #     if not connection.setup():
    #         raise ConnectionError()
    #     return True