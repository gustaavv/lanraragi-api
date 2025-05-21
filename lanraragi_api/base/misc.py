import requests
from pydantic import BaseModel
from script_house.utils import JsonUtils

from lanraragi_api.base.base import BaseAPICall


class ServerInfo(BaseModel):
    archives_per_page: int
    cache_last_cleared: int
    debug_mode: bool
    has_password: bool
    motd: str
    name: str
    nofun_mode: bool
    server_resizes_images: bool
    server_tracks_progress: bool
    total_archives: int
    total_pages_read: int
    version: str
    version_desc: str
    version_name: str


class MiscAPI(BaseAPICall):
    """
    Other APIs that don't fit a dedicated theme.
    """

    def get_server_information(self) -> ServerInfo:
        """
        Returns some basic information about the LRR instance this server is running.
        :return:
        """
        resp = requests.get(f"{self.server}/api/info", params=self.build_params(),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, ServerInfo)

    def get_opds_catalog(self, archive_id: str = None, category_id: str = None) -> str:
        """
        Get the Archive Index as an OPDS 1.2 Catalog with PSE 1.1 compatibility.
        :param archive_id: ID of an archive. Passing this will show only one
        <entry> for the given ID in the result, instead of all the archives.
        :param category_id: Category ID. If passed, the OPDS catalog will be
        filtered to only show archives from this category.
        :return: XML string
        """
        resp = requests.get(f"{self.server}/api/opds{f'/{archive_id}' if archive_id else ''}",
                            params=self.build_params({'category': category_id}),
                            headers=self.build_headers())
        return resp.text

    def get_available_plugins(self, type: str) -> list[dict]:
        """
        Get a list of the available plugins on the server, filtered by type.
        :param type: Type of plugins you want to list.
                You can either use 'login', 'metadata', 'script',
                 or 'all' to get all previous types at once.
        :return: list of plugins
        """
        resp = requests.get(f"{self.server}/api/plugins/{type}", params=self.build_params(),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def use_plugin(self, plugin: str, id: str = None, arg: str = None) -> dict:
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
        resp = requests.post(f"{self.server}/api/plugins/use",
                             params=self.build_params({
                                 'key': self.key,
                                 'plugin': plugin,
                                 'id': id,
                                 'arg': arg}),
                             headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def use_plugin_async(self, plugin: str, id: str = None, arg: str = None) -> dict:
        """
        Uses a Plugin and returns a Minion Job ID matching the Plugin run.

        This endpoint is useful if you want to run longer-lived plugins which
        might timeout if ran with the standard endpoint.

        :param plugin: Namespace of the plugin to use.
        :param id: ID of the archive to use the Plugin on. This is only
        mandatory for metadata plugins.
        :param arg: Optional One-Shot argument to use when executing this
        Plugin.
        :return: operation result
        """
        resp = requests.post(f"{self.server}/api/plugins/queue",
                             params=self.build_params({
                                 'key': self.key,
                                 'plugin': plugin,
                                 'id': id,
                                 'arg': arg}),
                             headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def clean_temporary_folder(self) -> dict:
        """
        Cleans the server's temporary folder.
        :return: operation result
        """
        resp = requests.delete(f"{self.server}/api/tempfolder", params=self.build_params(),
                               headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def queue_url_to_download(self, url: str, category_id: str = None) -> dict:
        """
        Add a URL to be downloaded by the server and added to its library.
        :param url: URL to download
        :param category_id: Category ID to add the downloaded URL to.
        :return: operation result
        """
        resp = requests.post(f"{self.server}/api/download_url",
                             params=self.build_params({'url': url, 'catid': category_id}),
                             headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def regenerate_thumbnails(self, force: bool = False) -> dict:
        """
        Queue a Minion job to regenerate missing/all thumbnails on the server.
        :param force: Whether to generate all thumbnails, or only the missing ones.
        :return: operation result
        """
        resp = requests.post(f"{self.server}/api/regen_thumbs",
                             params=self.build_params({'force': force if force else None}),
                             headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)
