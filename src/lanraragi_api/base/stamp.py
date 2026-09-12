from pydantic import BaseModel, Field

from lanraragi_api.base.base import (
    APIResponseDecodeError,
    BaseAPICall,
    DictLikeModel,
    OperationResponse,
)


class StampsData(BaseModel):
    """JSON object for the Stamp model.

    Attributes:
        id: ID of the stamp.
        position: Position of the stamp in the page in normalized coordinates
            (0-100).
        content: Text of the stamp.
    """

    id: str | None = Field(default=None)
    position: str = Field(...)
    content: str = Field(...)


class StampsResponse(DictLikeModel):
    """Response listing the pages that contain at least one stamp.

    Attributes:
        result: Page indices of the archive that contain a stamp.
    """

    result: list[str] = Field(default_factory=list)


class AddStampResponse(OperationResponse):
    """Result of the operation that adds a stamp to a page.

    Attributes:
        stamp_id: ID of the created stamp.
    """

    stamp_id: str | None = Field(default=None)


class StampAPI(BaseAPICall):
    """Stamps.

    Shared request and error behavior is documented on ``BaseAPICall``.
    """

    def get_stamped_pages(self, archive_id: str) -> StampsResponse:
        """Get pages that contain at least one stamp in the archive.

        Args:
            archive_id: ID of the archive.

        Returns:
            StampsResponse: Page indices of the archive that contain a stamp.

        Raises:
            APIHttpError: 400 if the server rejected the request.
            APIResponseDecodeError: If the response does not match
                ``StampsResponse``.
        """
        return self.request_model(
            "GET", f"/api/archives/{archive_id}/stamps", StampsResponse
        )

    def get_stamps_by_page(self, archive_id: str, index: int) -> list[StampsData]:
        """Get the stamps linked to the page.

        Args:
            archive_id: ID of the archive.
            index: Page of the archive.

        Returns:
            list[StampsData]: Stamps of the page.

        Raises:
            APIHttpError: 400 if the server rejected the request.
            APIResponseDecodeError: If the response has no ``result`` list, or
                if an item does not match ``StampsData``.
        """
        path = f"/api/archives/{archive_id}/stamps/{index}"
        payload = self.request_json("GET", path)
        result = payload.get("result")
        if not isinstance(result, list):
            raise APIResponseDecodeError(self._to_url(path), "missing result list")
        return [self.parse_model(StampsData, item, path) for item in result]

    def add_stamp(
        self,
        archive_id: str,
        index: int,
        content: str | None = None,
        position: str | None = None,
    ) -> AddStampResponse:
        """Add a new Stamp to the page at the given coordinates.

        Args:
            archive_id: ID of the archive.
            index: Page of the archive.
            content: Text of the stamp. Defaults to None.
            position: Position of the stamp in the page. Defaults to None.

        Returns:
            AddStampResponse: Result of the operation, with the ``stamp_id`` of
                the created stamp.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``AddStampResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            A 400 response is returned in the operation result, with ``success``
            set to 0, instead of raising.
        """
        return self.request_operation(
            "PUT",
            f"/api/archives/{archive_id}/stamps/{index}",
            model=AddStampResponse,
            params={"content": content, "position": position},
        )

    def get_stamp(self, id: str) -> StampsData:
        """Get a stamp from an Archive.

        Args:
            id: ID of the stamp.

        Returns:
            StampsData: Stamp data.

        Raises:
            APIHttpError: 400 if the server rejected the request; 423 if the
                Stamp is currently locked for modification.
            APIResponseDecodeError: If the response does not match
                ``StampsData``.
        """
        path = f"/api/stamps/{id}"
        return self.request_model("GET", path, StampsData)

    def update_stamp(
        self,
        id: str,
        content: str | None = None,
        position: str | None = None,
    ) -> OperationResponse:
        """Update a stamp from an Archive.

        Args:
            id: ID of the stamp.
            content: Text of the stamp. Defaults to None.
            position: Position of the stamp in the page. Defaults to None.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            Failure responses such as 400 (error response) or 423 (Stamp locked
            for modification) are returned in the operation result, with
            ``success`` set to 0, instead of raising.
        """
        return self.request_operation(
            "PUT",
            f"/api/stamps/{id}",
            params={"content": content, "position": position},
        )

    def delete_stamp(self, id: str) -> OperationResponse:
        """Remove a stamp from an Archive.

        Args:
            id: ID of the stamp.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            Failure responses such as 400 (error response) or 423 (Stamp locked
            for modification) are returned in the operation result, with
            ``success`` set to 0, instead of raising.
        """
        return self.request_operation("DELETE", f"/api/stamps/{id}")
