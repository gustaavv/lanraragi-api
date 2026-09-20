from pydantic import BaseModel, Field

from lanraragi_api.entity.archive import ArchiveMetadata


class SearchResult(BaseModel):
    """Result of a search returning archive metadata.

    Attributes:
        data: Archive metadata objects for each search result.
        draw: Draw counter sent back by the server for paged searches, if any.
            Defaults to None.
        recordsFiltered: Amount of archives in the search result. Defaults to
            None.
        recordsTotal: Total number of archives available. This result changes
            depending on the ``groupby_tanks`` parameter. Defaults to None.
    """

    data: list[ArchiveMetadata] = Field(...)
    draw: int | None = Field(default=None)
    recordsFiltered: int | None = Field(default=None)
    recordsTotal: int | None = Field(default=None)


class SearchIdsResult(BaseModel):
    """Result of a search returning only archive IDs.

    Attributes:
        data: Archive IDs for each search result.
        recordsFiltered: Amount of archives in the search result. Defaults to
            None.
        recordsTotal: Total number of archives available. This result changes
            depending on the ``groupby_tanks`` parameter. Defaults to None.
    """

    data: list[str] = Field(...)
    recordsFiltered: int | None = Field(default=None)
    recordsTotal: int | None = Field(default=None)
