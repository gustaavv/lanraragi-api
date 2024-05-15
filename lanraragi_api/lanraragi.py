from .api import *
from .common.base import AUTH


class LANrargiAPI:
    def __init__(self, key: str, server: str, auth_way: AUTH = AUTH.QUERY_PARAM, default_headers: dict[str, str] = {}):
        self.archive = ArchiveAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.category = CategoryAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.database = DatabaseAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.minion = MinionAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.other = OtherAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.search = SearchAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.shinobu = ShinobuAPI(key, server, auth_way=auth_way, default_headers=default_headers)
