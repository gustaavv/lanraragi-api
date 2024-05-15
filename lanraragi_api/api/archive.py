from script_house.utils import JsonUtils
import requests

from ..common.base import BaseAPICall
from ..common.entity import Archive, Category


class ArchiveAPI(BaseAPICall):
    """
    Everything dealing with Archives.
    """
    def get_all_archives(self) -> list[Archive]:
        resp = requests.get(f"{self.server}/api/archives", params={'key': self.key},
                            headers=self.build_headers())
        list = JsonUtils.to_obj(resp.text)
        return [JsonUtils.to_obj(JsonUtils.to_str(o), Archive) for o in list]

    def get_untagged_archives(self) -> list[str]:
        """
        Get archives that don't have any tags recorded. This follows the same
        rules as the Batch Tagging filter and will include archives that have
        parody:, date_added:, series: or artist: tags.
        :return: list of archive IDs
        """
        resp = requests.get(f"{self.server}/api/archives/untagged", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def get_archive_metadata(self, id: str) -> Archive:
        """
        Get Metadata (title, tags) for a given Archive.
        :param id: ID of the Archive to process.
        :return:
        """
        resp = requests.get(f"{self.server}/api/archives/{id}/metadata", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, Archive)

    def get_archive_categories(self, id: str) -> list[Category]:
        """
        Get all the Categories which currently refer to this Archive ID.
        :param id: ID of the Archive to process.
        :return:
        """
        resp = requests.get(f"{self.server}/api/archives/{id}/categories", params={'key': self.key},
                            headers=self.build_headers())
        clist = JsonUtils.to_obj(resp.text)["categories"]
        return [JsonUtils.to_obj(JsonUtils.to_str(c), Category) for c in clist]

    def get_archive_tankoubons(self, id: str) -> list[str]:
        """
        Get all the Tankoubons which currently refer to this Archive ID.

        Tankoubon: 単行本
        :param id: ID of the Archive to process.
        :return: list of tankoubon ids
        """
        resp = requests.get(f"{self.server}/api/archives/{id}/tankoubons", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)['tankoubons']

    def get_archive_thumbnail(self):
        # TODO: used not so often
        pass

    def download_archive(self, id: str) -> bytes:
        """
        Download an Archive from the server.

        :param id: ID of the Archive to download.
        :return: bytes representing the archive. You can write it to a file.
        """
        resp = requests.get(f"{self.server}/api/archives/{id}/download", params={'key': self.key},
                            headers=self.build_headers())
        return resp.content

    def extract_archive(self):
        # TODO: used not so often
        pass

    def clear_archive_new_flag(self, id: str) -> bool:
        """
        Clears the "New!" flag on an archive.

        :param id: ID of the Archive to process.
        :return: succeed or not
        """
        # TODO: untested
        resp = requests.delete(f"{self.server}/api/archives/{id}/isnew", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)['success'] == 1

    def update_reading_progression(self):
        # TODO: used not so often
        pass

    def update_thumbnail(self):
        # TODO: used not so often
        pass

    def update_archive_metadata(self, id: str, archive: Archive) -> bool:
        """
        Update tags and title for the given Archive. Data supplied to the server through
        this method will <b>overwrite</b> the previous data.
        :param archive: the Archive whose tags and title will be updated
        :param id: ID of the Archive to process.
        :return: whether update succeeds
        """
        resp = requests.put(f"{self.server}/api/archives/{id}/metadata", params={
            'key': self.key,
            'title': archive.title,
            'tags': archive.tags
        }, headers=self.build_headers())
        return resp.status_code == 200

    def delete_archive(self, id: str):
        """
        Delete both the archive metadata and the file stored on the server.
        :param id: ID of the Archive to process.
        :return: succeed or not
        """
        # This function is not implemented on purpose. Just because it is
        # too dangerous.
        raise NotImplementedError
