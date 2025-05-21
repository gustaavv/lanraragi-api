import requests
from pydantic import BaseModel
from script_house.utils import JsonUtils

from lanraragi_api.base.archive import Archive
from lanraragi_api.base.base import BaseAPICall


class SearchResult(BaseModel):
    data: list[Archive]
    draw: int
    recordsFiltered: int
    recordsTotal: int


class SearchAPI(BaseAPICall):
    """
    Perform searches.
    """

    def search(self,
               category: str = None,
               filter: str = None,
               start: str = None,
               sort_by: str = 'title',
               order: str = 'asc',
               new_only: bool = False,
               untagged_only: bool = False,
               groupby_tanks: bool = True,
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
        :param sort_by: Namespace by which you want to sort the results. There
        are specific sort keys you can use: (1) title if you want to sort by
        title; (2) lastread if you want to sort by last read time. (If
        Server-side Progress Tracking is enabled) (Default value is title. If
        you sort by lastread, IDs that have never been read will be removed
        from the search.)
        :param order: Order of the sort, either asc or desc. default is asc
        :param new_only: Limit search to new archives only.
        :param untagged_only: Limit search to untagged archives only.
        :param groupby_tanks: Enable or disable Tankoubon grouping. Defaults to
        true. When enabled, Tankoubons will show in search results, replacing
        all the archive IDs they contain.
        :return: SearchResult
        """

        resp = requests.get(f"{self.server}/api/search",
                            params=self.build_params({'category': category,
                                                      'filter': filter,
                                                      'start': start,
                                                      'sortby': sort_by,
                                                      'order': order,
                                                      'newonly': new_only if new_only else None,
                                                      'untaggedonly': untagged_only if untagged_only else None,
                                                      'groupby_tanks': groupby_tanks if groupby_tanks else None,
                                                      }),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, SearchResult)

    def get_random_archives(self,
                            category: str = None,
                            filter: str = None,
                            count: int = 5,
                            new_only: bool = False,
                            untagged_only: bool = False,
                            groupby_tanks: bool = True,
                            ) -> list[Archive]:
        """
        Get randomly selected Archives from the given filter and/or category.
        :param category: ID of the category you want to restrict this search to.
        :param filter: Search query. You can use special characters. See the doc.
        :param count: How many archives you want to pull randomly. Defaults to 5.
                If the search doesn't return enough data to match your count,
                you will get the full search shuffled randomly.
        :param new_only: Limit search to new archives only.
        :param untagged_only: Limit search to untagged archives only.
        :param groupby_tanks: Enable or disable Tankoubon grouping. Defaults to
        true. When enabled, Tankoubons will show in search results, replacing
        all the archive IDs they contain.
        :return: randomly selected Archives
        """

        resp = requests.get(f"{self.server}/api/search/random",
                            params=self.build_params({'category': category,
                                                      'filter': filter,
                                                      'count': count,
                                                      'newonly': new_only if new_only else None,
                                                      'untaggedonly': untagged_only if untagged_only else None,
                                                      'groupby_tanks': groupby_tanks if groupby_tanks else None,
                                                      }),
                            headers=self.build_headers())
        list = JsonUtils.to_obj(resp.text)['data']
        return [JsonUtils.to_obj(JsonUtils.to_str(o), Archive) for o in list]

    def discard_search_cache(self) -> dict:
        """
        Discard the cache containing previous user searches.
        :return: operation result
        """
        resp = requests.delete(f"{self.server}/api/search/cache", params=self.build_params(),
                               headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)
