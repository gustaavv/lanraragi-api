from lanraragi_api.base import *
from lanraragi_api.base.base import AUTH


class LANraragiAPI:
    def __init__(self, key: str, server: str, auth_way: AUTH = AUTH.QUERY_PARAM, default_headers=None):
        if default_headers is None:
            default_headers = {}
        self.archive = ArchiveAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.category = CategoryAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.database = DatabaseAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.minion = MinionAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.other = OtherAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.search = SearchAPI(key, server, auth_way=auth_way, default_headers=default_headers)
        self.shinobu = ShinobuAPI(key, server, auth_way=auth_way, default_headers=default_headers)
