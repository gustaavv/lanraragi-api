from pydantic import BaseModel, Field

from lanraragi_api.base.archive import ArchiveMetadata
from lanraragi_api.base.base import (
    APIResponseDecodeError,
    BaseAPICall,
    OperationResponse,
)


class SearchResult(BaseModel):
    data: list[ArchiveMetadata] = Field(...)
    draw: int | None = Field(default=None)
    recordsFiltered: int | None = Field(default=None)
    recordsTotal: int | None = Field(default=None)


class SearchAPI(BaseAPICall):
    """
    Perform searches.
    """

    def search_archives(
        self,
        category: str | None = None,
        filter: str | None = None,
        start: int | None = None,
        sortby: str | None = None,
        order: str | None = None,
        newonly: bool | None = None,
        untaggedonly: bool | None = None,
        hidecompleted: bool | None = None,
        groupby_tanks: bool | None = None,
    ) -> SearchResult:
        """
        Search for Archives. You can use the IDs of this JSON with the other
        endpoints.

        :param category: ID of the category you want to restrict this search to.
        :param filter: Search query. You can use special characters. See the doc.
        :param start: From which archive in the total result count this
                enumeration should start. The total number of archives displayed
                depends on the server-side page size preference. you can use "-1"
                here to get the full, unpaged data.
        :param sortby: Namespace by which you want to sort the results. There
        are specific sort keys you can use: (1) title if you want to sort by
        title; (2) lastread if you want to sort by last read time. (If
        Server-side Progress Tracking is enabled) (Default value is title. If
        you sort by lastread, IDs that have never been read will be removed
        from the search.)
        :param order: Order of the sort, either asc or desc. default is asc
        :param newonly: Limit search to new archives only.
        :param untaggedonly: Limit search to untagged archives only.
        :param hidecompleted: Hide archives with completed progress
        (client-specific compatibility parameter, not defined in OpenAPI).
        :param groupby_tanks: Enable or disable Tankoubon grouping. Defaults to
        true. When enabled, Tankoubons will show in search results, replacing
        all the archive IDs they contain.
        :return: SearchResult
        """

        return self.request_model(
            "GET",
            "/api/search",
            SearchResult,
            params={
                "category": category,
                "filter": filter,
                "start": start,
                "sortby": sortby,
                "order": order,
                "newonly": newonly,
                "untaggedonly": untaggedonly,
                "hidecompleted": hidecompleted,
                "groupby_tanks": groupby_tanks,
            },
        )

    def search(
        self,
        category: str = None,
        filter: str = None,
        start: int = None,
        sort_by: str = "title",
        order: str = "asc",
        new_only: bool = False,
        untagged_only: bool = False,
        hide_completed: bool | None = None,
        groupby_tanks: bool = True,
    ) -> SearchResult:
        """
        Backward-compatible wrapper for search_archives.
        """
        return self.search_archives(
            category=category,
            filter=filter,
            start=start,
            sortby=sort_by,
            order=order,
            newonly=new_only if new_only else None,
            untaggedonly=untagged_only if untagged_only else None,
            hidecompleted=hide_completed if hide_completed else None,
            groupby_tanks=groupby_tanks if groupby_tanks else None,
        )

    def get_random_archives(
        self,
        category: str = None,
        filter: str = None,
        count: int = 5,
        new_only: bool = False,
        untagged_only: bool = False,
        hide_completed: bool | None = None,
        groupby_tanks: bool = True,
    ) -> list[ArchiveMetadata]:
        """
        Get randomly selected Archives from the given filter and/or category.
        :param category: ID of the category you want to restrict this search to.
        :param filter: Search query. You can use special characters. See the doc.
        :param count: How many archives you want to pull randomly. Defaults to 5.
                If the search doesn't return enough data to match your count,
                you will get the full search shuffled randomly.
        :param new_only: Limit search to new archives only.
        :param untagged_only: Limit search to untagged archives only.
        :param hide_completed: Hide archives with completed progress
        (client-specific compatibility parameter, not defined in OpenAPI).
        :param groupby_tanks: Enable or disable Tankoubon grouping. Defaults to
        true. When enabled, Tankoubons will show in search results, replacing
        all the archive IDs they contain.
        :return: randomly selected Archives
        """

        path = "/api/search/random"
        payload = self.request_json(
            "GET",
            path,
            params={
                "category": category,
                "filter": filter,
                "count": count,
                "newonly": new_only if new_only else None,
                "untaggedonly": untagged_only if untagged_only else None,
                "hidecompleted": hide_completed if hide_completed else None,
                "groupby_tanks": groupby_tanks if groupby_tanks else None,
            },
        )
        data = payload.get("data")
        if not isinstance(data, list):
            raise APIResponseDecodeError(self._to_url(path), "missing data list")
        return [self.parse_model(ArchiveMetadata, a, path) for a in data]

    def discard_search_cache(self) -> OperationResponse:
        """
        Discard the cache containing previous user searches.
        :return: operation result
        """
        return self.request_operation("DELETE", "/api/search/cache")
