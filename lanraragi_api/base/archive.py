from os.path import isfile
from typing import Optional

from pydantic import BaseModel, Field
from requests import Response

from lanraragi_api.base.base import (
    APIResponseDecodeError,
    BaseAPICall,
    MinionJobResponse,
    OperationResponse,
)
from lanraragi_api.base.category import CategoryMetadata

ARCHIVE_TAG_VALUES_SET = "ONLY_VALUES"


class ArchiveMetadata(BaseModel):
    arcid: str = Field(...)
    extension: str = Field(...)
    filename: str = Field(...)
    isnew: bool | str | None = Field(default=None)
    lastreadtime: int = Field(...)
    pagecount: int = Field(...)
    progress: int = Field(...)
    size: int = Field(...)
    summary: str | None = Field(default=None)
    toc: list[dict] | None = Field(default=None)

    # k1:v1, k2:v21, k2:v22, v3, v4
    # allow duplicate keys, only values
    tags: str = Field(...)
    title: str = Field(...)

    def __tags_to_dict(self) -> dict[str, list[str]]:
        tags = self.tags.split(",")
        ans = {}
        for t in tags:
            if t == "":
                continue
            t = t.strip()
            if ":" in t:
                kv = t.split(":")
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
        return self.__tags_to_dict()["artist"]

    def set_artists(self, artists: list[str]):
        json = self.__tags_to_dict()
        json["artist"] = artists
        self.__dict_to_tags(json)

    def remove_artists(self):
        json = self.__tags_to_dict()
        json["artist"] = []
        self.__dict_to_tags(json)

    def has_artists(self) -> bool:
        return "artist" in self.tags


class ArchiveAPI(BaseAPICall):
    """
    Everything dealing with Archives.
    """

    def get_all_archives(self) -> list[ArchiveMetadata]:
        """
        Get the Archive Index in JSON form. You can use the IDs of this JSON
        with the other endpoints.
        :return: list of archives
        """
        return self.request_model_list("GET", "/api/archives", ArchiveMetadata)

    def get_archive(self, id: str) -> Optional[ArchiveMetadata]:
        """
        Get Metadata (title, tags) for a given Archive using deprecated endpoint.
        :param id: ID of the Archive to process.
        :return: archive
        """
        path = f"/api/archives/{id}"
        resp = self.request("GET", path, expected_statuses={200, 400})
        if resp.status_code == 400:
            return None
        payload = self.parse_json_response(resp, path)
        return self.parse_model(ArchiveMetadata, payload, path)

    def get_untagged_archives(self) -> list[str]:
        """
        Get archives that don't have any tags recorded. This follows the same
        rules as the Batch Tagging filter and will include archives that have
        parody:, date_added:, series: or artist: tags.
        :return: list of archive IDs
        """
        path = "/api/archives/untagged"
        payload = self.request_json("GET", path)
        if not isinstance(payload, list):
            raise APIResponseDecodeError(self._to_url(path), "response is not a list")
        return payload

    def get_archive_metadata(self, id: str) -> Optional[ArchiveMetadata]:
        """
        Get Metadata (title, tags) for a given Archive.
        :param id: ID of the Archive to process.
        :return: archive
        """
        path = f"/api/archives/{id}/metadata"
        resp = self.request("GET", path, expected_statuses={200, 400})
        if resp.status_code == 400:
            return None
        payload = self.parse_json_response(resp, path)
        return self.parse_model(ArchiveMetadata, payload, path)

    def get_archive_categories(self, id: str) -> list[CategoryMetadata]:
        """
        Get all the Categories which currently refer to this Archive ID.
        :param id: ID of the Archive to process.
        :return: list of category metadata
        """
        path = f"/api/archives/{id}/categories"
        payload = self.request_json("GET", path)
        clist = payload.get("categories")
        if not isinstance(clist, list):
            raise APIResponseDecodeError(self._to_url(path), "missing categories list")
        return [self.parse_model(CategoryMetadata, c, path) for c in clist]

    def get_archive_tankoubons(self, id: str) -> list[str]:
        """
        Get all the Tankoubons which currently refer to this Archive ID.

        Tankoubon: 単行本
        :param id: ID of the Archive to process.
        :return: list of tankoubon ids
        """
        path = f"/api/archives/{id}/tankoubons"
        payload = self.request_json("GET", path)
        tankoubons = payload.get("tankoubons")
        if not isinstance(tankoubons, list):
            raise APIResponseDecodeError(self._to_url(path), "missing tankoubons list")
        return tankoubons

    def get_archive_thumbnail(
        self, id: str, page: int = 1, no_fallback: bool | None = None
    ) -> Response:
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
        no_fallback_value = None
        if no_fallback is not None:
            no_fallback_value = "true" if no_fallback else "false"

        return self.request(
            "GET",
            f"/api/archives/{id}/thumbnail",
            params={"page": page, "no_fallback": no_fallback_value},
        )

    def queue_extraction_of_page_thumbnails(
        self, id: str, force: bool = False
    ) -> MinionJobResponse:
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
        return self.request_operation(
            "POST",
            f"/api/archives/{id}/files/thumbnails",
            model=MinionJobResponse,
            params={"force": force},
        )

    def download_archive(self, id: str) -> Response:
        """
        Download an Archive from the server.

        :param id: ID of the Archive to download.
        :return: the response object
        """
        return self.request("GET", f"/api/archives/{id}/download")

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
        return self.request_json(
            "GET", f"/api/archives/{id}/files", params={"force": force}
        )

    def add_archive_toc(self, id: str, page: int, title: str) -> OperationResponse:
        """
        Add a Table of Contents entry for an archive.
        :param id: ID of the Archive to process.
        :param page: Page number where the chapter starts.
        :param title: Chapter title.
        :return: operation result
        """
        return self.request_operation(
            "PUT", f"/api/archives/{id}/toc", params={"page": page, "title": title}
        )

    def delete_archive_toc(self, id: str, page: int) -> OperationResponse:
        """
        Delete a Table of Contents entry for an archive.
        :param id: ID of the Archive to process.
        :param page: Page number of the chapter entry to remove.
        :return: operation result
        """
        return self.request_operation(
            "DELETE", f"/api/archives/{id}/toc", params={"page": page}
        )

    def get_archive_page(self, id: str, path: str) -> Response:
        """
        Get a specific image page from an archive.
        :param id: ID of the Archive to process.
        :param path: Path to the image in extracted archive files.
        :return: the response object
        """
        return self.request("GET", f"/api/archives/{id}/page", params={"path": path})

    def set_archive_new_flag(self, id: str) -> OperationResponse:
        """
        Sets/restores the "New!" flag on an archive.

        :param id: ID of the Archive to process.
        :return: operation result
        """
        return self.request_operation("PUT", f"/api/archives/{id}/isnew")

    def clear_archive_new_flag(self, id: str) -> OperationResponse:
        """
        Clears the "New!" flag on an archive.

        :param id: ID of the Archive to process.
        :return: operation result
        """
        return self.request_operation("DELETE", f"/api/archives/{id}/isnew")

    def update_reading_progression(self, id: str, page: int) -> OperationResponse:
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
        return self.request_operation("PUT", f"/api/archives/{id}/progress/{page}")

    def upload_archive(
        self,
        archive_path: str,
        title: str = None,
        tags: str = None,
        summary: str = None,
        category_id: str = None,
        file_checksum: str = None,
    ) -> OperationResponse:
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
        archive_path = archive_path.replace("\\", "/")

        if not isfile(archive_path):
            raise FileNotFoundError(f"File {archive_path} not found")

        with open(archive_path, "rb") as archive_file:
            return self.request_operation(
                "PUT",
                "/api/archives/upload",
                files={
                    "file": (
                        archive_path.split("/")[-1],
                        archive_file,
                        "application/octet-stream",
                    )
                },
                data={
                    "title": title,
                    "tags": tags,
                    "summary": summary,
                    "category_id": category_id,
                    "file_checksum": file_checksum,
                },
            )

    def update_thumbnail(self, id: str, page: int = 1) -> OperationResponse:
        """
        Update the cover thumbnail for the given Archive. You can specify a
        page number to use as the thumbnail, or you can use the default
        thumbnail.
        :param id: ID of the Archive to process.
        :param page: Page you want to make the thumbnail out of. Defaults to 1.
        :return: operation result
        """
        return self.request_operation(
            "PUT", f"/api/archives/{id}/thumbnail", params={"page": page}
        )

    def update_archive_metadata(
        self,
        id: str,
        archive: ArchiveMetadata | None = None,
        *,
        title: str | None = None,
        tags: str | None = None,
        summary: str | None = None,
    ) -> OperationResponse:
        """
        Update tags, title and summary for the given Archive.
        :param id: ID of the Archive to process.
        :param archive: Optional backward-compatible metadata object.
        :param title: Archive title to set. If omitted and archive is provided,
        uses archive.title.
        :param tags: Archive tags string to set. If omitted and archive is
        provided, uses archive.tags.
        :param summary: Archive summary to set. If omitted and archive is
        provided, uses archive.summary.
        :return: operation result
        """
        if archive is not None:
            if title is None:
                title = archive.title
            if tags is None:
                tags = archive.tags
            if summary is None:
                summary = archive.summary

        return self.request_operation(
            "PUT",
            f"/api/archives/{id}/metadata",
            params={"title": title, "tags": tags, "summary": summary},
        )

    def delete_archive(self, id: str) -> OperationResponse:
        """
        Delete both the archive metadata and the file stored on the server.

        🙏 Please ask your user for confirmation before invoking this endpoint.
        :param id: ID of the Archive to process.
        :return: operation result
        """
        return self.request_operation("DELETE", f"/api/archives/{id}")
