from lanraragi_api.base import *
from lanraragi_api.base.base import Auth


class LANraragiAPI:
    def __init__(self, server: str, key: str = None, auth_way: Auth = Auth.AUTH_HEADER,
                 default_headers=None, default_params=None):
        self.search = SearchAPI(server, key=key, auth_way=auth_way, default_headers=default_headers,
                                default_params=default_params)
        self.archive = ArchiveAPI(server, key=key, auth_way=auth_way, default_headers=default_headers,
                                  default_params=default_params)
        self.database = DatabaseAPI(server, key=key, auth_way=auth_way, default_headers=default_headers,
                                    default_params=default_params)
        self.category = CategoryAPI(server, key=key, auth_way=auth_way, default_headers=default_headers,
                                    default_params=default_params)
        self.tankoubon = TankoubonAPI(server, key=key, auth_way=auth_way, default_headers=default_headers,
                                      default_params=default_params)
        self.shinobu = ShinobuAPI(server, key=key, auth_way=auth_way, default_headers=default_headers,
                                  default_params=default_params)
        self.minion = MinionAPI(server, key=key, auth_way=auth_way, default_headers=default_headers,
                                default_params=default_params)
        self.misc = MiscAPI(server, key=key, auth_way=auth_way, default_headers=default_headers,
                            default_params=default_params)
