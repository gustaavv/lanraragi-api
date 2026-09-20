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

    def __tags_to_dict(self) -> dict[str, list[str]]:
        """Convert the ``tags`` string into a mapping of keys to values.

        The string is split on commas. Tags written as ``key:value`` are
        grouped under ``key``, allowing duplicate keys, while bare tags are
        grouped under the ``ONLY_VALUES`` key.

        Returns:
            dict[str, list[str]]: One entry per tag key, holding its values in
                order of appearance.
        """
        tags: list[str] = self.tags.split(",")
        ans: dict[str, list[str]] = {}
        for t in tags:
            if t == "":
                continue
            t = t.strip()
            if ":" in t:
                kv = t.split(":")
                k = kv[0]
                v = kv[1]
                if k not in ans:
                    ans[k] = []
                ans[k].append(v)
            else:
                k = ARCHIVE_TAG_VALUES_SET
                if k not in ans:
                    ans[k] = []
                ans[k].append(t)
        return ans

    def __dict_to_tags(self, json: dict[str, list[str]]):
        """Write a mapping of tag keys to values back into ``tags``.

        Keys other than ``ONLY_VALUES`` are written as ``key:value`` pairs,
        while values of ``ONLY_VALUES`` are written as bare tags, all joined
        with commas.

        Args:
            json: Mapping of tag keys to their values, in the shape returned
                by ``__tags_to_dict``.

        Note:
            The function will modify the object: ``self.tags`` is replaced in
            place.
        """
        tags = ""
        modified: bool = False
        for k, values in json.items():
            for v in values:
                modified = True
                if k == ARCHIVE_TAG_VALUES_SET:
                    tags += f"{v},"
                else:
                    tags += f"{k}:{v},"
        if modified:
            tags = tags[:-1]
        self.tags = tags

    def get_artists(self) -> list[str]:
        """Return the values of the ``artist`` tag.

        Returns:
            list[str]: Artist names found in ``tags``, in order of appearance.
        """
        return self.__tags_to_dict()["artist"]

    def set_artists(self, artists: list[str]):
        """Replace the ``artist`` tag with the given values.

        The ``tags`` string of the model is modified in place, and the other
        tag keys are kept.

        Args:
            artists: Artist names to store in the ``artist`` tag.
        """
        json = self.__tags_to_dict()
        json["artist"] = artists
        self.__dict_to_tags(json)

    def remove_artists(self):
        """Remove the ``artist`` tag.

        The ``tags`` string of the model is modified in place, and the other
        tag keys are kept.
        """
        json = self.__tags_to_dict()
        json["artist"] = []
        self.__dict_to_tags(json)

    def has_artists(self) -> bool:
        """Return whether the archive carries an ``artist`` tag.

        Returns:
            bool: True if the ``artist`` key appears in ``tags``.
        """
        return "artist" in self.tags
