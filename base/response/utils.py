from rest_framework.response import Response
from rest_framework.fields import empty

def api_response(status: int, msg: str, http_code: int, format_version:int, data: dict = {}) -> Response:
    body = {
        'status': status,
    }
    if msg:
        body['msg'] = msg
    if data:
        body['data'] = data
    if format_version:
        body['format_version'] = format_version
    return Response(body, status=http_code)

def api_response_success(status: int = 0, msg: str = "",  http_code: int = 200, format_version:int = 1000, data: dict = {}) -> Response:
    return api_response(status=status, msg=msg, http_code=http_code, format_version=format_version, data=data)

def api_response_error(status: int = 100, msg: str = "Error", http_code: int = 400, format_version:int = 1000, data: dict = {}) -> Response:
    return api_response(data=data, status=status, http_code=http_code, msg=msg, format_version=format_version)