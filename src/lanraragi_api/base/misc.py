from pydantic import BaseModel, Field

from lanraragi_api.base.base import (
    BaseAPICall,
    MinionJobResponse,
    OperationResponse,
)


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


class MiscAPI(BaseAPICall):
    """Other APIs that don't fit a dedicated theme.

    Shared request and error behavior is documented on ``BaseAPICall``.
    """

    def get_server_information(self) -> ServerInfo:
        """Return basic information about the LRR instance this server is running.

        Returns:
            ServerInfo: Basic information about the instance.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the body does not match ``ServerInfo``.
        """
        return self.request_model("GET", "/api/info", ServerInfo)

    def clean_temporary_folder(self) -> TempfolderCleanupResponse:
        """Clean the server's temporary folder.

        Returns:
            TempfolderCleanupResponse: Result of the cleanup, with the new size
                of the temporary folder.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``TempfolderCleanupResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            A cleanup error is reported in the ``error`` field of the result
            while the call still answers with 200.
        """
        return self.request_operation(
            "DELETE", "/api/tempfolder", model=TempfolderCleanupResponse
        )

    def queue_url_to_download(
        self,
        url: str,
        category_id: str | None = None,
        use_form_data: bool = False,
    ) -> DownloadUrlResponse:
        """Add a URL to be downloaded by the server and added to its library.

        Args:
            url: URL to download.
            category_id: Category ID to add the downloaded URL to. Defaults to
                None.
            use_form_data: Send the arguments as form data instead of query
                parameters. Defaults to False.

        Returns:
            DownloadUrlResponse: Result of the call, with the ID of the queued
                job and the URL that was queued.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``DownloadUrlResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            The endpoint takes its arguments either as query parameters or in a
            multipart form body; this switch picks the body variant.
            A 400 response, returned for a bad request such as a missing URL,
            is returned in the operation result, with ``success`` set to 0,
            instead of raising.
        """
        request_kwargs = {"params": {"url": url, "catid": category_id}}
        if use_form_data:
            files = {}
            if url is not None:
                files["url"] = (None, url)
            if category_id is not None:
                files["catid"] = (None, category_id)
            request_kwargs = {"files": files}

        return self.request_operation(
            "POST",
            "/api/download_url",
            model=DownloadUrlResponse,
            **request_kwargs,
        )

    def regenerate_thumbnails(self, force: bool = False) -> MinionJobResponse:
        """Queue a Minion job to regenerate missing/all thumbnails on the server.

        Args:
            force: Whether to generate all thumbnails, or only the missing
                ones. Defaults to False.

        Returns:
            MinionJobResponse: Result of the call, with the ID of the queued
                job.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``MinionJobResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation(
            "POST",
            "/api/regen_thumbs",
            model=MinionJobResponse,
            params={"force": force if force else None},
        )
