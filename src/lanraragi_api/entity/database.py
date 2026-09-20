from pydantic import BaseModel, Field

from lanraragi_api.entity.base import DictLikeModel


class TagStatistic(BaseModel):
    """Prevalence of a single tag in the database.

    Attributes:
        namespace: Namespace of the tag, if it has one.
        text: The tag itself.
        weight: Weight of the tag in the database.
    """

    namespace: str | None = Field(default=None)
    text: str = Field(...)
    weight: int = Field(...)


class BackupArchiveMetadata(DictLikeModel):
    """Archive metadata as returned in a database backup.

    Attributes:
        arcid: Unique identifier for the archive.
        title: Title of the archive.
        tags: Comma-separated list of tags associated with the archive.
        summary: Summary description of the archive.
        thumbhash: Thumbnail hash, or null if not set.
        filename: Filename of the archive.
    """

    arcid: str = Field(...)
    title: str = Field(...)
    tags: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    thumbhash: str | None = Field(default=None)
    filename: str = Field(...)


class BackupCategoryMetadata(DictLikeModel):
    """Category metadata as returned in a database backup.

    Attributes:
        archives: Array of archive IDs.
        catid: ID of the category.
        name: Name of the category.
        search: Category search filter.
    """

    archives: list[str] = Field(default_factory=list)
    catid: str = Field(...)
    name: str | None = Field(default=None)
    search: str | None = Field(default=None)


class BackupTankoubonMetadataJson(DictLikeModel):
    """Tankoubon metadata as returned in a database backup.

    Attributes:
        tankid: ID of the tankoubon.
        name: Name of the tankoubon.
        summary: Summary of the tankoubon.
        tags: Tags associated with the tankoubon.
        archives: Array of archive IDs.
    """

    tankid: str = Field(...)
    name: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    tags: str | None = Field(default=None)
    archives: list[str] = Field(default_factory=list)


class DatabaseBackup(DictLikeModel):
    """Full backup of the database in JSON form.

    Attributes:
        archives: Array of archive metadata.
        categories: Array of category metadata.
        tankoubons: Array of tankoubon metadata.
    """

    archives: list[BackupArchiveMetadata] = Field(default_factory=list)
    categories: list[BackupCategoryMetadata] = Field(default_factory=list)
    tankoubons: list[BackupTankoubonMetadataJson] = Field(default_factory=list)
