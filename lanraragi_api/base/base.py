import base64
from enum import Enum


class Auth(str, Enum):
    QUERY_PARAM = 'query param'
    AUTH_HEADER = 'auth header'


class BaseAPICall:

    def __init__(self, server: str, key: str = None, auth_way: Auth = Auth.QUERY_PARAM,
                 default_headers=None, default_params=None):
        if default_params is None:
            default_params = {}
        if default_headers is None:
            default_headers = {}

        self.auth_way = auth_way
        self.key = key
        self.server = server
        if self.server.endswith('/'):
            self.server = self.server[:-1]
        self.default_headers = default_headers
        self.default_params = default_params

        if key:
            if auth_way == Auth.QUERY_PARAM:
                self.default_params['key'] = self.key
            elif auth_way == Auth.AUTH_HEADER:
                base64_key = base64.b64encode(self.key.encode('utf-8')).decode('utf-8')
                self.default_headers['Authorization'] = f'Bearer {base64_key}'

    def build_headers(self, headers=None):
        if headers is None:
            headers = {}
        for k in self.default_headers:
            if k in headers:
                continue
            headers[k] = self.default_headers[k]
        return headers

    def build_params(self, params=None):
        if params is None:
            params = {}
        for k in self.default_params:
            if k in params:
                continue
            params[k] = self.default_params[k]
        return params
