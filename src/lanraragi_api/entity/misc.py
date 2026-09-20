from pydantic import BaseModel, Field

from lanraragi_api.entity.base import OperationResponse
from lanraragi_api.entity.minion import MinionJobResponse


class ServerInfo(BaseModel):
    """Server info payload emitted by ``/api/info``.

    Older server versions used integers instead of booleans here.

    Attributes:
        archives_per_page: How many archives per page the server lists.
        cache_last_cleared: Timestamp for last time the search cache was wiped.
        debug_mode: Whether the instance has debug mode enabled.
        has_password: Whether the instance is password-protected.
        motd: MOTD of the instance.
        name: Name of the instance.
        nofun_mode: Whether the instance has no-fun mode enabled.
        server_resizes_images: Whether the instance auto-downsizes images
            before serving them.
        server_tracks_progress: Whether the instance tracks reading progression
            server-side.
        authenticated_progress: Whether the instance requires authentication
            for server-side progress updates.
        total_archives: Total amount of archives stored on instance.
        total_pages_read: Total amount of pages read.
        version: Version of the server.
        version_desc: Version description.
        version_name: Version name.
        excluded_namespaces: Tag namespaces excluded from search suggestions
            and tag statistics.
    """

    archives_per_page: int = Field(...)
    cache_last_cleared: int = Field(...)
    debug_mode: bool = Field(...)
    has_password: bool = Field(...)
    motd: str = Field(...)
    name: str = Field(...)
    nofun_mode: bool = Field(...)
    server_resizes_images: bool = Field(...)
    server_tracks_progress: bool = Field(...)
    authenticated_progress: bool | None = Field(default=None)
    total_archives: int = Field(...)
    total_pages_read: int = Field(...)
    version: str = Field(...)
    version_desc: str = Field(...)
    version_name: str = Field(...)
    excluded_namespaces: list[str] = Field(default_factory=list)


class TempfolderCleanupResponse(OperationResponse):
    """Result of a temporary folder cleanup.

    Attributes:
        newsize: Current size of the temporary folder post-cleanup.
    """

    newsize: int | None = Field(default=None)


class DownloadUrlResponse(MinionJobResponse):
    """Result of an operation that queued a URL download.

    Attributes:
        url: URL queued for download.
        category: Category the download was added to, if one was given.
    """

    url: str | None = Field(default=None)
    category: str | None = Field(default=None)
