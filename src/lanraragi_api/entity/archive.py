from typing import Any

from pydantic import BaseModel, Field

ARCHIVE_TAG_VALUES_SET = "ONLY_VALUES"


class ArchiveMetadata(BaseModel):
    """Metadata of a single Archive.

    Attributes:
        arcid: Unique identifier for the archive, a 40 character SHA1 hash.
        extension: File extension of the archive.
        filename: Filename of the archive.
        isnew: Whether the archive is newly added. Defaults to None.
        lastreadtime: Unix timestamp of when the archive was last read.
        pagecount: Total number of pages in the archive.
        progress: Reading progress, as a page number.
        size: Size of the archive in bytes.
        summary: Summary description of the archive. Defaults to None.
        toc: Table of contents for the archive, as objects holding the ``page``
            where a chapter starts and its ``name``. Defaults to None.
        tags: Comma-separated list of tags associated with the archive, with
            namespaced tags in ``namespace:value`` form.
        title: Title of the archive.
    """

    arcid: str = Field(...)
    extension: str = Field(...)
    filename: str = Field(...)
    isnew: bool | str | None = Field(default=None)
    lastreadtime: int = Field(...)
    pagecount: int = Field(...)
    progress: int = Field(...)
    size: int = Field(...)
    summary: str | None = Field(default=None)
    toc: list[dict[Any, Any]] | None = Field(default=None)

    # k1:v1, k2:v21, k2:v22, v3, v4
    # allow duplicate keys, only values
    tags: str = Field(...)
    title: str = Field(...)


class ArchiveTags:
    """Offer utility methods to operate ``ArchiveMetadata.tags``"""

    def __init__(self, tags: str):
        self._tags: str = tags

    @property
    def tags(self):
        """Get the ``tags`` string represented by this class"""
        return self._tags

    def get_tag_list(self) -> list[str]:
        """Get a list of tags"""
        tags = [t.strip() for t in self._tags.split(",")]
        tags = [t for t in tags if t != ""]
        return tags

    def set_tag(self, tag_list: list[str]):
        """Set the inner ``tags`` by a list of tags. Note that there will be
        a deduplication first.
        """
        # deduplicate first
        tag_list = list(dict.fromkeys(tag_list))
        self._tags = ",".join(tag_list)

    def get_artists(self) -> list[str]:
        """Get all artists in a list from tags prefixed with ``artist:``."""
        tag_list = self.get_tag_list()
        return [t[len("artist:") :] for t in tag_list if t.startswith("artist:")]

    def set_artists(self, artists: list[str]):
        """Set/Overwrite existing artists.

        Consider using ``append_artists`` method if you want to add some new
        artists.

        """
        tag_list = self.get_tag_list()
        tag_list = [t for t in tag_list if not t.startswith("artist:")]
        self.set_tag(tag_list)

        self.append_artists(artists)

    def append_artists(self, artists: list[str]):
        """Add some new artists to the existing ones."""
        tag_list = self.get_tag_list()
        tag_list += [f"artist:{a}" for a in artists]
        self.set_tag(tag_list)
