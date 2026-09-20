from pydantic import BaseModel, Field


class CategoryMetadata(BaseModel):
    """Metadata of a single Category.

    Attributes:
        archives: IDs of the archives of a static category, empty for a dynamic
            category.
        id: ID of the category.
        name: Name of the category.
        pinned: Whether this category should be pinned in the UI.
        search: Search filter of a dynamic category, empty for a static
            category.
    """

    archives: list[str] = Field(...)
    id: str = Field(...)
    name: str = Field(...)
    pinned: int | str | None = Field(default=None)
    search: str | None = Field(default=None)
