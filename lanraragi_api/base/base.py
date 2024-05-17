from enum import Enum


class AUTH(str, Enum):
    QUERY_PARAM = 'query param'
    AUTH_HEADER = 'auth header'


class BaseAPICall:

    def __init__(self, key: str, server: str, auth_way: AUTH = AUTH.QUERY_PARAM, default_headers: dict[str, str] = {}):
        assert auth_way == AUTH.QUERY_PARAM, 'AUTH.AUTH_HEADER is not supported now'
        self.auth_way = auth_way
        self.key = key
        self.server = server
        if self.server.endswith('/'):
            self.server = self.server[:-1]
        self.default_headers = default_headers

    def build_headers(self, headers: dict[str, str] = {}):
        for k in self.default_headers:
            if k in headers:
                continue
            headers[k] = self.default_headers[k]
        return headers
