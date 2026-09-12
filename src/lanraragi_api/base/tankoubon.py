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
    """Metadata of a single Tankoubon.

    Tankoubon metadata as returned by the list endpoint, with the archive IDs
    it contains and optional full archive metadata.

    Attributes:
        archives: Array of archive IDs contained in this Tankoubon.
        full_data: Archive metadata of the archives, filled by the full detail
            endpoint only.
        tankid: ID of the tankoubon.
        name: Name of the tankoubon.
        summary: Summary of the tankoubon.
        tags: Tags associated with the tankoubon.
        progress: Reading progress (page number) for this Tankoubon.
    """

    archives: list[str] = Field(...)
    full_data: list[ArchiveMetadata] | None = Field(default=None)
    tankid: str = Field(..., validation_alias=AliasChoices("tankid", "id"))
    name: str = Field(...)
    summary: str | None = Field(default=None)
    tags: str | None = Field(default=None)
    progress: int | None = Field(default=None)

    @property
    def id(self) -> str:
        """Return the ID of the tankoubon.

        This is a backward-compatible alias for the ``tankid`` field.

        Returns:
            str: ID of the tankoubon.
        """
        return self.tankid


class TankoubonListResponse(DictLikeModel):
    """Paginated list of Tankoubons returned by the list endpoint.

    Attributes:
        result: Tankoubons of the current page.
        total: Total count of Tankoubons on the server.
        filtered: Number of Tankoubons on the current page.
    """

    result: list[TankoubonMetadata] = Field(default_factory=list)
    total: int | None = Field(default=None)
    filtered: int | None = Field(default=None)


class TankoubonDetailResponse(DictLikeModel):
    """Tankoubon returned by the full detail endpoint.

    Attributes:
        result: Tankoubon metadata, with ``full_data`` filled in.
        total: Total amount of archives in this Tankoubon.
        filtered: Amount of archives in the current page.
    """

    result: TankoubonMetadata = Field(...)
    total: int | None = Field(default=None)
    filtered: int | None = Field(default=None)


class TankoubonAPI(BaseAPICall):
    """Endpoints related to Tankoubons.

    Shared request and error behavior is documented on ``BaseAPICall``.
    """

    def get_tankoubon_list(self, page: int | None = None) -> TankoubonListResponse:
        """Get list of Tankoubons paginated.

        The amount of tanks per page depends on the server
        ``archives_per_page`` setting.

        Args:
            page: Page of the list of Tankoubons. Defaults to None.

        Returns:
            TankoubonListResponse: Tankoubons of the requested page.

        Raises:
            APIHttpError: Any non-2xx status code returned by the server.
            APIResponseDecodeError: If the response has no ``result`` list, or
                if an item does not match ``TankoubonMetadata``.
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
        """Return only the tankoubon list of the paginated list endpoint.

        This is a backward-compatible wrapper around ``get_tankoubon_list``.

        Args:
            page: Page of the list of Tankoubons. Defaults to None.

        Returns:
            list[TankoubonMetadata]: Tankoubons of the requested page.
        """
        return self.get_tankoubon_list(page=page).result

    def get_tankoubon_detail(
        self,
        id: str,
    ) -> TankoubonMetadata:
        """Get the details of the specified tankoubon ID.

        Args:
            id: ID of the Tankoubon desired.

        Returns:
            TankoubonMetadata: Metadata of the tankoubon.

        Raises:
            APIHttpError: 400 if the server rejected the request, or any other
                non-2xx status code.
            APIResponseDecodeError: If the response does not match
                ``TankoubonMetadata``.
        """
        path = f"/api/tankoubons/{id}"
        payload = self.request_json("GET", path)
        return self.parse_model(TankoubonMetadata, payload, path)

    def get_tankoubon_full(
        self,
        id: str,
        page: int = -1,
    ) -> TankoubonDetailResponse:
        """Get the details of a tankoubon with paginated archive metadata.

        The amount of archives per page depends on the server
        ``archives_per_page`` setting.

        Args:
            id: ID of the Tankoubon desired.
            page: Page of the Archives list. Defaults to -1, which returns all
                archives.

        Returns:
            TankoubonDetailResponse: Tankoubon metadata with ``full_data``
                filled in.

        Raises:
            APIHttpError: 400 if the server rejected the request, or any other
                non-2xx status code.
            APIResponseDecodeError: If the response has no ``result`` payload,
                or if it does not match ``TankoubonMetadata``.
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
        """Get the details of the specified tankoubon ID.

        This is a backward-compatible wrapper around ``get_tankoubon_detail``.

        Args:
            id: ID of the Tankoubon desired.

        Returns:
            TankoubonMetadata: Metadata of the tankoubon.
        """
        return self.get_tankoubon_detail(id=id)

    def get_tankoubon_thumbnail(
        self,
        id: str,
        no_fallback: bool | None = None,
    ) -> Response:
        """Get the cover thumbnail for a given Tankoubon.

        By default, the thumbnail is sourced from the first page of the first
        archive. This endpoint returns a placeholder image if the thumbnail
        does not exist yet. If you want to queue generation of the thumbnail in
        the background, you can use the ``no_fallback`` query parameter.

        Args:
            id: ID of the Tankoubon desired.
            no_fallback: Disables the placeholder image, queues the thumbnail
                for extraction and returns a JSON with code 202. This parameter
                does nothing if the image already exists. Defaults to None.

        Returns:
            Response: Response of the server, either the thumbnail bytes with
                code 200 or the job JSON with code 202.

        Raises:
            APIHttpError: 400 if the server rejected the request, or any other
                non-2xx status code.

        Note:
            When the thumbnail already exists, the image is returned with code
            200 no matter what. Otherwise, ``no_fallback`` queues the
            extraction and the 202 body carries a Minion job; use
            ``/api/minion/:jobid`` to track when the thumbnail is ready.
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
        """Set the cover thumbnail of a Tankoubon from a global page number.

        The global page falls within all archives of the tank, in order, and is
        translated to the correct archive and local page automatically.

        Args:
            id: ID of the Tankoubon desired.
            page: Global 1-indexed page number across all archives in the
                tankoubon. Page 1 is the first page of the first archive, and so
                on.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            On success the server also returns a ``new_thumbnail`` field with
            the path of the new thumbnail file.
        """
        return self.request_operation(
            "PUT",
            f"/api/tankoubons/{id}/thumbnail",
            params={"page": page},
        )

    def update_tank_progress(self, id: str, page: int) -> OperationResponse:
        """Tell the server which page of this Tankoubon you're reading.

        The server updates its internal reading progression accordingly. The
        page number is global across all Archives in the tank (if a tank has
        two Archives with 20 and 25 pages, page 26 will be page 6 in Archive
        #2).

        Args:
            id: ID of the Tankoubon to update.
            page: Global 1-indexed page number to update the reading progress
                to. Must be a positive integer.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            If the server is configured to use clientside progress tracking,
            this API call returns an error. Make sure to check through
            ``/api/info`` whether the server tracks reading progression or not
            before calling this endpoint.
        """
        return self.request_operation("PUT", f"/api/tankoubons/{id}/progress/{page}")

    def create_tankoubon(
        self, name: str, tankid: str | None = None
    ) -> OperationResponse:
        """Create a new Tankoubon or update the name of an existing one.

        Args:
            name: Name of the Tankoubon.
            tankid: ID of an existing Tankoubon, if you want to change its
                name. Defaults to None, which creates a new Tankoubon.

        Returns:
            OperationResponse: Result of the operation; ``tankoubon_id`` holds
                the ID of the created or modified Tankoubon.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.
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
        """Modify the full metadata (name, summary, additional tags) or the
        contents of a Tankoubon.

        If you only need to change the name of a Tank, consider just using
        ``PUT /api/tankoubons`` instead.

        Args:
            id: ID of the Tankoubon to update.
            archives: Ordered list of archive IDs. Defaults to None.
            name: Name of the Tankoubon. Defaults to None.
            summary: Summary of the Tankoubon. Defaults to None.
            tags: Additional tags for the Tankoubon, in LRR comma-separated
                format. This replaces whatever additional tags the Tank already
                has, unless ``append`` is True. Defaults to None.
            append: If True, tags are appended to the Tank's existing own tags
                instead of replacing them. Defaults to None, which leaves the
                server default of False.
            metadata: Metadata payload, merged with the explicit arguments.
                Defaults to None.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            If there is no need to update something in one of the metadata
            keys, do not send the key, as this can otherwise result in unwanted
            results.
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
        """Append an archive at the final position of a Tankoubon.

        Args:
            tankoubon_id: ID of the Tankoubon to update.
            archive_id: ID of the Archive to append.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            Failure responses such as 400 (error response) or 423 (Tankoubon
            locked for modification) are returned in the operation result, with
            ``success`` set to 0, instead of raising.
        """
        return self.request_operation(
            "PUT", f"/api/tankoubons/{tankoubon_id}/{archive_id}"
        )

    def remove_archive_from_tankoubon(
        self, tankoubon_id: str, archive_id: str
    ) -> OperationResponse:
        """Remove an archive from a Tankoubon.

        Args:
            tankoubon_id: ID of the Tankoubon to update.
            archive_id: ID of the archive to remove.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            Failure responses such as 400 (error response) or 423 (Tankoubon
            locked for modification) are returned in the operation result, with
            ``success`` set to 0, instead of raising.
        """
        return self.request_operation(
            "DELETE", f"/api/tankoubons/{tankoubon_id}/{archive_id}"
        )

    def delete_tankoubon(self, id: str) -> OperationResponse:
        """Remove a Tankoubon from the server.

        This doesn't delete the underlying Archives.

        Args:
            id: ID of the Tankoubon to delete.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            Failure responses such as 400 (error response) or 423 (Tankoubon
            locked for modification) are returned in the operation result, with
            ``success`` set to 0, instead of raising.
        """
        return self.request_operation("DELETE", f"/api/tankoubons/{id}")
