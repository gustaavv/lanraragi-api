import requests
from pydantic import BaseModel
from script_house.utils import JsonUtils

from ..common.base import BaseAPICall


class ServerInfo(BaseModel):
    archives_per_page: str
    cache_last_cleared: str
    debug_mode: str
    has_password: str
    motd: str
    name: str
    nofun_mode: str
    server_resizes_images: str
    server_tracks_progress: str
    total_pages_read: int
    version: str
    version_desc: str
    version_name: str


class OtherAPI(BaseAPICall):
    """
    Other APIs that don't fit a dedicated theme.
    """

    def get_server_information(self) -> ServerInfo:
        """
        Returns some basic information about the LRR instance this server is running.
        :return:
        """
        resp = requests.get(f"{self.server}/api/info", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, ServerInfo)

    def get_opds_catalog(self):
        pass

    def get_available_plugins(self, type: str) -> list[dict]:
        """
        Get a list of the available plugins on the server, filtered by type.
        :param type: Type of plugins you want to list.
                You can either use 'login', 'metadata', 'script',
                 or 'all' to get all previous types at once.
        :return: list of plugins
        """
        resp = requests.get(f"{self.server}/api/plugins/{type}", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def use_plugin(self):
        pass

    def use_plugin_async(self):
        pass

    def clean_temporary_folder(self) -> bool:
        """
        Cleans the server's temporary folder.
        :return: whether the operation succeeds or not
        """
        # TODO: untested
        resp = requests.delete(f"{self.server}/api/tempfolder", params={'key': self.key},
                               headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)['success'] == 1

    def queue_url_to_download(self):
        pass

    def generate_thumbnails(self, all: bool = False) -> int:
        """
        Queue a Minion job to regenerate missing/all thumbnails on the server.
        :param all: Whether to generate all thumbnails, or only the missing ones.
        :return: job id
        """
        # TODO: untested
        resp = requests.post(f"{self.server}/api/regen_thumbs", params={'key': self.key, 'force': all},
                             headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)["job"]
