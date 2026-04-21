from typing import Any

from pydantic import BaseModel, Field
from requests import Response

from lanraragi_api.base.base import (
    BaseAPICall,
    DictLikeModel,
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


class PluginParameter(DictLikeModel):
    name: str | None = Field(default=None)
    desc: str | None = Field(default=None)
    type: str | None = Field(default=None)
    default_value: str | None = Field(default=None)


class PluginInfo(DictLikeModel):
    author: str | None = Field(default=None)
    description: str | None = Field(default=None)
    name: str | None = Field(default=None)
    icon: str | None = Field(default=None)
    type: str | None = Field(default=None)
    namespace: str | None = Field(default=None)
    parameters: list[PluginParameter] = Field(default_factory=list)
    version: str | None = Field(default=None)
    oneshot_arg: str | None = Field(default=None)
    url_regex: str | None = Field(default=None)
    login_from: str | None = Field(default=None)


class PluginUseResponse(OperationResponse):
    type: str | None = Field(default=None)
    data: dict[str, Any] | None = Field(default=None)


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

    def get_opds_catalog(self, archive_id: str = None, category_id: str = None) -> str:
        """
        Get the Archive Index as an OPDS 1.2 Catalog with PSE 1.1 compatibility.
        :param category_id: Category ID. If passed, the OPDS catalog will be
        filtered to only show archives from this category.
        :param archive_id: Backward-compatible argument for getting one OPDS item.
        :return: XML string
        """
        if archive_id:
            return self.get_opds_item(archive_id)

        path = "/api/opds"
        resp = self.request("GET", path, params={"category": category_id})
        return resp.text

    def get_opds_item(self, id: str) -> str:
        """
        Get one OPDS item entry by archive ID.
        :param id: ID of an archive.
        :return: XML string
        """
        resp = self.request("GET", f"/api/opds/{id}")
        return resp.text

    def get_opds_page(self, id: str, page: int = None) -> Response:
        """
        Get an OPDS-PSE image page for an archive.
        :param id: ID of an archive.
        :param page: Optional page number.
        :return: response object with image bytes
        """
        return self.request("GET", f"/api/opds/{id}/pse", params={"page": page})

    def get_available_plugins(self, type: str) -> list[PluginInfo]:
        """
        Get a list of the available plugins on the server, filtered by type.
        :param type: Type of plugins you want to list.
                You can either use 'login', 'metadata', 'script',
                 or 'all' to get all previous types at once.
        :return: list of plugins
        """
        return self.request_model_list("GET", f"/api/plugins/{type}", PluginInfo)

    def use_plugin(
        self, plugin: str, id: str = None, arg: str = None
    ) -> PluginUseResponse:
        """
        Uses a Plugin and returns the result.

        If using a metadata plugin, the matching archive will not be modified
        in the database.

        See more info on Plugins in the matching section of the Docs.
        :param plugin: Namespace of the plugin to use.
        :param id: ID of the archive to use the Plugin on. This is only
        mandatory for metadata plugins.
        :param arg: Optional One-Shot argument to use when executing this
        Plugin.
        :return: operation result
        """
        return self.request_operation(
            "POST",
            "/api/plugins/use",
            model=PluginUseResponse,
            params={"plugin": plugin, "id": id, "arg": arg},
        )

    def use_plugin_async(
        self, plugin: str, id: str = None, arg: str = None, priority: int = 0
    ) -> MinionJobResponse:
        """
        Uses a Plugin and returns a Minion Job ID matching the Plugin run.

        This endpoint is useful if you want to run longer-lived plugins which
        might timeout if ran with the standard endpoint.

        :param plugin: Namespace of the plugin to use.
        :param id: ID of the archive to use the Plugin on. This is only
        mandatory for metadata plugins.
        :param arg: Optional One-Shot argument to use when executing this
        Plugin.
        :param priority: Minion job priority. Higher values are processed first.
        Defaults to 0.
        :return: operation result
        """
        return self.request_operation(
            "POST",
            "/api/plugins/queue",
            model=MinionJobResponse,
            params={"plugin": plugin, "id": id, "arg": arg, "priority": priority},
        )

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
        category_id: str = None,
        use_form_data: bool = False,
    ) -> DownloadUrlResponse:
        """
        Add a URL to be downloaded by the server and added to its library.
        :param url: URL to download
        :param category_id: Category ID to add the downloaded URL to.
        :param use_form_data: Send values as form data instead of query params.
        :return: operation result
        """
        payload = {"url": url, "catid": category_id}
        request_kwargs = {"params": payload}
        if use_form_data:
            request_kwargs = {"data": payload}

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
