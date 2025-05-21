from os.path import isfile
from typing import Optional

import requests
from pydantic import BaseModel
from requests import Response
from script_house.utils import JsonUtils

from lanraragi_api.base.base import BaseAPICall
from lanraragi_api.base.category import Category

ARCHIVE_TAG_VALUES_SET = "ONLY_VALUES"


class Archive(BaseModel):
    arcid: str
    extension: str
    filename: str
    isnew: str
    lastreadtime: int
    pagecount: int
    progress: int
    size: int
    summary: str

    # k1:v1, k2:v21, k2:v22, v3, v4
    # allow duplicate keys, only values
    tags: str
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

    def get_artists(self) -> list[str]:
        return self.__tags_to_dict()['artist']

    def set_artists(self, artists: list[str]):
        json = self.__tags_to_dict()
        json['artist'] = artists
        self.__dict_to_tags(json)

    def remove_artists(self):
        json = self.__tags_to_dict()
        json['artist'] = []
        self.__dict_to_tags(json)

    def has_artists(self) -> bool:
        return "artist" in self.tags


class ArchiveAPI(BaseAPICall):
    """
    Everything dealing with Archives.
    """

    def get_all_archives(self) -> list[Archive]:
        """
        Get the Archive Index in JSON form. You can use the IDs of this JSON
        with the other endpoints.
        :return: list of archives
        """
        resp = requests.get(f"{self.server}/api/archives", params=self.build_params(),
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
        resp = requests.get(f"{self.server}/api/archives/untagged", params=self.build_params(),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def get_archive_metadata(self, id: str) -> Optional[Archive]:
        """
        Get Metadata (title, tags) for a given Archive.
        :param id: ID of the Archive to process.
        :return: archive
        """
        resp = requests.get(f"{self.server}/api/archives/{id}/metadata", params=self.build_params(),
                            headers=self.build_headers())
        if resp.status_code == 400:
            return None
        return JsonUtils.to_obj(resp.text, Archive)

    def get_archive_categories(self, id: str) -> list[Category]:
        """
        Get all the Categories which currently refer to this Archive ID.
        :param id: ID of the Archive to process.
        :return:
        """
        resp = requests.get(f"{self.server}/api/archives/{id}/categories", params=self.build_params(),
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
        resp = requests.get(f"{self.server}/api/archives/{id}/tankoubons", params=self.build_params(),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)['tankoubons']

    def get_archive_thumbnail(self, id: str, page: int = 1, no_fallback: bool = False) -> Response:
        """
        Get a Thumbnail image for a given Archive. This endpoint will return
        a placeholder image if it doesn't already exist.

        If you want to queue generation of the thumbnail in the background,
        you can use the no_fallback query parameter. This will give you a
        background job ID instead of the placeholder.

        :param id: ID of the Archive to process.
        :param page: Specify which page you want to get a thumbnail for.
        Defaults to the cover, aka page 1.
        :param no_fallback: Disables the placeholder image, queues the
        thumbnail for extraction and returns a JSON with code 202. This
        parameter does nothing if the image already exists. (You will get the
        image with code 200 no matter what)
        :return: the response object
        """
        resp = requests.get(f"{self.server}/api/archives/{id}/thumbnail",
                            params=self.build_params({'page': page, 'no_fallback': no_fallback}),
                            headers=self.build_headers())
        return resp

    def queue_extraction_of_page_thumbnails(self, id: str, force: bool = False) -> Response:
        """
        Create thumbnails for every page of a given Archive. This endpoint will
        queue generation of the thumbnails in the background.

        If all thumbnails are detected as already existing, the call will
        return HTTP code 200.

        This endpoint can be called multiple times -- If a thumbnailing job is
        already in progress for the given ID, it'll just give you the ID for
        that ongoing job.
        :param id: ID of the Archive to process.
        :param force: Whether to force regeneration of all thumbnails even if
        they already exist.
        :return: operation result
        """
        resp = requests.post(f"{self.server}/api/archives/{id}/files/thumbnails",
                             params=self.build_params({'force': force}),
                             headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def download_archive(self, id: str) -> Response:
        """
        Download an Archive from the server.

        :param id: ID of the Archive to download.
        :return: the response object
        """
        resp = requests.get(f"{self.server}/api/archives/{id}/download", params=self.build_params(),
                            headers=self.build_headers())
        return resp

    def extract_archive(self, id: str, force: bool = False) -> dict:
        """
        Get a list of URLs pointing to the images contained in an archive.
        If necessary, this endpoint also launches a background Minion job to
        extract the archive so it is ready for reading.

        :param id: ID of the Archive to process.
        :param force: Force a full background re-extraction of the Archive.
        Existing cached files might still be used in subsequent
        /api/archives/:id/page calls until the Archive is fully re-extracted.
        :return: operation result
        """
        resp = requests.get(f"{self.server}/api/archives/{id}/files",
                            params=self.build_params({'force': force}),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def clear_archive_new_flag(self, id: str) -> dict:
        """
        Clears the "New!" flag on an archive.

        :param id: ID of the Archive to process.
        :return: operation result
        """
        resp = requests.delete(f"{self.server}/api/archives/{id}/isnew", params=self.build_params(),
                               headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def update_reading_progression(self, id: str, page: int) -> dict:
        """
        Tell the server which page of this Archive you're currently
        showing/reading, so that it updates its internal reading progression
        accordingly.

        This endpoint will also update the date this Archive was last read,
        using the current server timestamp.

        You should call this endpoint only when you're sure the user is
        currently reading the page you present.

        Don't use it when preloading images off the server.

        Whether to make reading progression regressible or not is up to
         the client. (The web client will reduce progression if the user
         starts reading previous pages)

        Consider however removing the "New!" flag from an archive when you
        start updating its progress - The web client won't display any
        reading progression if the new flag is still set.

        ⚠ If the server is configured to use clientside progress tracking,
        this API call will return an error!

        Make sure to check using /api/info whether the server tracks reading
        progression or not before calling this endpoint.
        :param id: ID of the Archive to process
        :param page: Current page to update the reading progress to. Must be
        a positive integer, and inferior or equal to the total page number of
        the archive.
        :return: operation result
        """
        resp = requests.put(f"{self.server}/api/archives/{id}/progress/{page}", params=self.build_params(),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def upload_archive(self, archive_path: str, title: str = None, tags: str = None, summary: str = None,
                       category_id: int = None, file_checksum: str = None) -> dict:
        """
        Upload an Archive to the server.

        If a SHA1 checksum of the Archive is included, the server will perform
        an optional in-transit, file integrity validation, and reject the
        upload if the server-side checksum does not match.
        :param archive_path: filepath of the archive
        :param title: Title of the Archive.
        :param tags: Set of tags you want to insert in the database alongside
        the archive.
        :param summary: summary
        :param category_id: Category ID you'd want the archive to be added to.
        :param file_checksum: SHA1 checksum of the archive for in-transit
        validation.
        :return: operation result
        """
        # deal with windows path separator
        archive_path = archive_path.replace('\\', '/')

        if not isfile(archive_path):
            raise FileNotFoundError(f"File {archive_path} not found")

        resp = requests.put(f"{self.server}/api/archives/upload",
                            params=self.build_params(),
                            headers=self.build_headers(),
                            files={"file": (
                                archive_path.split("/")[-1], open(archive_path, "rb"), "application/octet-stream"
                            )},
                            data={
                                'title': title,
                                'tags': tags,
                                'summary': summary,
                                'category_id': category_id,
                                'file_checksum': file_checksum,
                            })

        return JsonUtils.to_obj(resp.text)

    def update_thumbnail(self, id: str, page: int = 1) -> dict:
        """
        Update the cover thumbnail for the given Archive. You can specify a
        page number to use as the thumbnail, or you can use the default
        thumbnail.
        :param id: ID of the Archive to process.
        :param page: Page you want to make the thumbnail out of. Defaults to 1.
        :return: operation result
        """
        resp = requests.put(f"{self.server}/api/archives/{id}/thumbnail",
                            params=self.build_params({'page': page}),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def update_archive_metadata(self, id: str, archive: Archive) -> dict:
        """
        Update tags and title for the given Archive. Data supplied to the
        server through this method will overwrite the previous data.
        :param archive: the Archive whose tags and title will be updated
        :param id: ID of the Archive to process.
        :return: operation result
        """

        resp = requests.put(f"{self.server}/api/archives/{id}/metadata",
                            params=self.build_params({
                                'title': archive.title,
                                'tags': archive.tags
                            }), headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def delete_archive(self, id: str) -> dict:
        """
        Delete both the archive metadata and the file stored on the server.

        🙏 Please ask your user for confirmation before invoking this endpoint.
        :param id: ID of the Archive to process.
        :return: operation result
        """
        resp = requests.delete(f"{self.server}/api/archives/{id}", params=self.build_params(),
                               headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)
