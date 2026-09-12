from lanraragi_api.base import (
    ArchiveAPI,
    CategoryAPI,
    DatabaseAPI,
    MinionAPI,
    MiscAPI,
    SearchAPI,
    ShinobuAPI,
    StampAPI,
    TankoubonAPI,
)
from lanraragi_api.base.base import Auth
from lanraragi_api.base.opds import OPDSAPI
from lanraragi_api.base.plugin import PluginAPI


class LANraragiAPI:
    """Entry point of the library, grouping every API section of a server.

    Each attribute is an independent client for one group of endpoints, and all
    of them share the connection settings passed to this class.

    Args:
        server: Base URL of the LANraragi server, with or without a trailing
            slash.
        key: API key sent with every request. Defaults to None, which sends no
            credentials.
        auth_way: How the API key is transmitted. Defaults to
            ``Auth.AUTH_HEADER``.
        timeout: Timeout applied to every request, either a single value or a
            ``(connect, read)`` pair. Defaults to None, meaning no timeout.
        include_error_payload: Whether ``APIOperationError`` carries the raw
            response payload. Defaults to False.
        include_operation_error_message: Whether ``APIOperationError`` carries
            the error message reported by the server. Defaults to True.
        raise_on_operation_error: Whether a failed operation raises
            ``APIOperationError`` instead of being returned to the caller.
            Defaults to False.
        default_headers: Extra headers sent with every request. Defaults to
            None, which sends no extra headers.
        default_params: Extra query parameters sent with every request.
            Defaults to None, which sends no extra parameters.

    Attributes:
        search (SearchAPI): Search endpoints.
        archives (ArchiveAPI): Archive endpoints.
        database (DatabaseAPI): Database endpoints.
        categories (CategoryAPI): Category endpoints.
        tankoubons (TankoubonAPI): Tankoubon endpoints.
        plugins (PluginAPI): Plugin endpoints.
        shinobu (ShinobuAPI): Shinobu endpoints.
        minion (MinionAPI): Minion job endpoints.
        opds (OPDSAPI): OPDS endpoints.
        misc (MiscAPI): Miscellaneous endpoints.
        stamps (StampAPI): Stamp endpoints.
    """

    def __init__(
        self,
        server: str,
        key: str | None = None,
        auth_way: Auth = Auth.AUTH_HEADER,
        timeout: float | tuple[int, int] | None = None,
        include_error_payload: bool = False,
        include_operation_error_message: bool = True,
        raise_on_operation_error: bool = False,
        default_headers=None,
        default_params=None,
    ):
        self.search = SearchAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.archives = ArchiveAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.database = DatabaseAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.categories = CategoryAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.tankoubons = TankoubonAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.plugins = PluginAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.shinobu = ShinobuAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.minion = MinionAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.opds = OPDSAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.misc = MiscAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
        self.stamps = StampAPI(
            server,
            key=key,
            auth_way=auth_way,
            timeout=timeout,
            include_error_payload=include_error_payload,
            include_operation_error_message=include_operation_error_message,
            raise_on_operation_error=raise_on_operation_error,
            default_headers=default_headers,
            default_params=default_params,
        )
