from typing import Any

from pydantic import AliasChoices, BaseModel, Field
from requests import Response

from lanraragi_api.base.archive import ArchiveMetadata
from lanraragi_api.base.base import (
    APIResponseDecodeError,
    BaseAPICall,
    DictLikeModel,
    OperationResponse,
)


class TankoubonMetadata(BaseModel):
    archives: list[str] = Field(...)
    full_data: list[ArchiveMetadata] | None = Field(default=None)
    tankid: str = Field(..., validation_alias=AliasChoices("tankid", "id"))
    name: str = Field(...)
    summary: str | None = Field(default=None)
    tags: str | None = Field(default=None)
    progress: int | None = Field(default=None)

    @property
    def id(self) -> str:
        """Backward-compatible alias for tankid."""
        return self.tankid


class TankoubonListResponse(DictLikeModel):
    result: list[TankoubonMetadata] = Field(default_factory=list)
    total: int | None = Field(default=None)
    filtered: int | None = Field(default=None)


class TankoubonDetailResponse(DictLikeModel):
    result: TankoubonMetadata = Field(...)
    total: int | None = Field(default=None)
    filtered: int | None = Field(default=None)


class TankoubonAPI(BaseAPICall):
    """
    Tankoubon API.
    """

    def get_tankoubon_list(self, page: int | None = None) -> TankoubonListResponse:
        """
        Get list of Tankoubons paginated.
        :param page: Page of the list of Tankoubons.
        :return: Tankoubon list response
        """
        path = "/api/tankoubons"
        payload = self.request_json("GET", path, params={"page": page})
        result = payload.get("result")
        if not isinstance(result, list):
            raise APIResponseDecodeError(self._to_url(path), "missing result list")
        return TankoubonListResponse(
            result=[self.parse_model(TankoubonMetadata, t, path) for t in result],
            total=payload.get("total"),
            filtered=payload.get("filtered"),
        )

    def get_all_tankoubons(self, page: int | None = None) -> list[TankoubonMetadata]:
        """
        Backward-compatible wrapper returning only the tankoubon list.
        :param page: Page of the list of Tankoubons.
        :return: list of Tankoubons
        """
        return self.get_tankoubon_list(page=page).result

    def get_tankoubon_detail(
        self,
        id: str,
    ) -> TankoubonMetadata:
        """
        Get the details of the specified tankoubon ID.

        :param id: ID of the Tankoubon desired.
        :return: Tankoubon metadata
        """
        path = f"/api/tankoubons/{id}"
        payload = self.request_json("GET", path)
        return self.parse_model(TankoubonMetadata, payload, path)

    def get_tankoubon_full(
        self,
        id: str,
        page: int = -1,
    ) -> TankoubonDetailResponse:
        """
        Get the details of the specified tankoubon ID with paginated archive
        metadata.

        The amount of archives per page depends on the server
        ``archives_per_page`` setting.

        :param id: ID of the Tankoubon desired.
        :param page: Page of the Archives list. Defaults to -1, which returns
            all archives.
        :return: Tankoubon detail response with full_data
        """
        path = f"/api/tankoubons/{id}/full"
        payload = self.request_json(
            "GET",
            path,
            params={"page": page},
        )
        result = payload.get("result")
        if result is None:
            raise APIResponseDecodeError(self._to_url(path), "missing result payload")
        return TankoubonDetailResponse(
            result=self.parse_model(TankoubonMetadata, result, path),
            total=payload.get("total"),
            filtered=payload.get("filtered"),
        )

    def get_tankoubon(self, id: str) -> TankoubonMetadata:
        """
        Get the details of the specified tankoubon ID.

        :param id: ID of the Tankoubon desired.
        :return: Tankoubon
        """
        return self.get_tankoubon_detail(id=id)

    def get_tankoubon_thumbnail(
        self,
        id: str,
        no_fallback: bool | None = None,
    ) -> Response:
        """
        Get the cover thumbnail for a given Tankoubon.

        By default, the thumbnail is sourced from the first page of the first
        archive. This endpoint will return a placeholder image if it doesn't
        already exist. If you want to queue generation of the thumbnail in the
        background, you can use the no_fallback query parameter.

        :param id: ID of the Tankoubon desired.
        :param no_fallback: Disables the placeholder image, queues the
            thumbnail for extraction and returns a JSON with code 202. This
            parameter does nothing if the image already exists. (You will get
            the image with code 200 no matter what)
        :return: the response object (image bytes or 202 JSON)
        """
        no_fallback_value = None
        if no_fallback is not None:
            no_fallback_value = "true" if no_fallback else "false"

        return self.request(
            "GET",
            f"/api/tankoubons/{id}/thumbnail",
            params={"no_fallback": no_fallback_value},
        )

    def update_tankoubon_thumbnail(self, id: str, page: int) -> OperationResponse:
        """
        Set the cover thumbnail for the given Tankoubon using a global page
        number that spans all archives in the tank (in order). The global page
        is translated to the correct archive and local page automatically.

        :param id: ID of the Tankoubon desired.
        :param page: Global 1-indexed page number across all archives in the
            tankoubon. Page 1 is the first page of the first archive, and so on.
        :return: operation result
        """
        return self.request_operation(
            "PUT",
            f"/api/tankoubons/{id}/thumbnail",
            params={"page": page},
        )

    def update_tank_progress(self, id: str, page: int) -> OperationResponse:
        """
        Tell the server which page of this Tankoubon you're currently reading,
        so that it updates its internal reading progression accordingly.

        The page number is global across all Archives in the tank (If a tank
        has two Archives with 20 and 25 pages, page 26 will be page 6 in
        Archive #2).

        If the server is configured to use clientside progress tracking, this
        API call will return an error!

        Make sure to check using ``/api/info`` whether the server tracks
        reading progression or not before calling this endpoint.

        :param id: ID of the Tankoubon to update.
        :param page: Global 1-indexed page number to update the reading
            progress to. Must be a positive integer.
        :return: operation result
        """
        return self.request_operation("PUT", f"/api/tankoubons/{id}/progress/{page}")

    def create_tankoubon(
        self, name: str, tankid: str | None = None
    ) -> OperationResponse:
        """
        Create a new Tankoubon or updated the name of an existing one.
        :param name: Name of the Tankoubon.
        :param tankid: Existing Tankoubon ID, if renaming.
        :return: operation result
        """
        return self.request_operation(
            "PUT", "/api/tankoubons", data={"name": name, "tankid": tankid}
        )

    def update_tankoubon(
        self,
        id: str,
        archives: list[str] | None = None,
        name: str | None = None,
        summary: str | None = None,
        tags: str | None = None,
        append: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OperationResponse:
        """
        Update Tankoubon metadata and/or contents.
        :param id: ID of the Tankoubon to update.
        :param archives: Ordered list of archive IDs.
        :param name: Optional metadata name.
        :param summary: Optional metadata summary.
        :param tags: Optional metadata tags. This will replace whatever
            additional tags the Tank already has, unless ``append`` is True.
        :param append: If True, tags are appended to the Tank's existing own
            tags instead of replacing them. Defaults to False.
        :param metadata: Optional metadata payload, merged with explicit args.
        :return: operation result
        """
        payload: dict[str, Any] = {}
        if archives is not None:
            payload["archives"] = archives

        metadata_payload = {} if metadata is None else dict(metadata)
        if name is not None:
            metadata_payload["name"] = name
        if summary is not None:
            metadata_payload["summary"] = summary
        if tags is not None:
            metadata_payload["tags"] = tags
        if append is not None:
            metadata_payload["append"] = append

        if metadata_payload:
            payload["metadata"] = metadata_payload

        return self.request_operation("PUT", f"/api/tankoubons/{id}", json=payload)

    def add_archive_to_tankoubon(
        self, tankoubon_id: str, archive_id: str
    ) -> OperationResponse:
        """
        Append an archive at the final position of a Tankoubon.
        :param tankoubon_id: ID of the Tankoubon to update.
        :param archive_id: ID of the Archive to append.
        :return: operation result
        """
        return self.request_operation(
            "PUT", f"/api/tankoubons/{tankoubon_id}/{archive_id}"
        )

    def remove_archive_from_tankoubon(
        self, tankoubon_id: str, archive_id: str
    ) -> OperationResponse:
        """
        Remove an archive from a Tankoubon.
        :param tankoubon_id: ID of the Tankoubon to update.
        :param archive_id: ID of the archive to remove.
        :return: operation result
        """
        return self.request_operation(
            "DELETE", f"/api/tankoubons/{tankoubon_id}/{archive_id}"
        )

    def delete_tankoubon(self, id: str) -> OperationResponse:
        """
        Remove a Tankoubon.
        :param id: ID of the Tankoubon to delete.
        :return: operation result
        """
        return self.request_operation("DELETE", f"/api/tankoubons/{id}")
