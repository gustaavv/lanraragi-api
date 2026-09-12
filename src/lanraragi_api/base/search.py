from pydantic import BaseModel, Field

from lanraragi_api.base.archive import ArchiveMetadata
from lanraragi_api.base.base import (
    APIResponseDecodeError,
    BaseAPICall,
    OperationResponse,
)


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


class SearchAPI(BaseAPICall):
    """Perform searches.

    Shared request and error behavior is documented on ``BaseAPICall``.
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
        """Search for Archives.

        You can use the IDs of this JSON with the other endpoints.

        The ``filter`` parameter accepts the following special characters:

        - Quotation marks (``"..."``): exact string search. Allows a search
          term to include spaces, as everything inside a pair of quotation
          marks is treated as a singular term. Wildcard characters are still
          interpreted as wildcards.
        - Question mark (``?``), underscore (``_``): wildcard matching any
          single character.
        - Asterisk (``*``), percentage sign (``%``): wildcard matching any
          sequence of characters, including none.
        - Subtraction sign (``-``): exclusion. When placed before a term, it
          prevents search results from including that term.
        - Dollar sign (``$``): add at the end of a tag to perform an exact tag
          search rather than displaying all elements that start with the term.
          Only matches tags regardless of the search parameters, and can be
          used as an exclusion to ignore misc tags in the search query.

        Args:
            category: ID of the category you want to restrict this search to.
                Defaults to None.
            filter: Search query, using the special characters listed above.
                Defaults to None.
            start: From which archive in the total result count this
                enumeration should start. The total number of archives
                displayed depends on the server-side page size preference.
                From 0.8.2 onwards, "-1" gives the full, unpaged data. Defaults
                to None.
            sortby: Namespace by which you want to sort the results. Use
                ``title`` to sort by title, or ``lastread`` to sort by last
                read time, which requires Server-side Progress Tracking to be
                enabled. Defaults to None, which sorts by title; sorting by
                ``lastread`` removes IDs that have never been read from the
                search.
            order: Order of the sort, either ``asc`` or ``desc``. Defaults to
                None, which the server treats as ``asc``.
            newonly: Limit search to new archives only. Defaults to None.
            untaggedonly: Limit search to untagged archives only. Defaults to
                None.
            hidecompleted: Hide archives where reading progress has reached the
                end. Defaults to None.
            groupby_tanks: Enable or disable Tankoubon grouping. When enabled,
                Tankoubons show in search results, replacing all the archive
                IDs they contain. Defaults to None, which the server treats as
                true.

        Returns:
            SearchResult: One ``ArchiveMetadata`` object per matching archive
                in ``data``.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``SearchResult``.

        Note:
            The server answers with ``204`` when the search engine is not
            initialized yet. That response carries no body and therefore raises
            ``APIResponseDecodeError``; wait a few seconds and retry the search
            in that case.
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
        category: str | None = None,
        filter: str | None = None,
        start: int | None = None,
        sort_by: str = "title",
        order: str = "asc",
        new_only: bool = False,
        untagged_only: bool = False,
        hide_completed: bool | None = None,
        groupby_tanks: bool = True,
    ) -> SearchResult:
        """Search for Archives using the legacy parameter names.

        This compatibility wrapper forwards every argument to
        ``search_archives``, renaming ``sort_by`` to ``sortby``, ``new_only``
        to ``newonly``, ``untagged_only`` to ``untaggedonly`` and
        ``hide_completed`` to ``hidecompleted``. ``groupby_tanks`` keeps its
        name.

        Args:
            category: ID of the category you want to restrict this search to.
                Defaults to None.
            filter: Search query, following the rules of ``search_archives``.
                Defaults to None.
            start: From which archive in the total result count this
                enumeration should start, with "-1" for the full, unpaged
                data. Defaults to None.
            sort_by: Namespace by which you want to sort the results, sent as
                ``sortby``. Defaults to "title".
            order: Order of the sort, either ``asc`` or ``desc``, sent as
                ``order``. Defaults to "asc".
            new_only: Limit search to new archives only, sent as ``newonly``.
                Defaults to False.
            untagged_only: Limit search to untagged archives only, sent as
                ``untaggedonly``. Defaults to False.
            hide_completed: Hide archives where reading progress has reached
                the end, sent as ``hidecompleted``. Defaults to None.
            groupby_tanks: Enable or disable Tankoubon grouping. Defaults to
                True.

        Returns:
            SearchResult: Same result as ``search_archives``.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``SearchResult``.

        Note:
            Falsy values are not forwarded to the server: ``new_only``,
            ``untagged_only``, ``hide_completed`` and ``groupby_tanks`` become
            ``None``, so the server-side default applies instead.
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

    def search_archive_ids(
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
    ) -> SearchIdsResult:
        """Search for Archives like ``/api/search``, but return only IDs.

        The ordered list of matching Archive IDs is returned without the
        accompanying metadata.

        Args:
            category: ID of the category you want to restrict this search to.
                Defaults to None.
            filter: Search query, following the same rules as the queries in
                ``/api/search``. Defaults to None.
            start: From which archive in the total result count this
                enumeration should start. The total number of archives
                displayed depends on the server-side page size preference.
                From 0.8.2 onwards, "-1" gives the full, unpaged list of IDs.
                Defaults to None.
            sortby: Namespace by which you want to sort the results. Use
                ``title`` to sort by title, or ``lastread`` to sort by last
                read time, which requires Server-side Progress Tracking to be
                enabled. Defaults to None, which sorts by title; sorting by
                ``lastread`` removes IDs that have never been read from the
                search.
            order: Order of the sort, either ``asc`` or ``desc``. Defaults to
                None, which the server treats as ``asc``.
            newonly: Limit search to new archives only. Defaults to None.
            untaggedonly: Limit search to untagged archives only. Defaults to
                None.
            hidecompleted: Hide archives where reading progress has reached the
                end. Defaults to None.
            groupby_tanks: Enable or disable Tankoubon grouping. When enabled,
                Tankoubons show in search results, replacing all the archive
                IDs they contain. Defaults to None, which the server treats as
                true.

        Returns:
            SearchIdsResult: One archive ID per matching archive in ``data``.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``SearchIdsResult``.

        Note:
            The server answers with ``204`` when the search engine is not
            initialized yet. That response carries no body and therefore raises
            ``APIResponseDecodeError``; wait a few seconds and retry the search
            in that case.
        """
        return self.request_model(
            "GET",
            "/api/search/ids",
            SearchIdsResult,
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

    def get_random_archives(
        self,
        category: str | None = None,
        filter: str | None = None,
        count: int = 5,
        new_only: bool = False,
        untagged_only: bool = False,
        hide_completed: bool | None = None,
        groupby_tanks: bool = True,
    ) -> list[ArchiveMetadata]:
        """Get randomly selected Archives from the given filter and/or category.

        Args:
            category: ID of the category you want to restrict this search to.
                Defaults to None.
            filter: Search query, following the same rules as the queries in
                ``/api/search``. Defaults to None.
            count: How many archives you want to pull randomly. If the search
                doesn't return enough data to match your count, you will get
                the full search shuffled randomly. Defaults to 5.
            new_only: Limit search to new archives only. Defaults to False,
                which is not sent to the server.
            untagged_only: Limit search to untagged archives only. Defaults to
                False, which is not sent to the server.
            hide_completed: Hide archives where reading progress has reached
                the end. Defaults to None.
            groupby_tanks: Enable or disable Tankoubon grouping. When enabled,
                Tankoubons show in search results, replacing all the archive
                IDs they contain. Defaults to True; a falsy value is not sent
                to the server.

        Returns:
            list[ArchiveMetadata]: Randomly selected archives, one object per
                archive.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the response body is not valid JSON, if
                it has no ``data`` list, or if an item of that list does not
                match ``ArchiveMetadata``.
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
        """Discard the cache containing previous user searches.

        Returns:
            OperationResponse: Result of the cache discard operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            A 400 response is returned in the operation result, with ``success``
            set to 0, instead of raising.
        """
        return self.request_operation("DELETE", "/api/search/cache")
