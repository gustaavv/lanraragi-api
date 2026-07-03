from pydantic import BaseModel, Field

from lanraragi_api.base.base import (
    APIResponseDecodeError,
    BaseAPICall,
    DictLikeModel,
    OperationResponse,
)


class StampsData(BaseModel):
    id: str | None = Field(default=None)
    position: str = Field(...)
    content: str = Field(...)


class StampsResponse(DictLikeModel):
    result: list[str] = Field(default_factory=list)


class AddStampResponse(OperationResponse):
    stamp_id: str | None = Field(default=None)


class StampAPI(BaseAPICall):
    """
    Stamp annotations API.
    """

    def get_stamped_pages(self, archive_id: str) -> StampsResponse:
        """
        Get pages that contain at least one stamp in the archive.

        :param archive_id: ID of the archive.
        :return: StampsResponse with list of page indices
        """
        return self.request_model(
            "GET", f"/api/archives/{archive_id}/stamps", StampsResponse
        )

    def get_stamps_by_page(self, archive_id: str, index: int) -> list[StampsData]:
        """
        Get the stamps linked to the page.

        :param archive_id: ID of the archive.
        :param index: Page of the archive.
        :return: list of stamps data
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
        content: str = None,
        position: str = None,
    ) -> AddStampResponse:
        """
        Add a new Stamp to the page at the given coordinates.

        :param archive_id: ID of the archive.
        :param index: Page of the archive.
        :param content: Text of the stamp.
        :param position: Position of the stamp in the page.
        :return: operation result with stamp ID
        """
        return self.request_operation(
            "PUT",
            f"/api/archives/{archive_id}/stamps/{index}",
            model=AddStampResponse,
            params={"content": content, "position": position},
        )

    def get_stamp(self, id: str) -> StampsData:
        """
        Get a stamp from an Archive.

        :param id: ID of the stamp.
        :return: stamp data
        """
        path = f"/api/stamps/{id}"
        return self.request_model("GET", path, StampsData)

    def update_stamp(
        self,
        id: str,
        content: str = None,
        position: str = None,
    ) -> OperationResponse:
        """
        Update a stamp from an Archive.

        :param id: ID of the stamp.
        :param content: Text of the stamp.
        :param position: Position of the stamp in the page.
        :return: operation result
        """
        return self.request_operation(
            "PUT",
            f"/api/stamps/{id}",
            params={"content": content, "position": position},
        )

    def delete_stamp(self, id: str) -> OperationResponse:
        """
        Remove a stamp from an Archive.

        :param id: ID of the stamp.
        :return: operation result
        """
        return self.request_operation("DELETE", f"/api/stamps/{id}")
