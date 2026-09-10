from pydantic import BaseModel, Field

from lanraragi_api.base.base import (
    BaseAPICall,
    MinionJobResponse,
    OperationResponse,
)


class ServerInfo(BaseModel):
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
    newsize: int | None = Field(default=None)


class DownloadUrlResponse(MinionJobResponse):
    url: str | None = Field(default=None)
    category: str | None = Field(default=None)


class MiscAPI(BaseAPICall):
    """
    Other APIs that don't fit a dedicated theme.
    """

    def get_server_information(self) -> ServerInfo:
        """
        Returns some basic information about the LRR instance this server is running.
        :return:
        """
        return self.request_model("GET", "/api/info", ServerInfo)

    def clean_temporary_folder(self) -> TempfolderCleanupResponse:
        """
        Cleans the server's temporary folder.
        :return: operation result
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
        """
        Add a URL to be downloaded by the server and added to its library.
        :param url: URL to download
        :param category_id: Category ID to add the downloaded URL to.
        :param use_form_data: Send values as form data instead of query params.
        :return: operation result
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
        """
        Queue a Minion job to regenerate missing/all thumbnails on the server.
        :param force: Whether to generate all thumbnails, or only the missing ones.
        :return: operation result
        """
        return self.request_operation(
            "POST",
            "/api/regen_thumbs",
            model=MinionJobResponse,
            params={"force": force if force else None},
        )
