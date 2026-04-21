from typing import Any, Optional

from pydantic import AliasChoices, BaseModel, Field

from lanraragi_api.base.archive import ArchiveMetadata
from lanraragi_api.base.base import (
    APIResponseDecodeError,
    BaseAPICall,
    DictLikeModel,
    OperationResponse,
)


class TankoubonMetadata(BaseModel):
    archives: list[str] = Field(...)
    full_data: Optional[list[ArchiveMetadata]] = Field(default=None)
    tankid: str = Field(..., validation_alias=AliasChoices("tankid", "id"))
    name: str = Field(...)
    summary: str | None = Field(default=None)
    tags: str | None = Field(default=None)

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

    @staticmethod
    def _as_bool_query(value: bool | str | None) -> bool | None:
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        return value

    def get_tankoubon_list(self, page: int = None) -> TankoubonListResponse:
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

    def get_all_tankoubons(self, page: int = None) -> list[TankoubonMetadata]:
        """
        Backward-compatible wrapper returning only the tankoubon list.
        :param page: Page of the list of Tankoubons.
        :return: list of Tankoubons
        """
        return self.get_tankoubon_list(page=page).result

    def get_tankoubon_detail(
        self,
        id: str,
        include_full_data: bool | str = None,
        page: int = None,
    ) -> TankoubonDetailResponse:
        """
        Get the details of the specified tankoubon ID, with the archives list
        paginated.
        :param id: ID of the Tankoubon desired.
        :param include_full_data: If true, appends a full_data array with Archive objects.
        :param page: Page of the Archives list.
        :return: Tankoubon detail response
        """
        path = f"/api/tankoubons/{id}"
        include_full_data_value = self._as_bool_query(include_full_data)
        payload = self.request_json(
            "GET",
            path,
            params={
                "page": page,
                "include_full_data": include_full_data_value,
            },
        )
        result = payload.get("result")
        if result is None:
            raise APIResponseDecodeError(self._to_url(path), "missing result payload")
        return TankoubonDetailResponse(
            result=self.parse_model(TankoubonMetadata, result, path),
            total=payload.get("total"),
            filtered=payload.get("filtered"),
        )

    def get_tankoubon(
        self,
        id: str,
        include_full_data: bool | str = None,
        page: int = None,
    ) -> TankoubonMetadata:
        """
        Backward-compatible wrapper returning only the tankoubon object.
        :param id: ID of the Tankoubon desired.
        :param include_full_data: If true, appends a full_data array with Archive objects.
        :param page: Page of the Archives list.
        :return: Tankoubon
        """
        return self.get_tankoubon_detail(
            id=id,
            include_full_data=include_full_data,
            page=page,
        ).result

    def create_tankoubon(self, name: str, tankid: str = None) -> OperationResponse:
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
        archives: list[str] = None,
        name: str = None,
        summary: str = None,
        tags: str = None,
        metadata: dict[str, Any] = None,
    ) -> OperationResponse:
        """
        Update Tankoubon metadata and/or contents.
        :param id: ID of the Tankoubon to update.
        :param archives: Ordered list of archive IDs.
        :param name: Optional metadata name.
        :param summary: Optional metadata summary.
        :param tags: Optional metadata tags.
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
