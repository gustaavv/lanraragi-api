import requests
from pydantic import BaseModel
from script_house.utils import JsonUtils

from lanraragi_api.Config import assert_use_untested_functions
from lanraragi_api.base.base import BaseAPICall
from lanraragi_api.base.category import Category

ARCHIVE_TAG_VALUES_SET = "ONLY_VALUES"


class Archive(BaseModel):
    arcid: str
    isnew: str
    extension: str
    pagecount: int
    progress: int
    # k1:v1, k2:v21, k2:v22, v3, v4
    # allow duplicate keys, only values
    tags: str
    lastreadtime: int
    title: str

    def __tags_to_dict(self) -> dict[str, list[str]]:
        tags = self.tags.split(',')
        ans = {}
        for t in tags:
            if t == '':
                continue
            t = t.strip()
            if ':' in t:
                kv = t.split(':')
                k = kv[0]
                v = kv[1]
                if k not in ans:
                    ans[k] = []
                ans[k].append(v)
            else:
                k = ARCHIVE_TAG_VALUES_SET
                if k not in ans:
                    ans[k] = []
                ans[k].append(t)
        return ans

    def __dict_to_tags(self, json: dict[str, list[str]]):
        """
        The function will modify the object
        """
        tags = ""
        modified: bool = False
        for k in json:
            for v in json[k]:
                modified = True
                if k == ARCHIVE_TAG_VALUES_SET:
                    tags += f"{v},"
                else:
                    tags += f"{k}:{v},"
        if modified:
            tags = tags[:-1]
        self.tags = tags

    def set_artists(self, artists: list[str]):
        json = self.__tags_to_dict()
        json['artist'] = artists
        self.__dict_to_tags(json)

    def has_artists(self) -> bool:
        return "artist" in self.tags


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

    def clear_archive_new_flag(self, id: str) -> dict:
        """
        Clears the "New!" flag on an archive.

        :param id: ID of the Archive to process.
        :return: operation result
        """
        # TODO: untested
        assert_use_untested_functions()
        resp = requests.delete(f"{self.server}/api/archives/{id}/isnew", params={'key': self.key},
                               headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def update_reading_progression(self):
        # TODO: used not so often
        pass

    def update_thumbnail(self):
        # TODO: used not so often
        pass

    def update_archive_metadata(self, id: str, archive: Archive) -> dict:
        """
        Update tags and title for the given Archive. Data supplied to the server through
        this method will <b>overwrite</b> the previous data.
        :param archive: the Archive whose tags and title will be updated
        :param id: ID of the Archive to process.
        :return: operation result
        """
        resp = requests.put(f"{self.server}/api/archives/{id}/metadata", params={
            'key': self.key,
            'title': archive.title,
            'tags': archive.tags
        }, headers=self.build_headers())
        return JsonUtils.to_obj(resp)

    def delete_archive(self, id: str) -> dict:
        """
        Delete both the archive metadata and the file stored on the server.
        :param id: ID of the Archive to process.
        :return: operation result
        """
        # This function is not implemented on purpose. Just because it is
        # too dangerous.
        raise NotImplementedError
