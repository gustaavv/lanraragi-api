from pydantic import AliasChoices, BaseModel, Field

from lanraragi_api.entity.archive import ArchiveMetadata
from lanraragi_api.entity.base import DictLikeModel


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
