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
               category: str = "",
               filter: str = "",
               start: str = "0",
               sort_by: str = "title",
               order: str = 'asc') -> SearchResult:
        """
        Search for Archives. You can use the IDs of this JSON with the other endpoints.


        :param category: ID of the category you want to restrict this search to.
        :param filter: Search query. You can use special characters. See the doc.
        :param start: From which archive in the total result count this
                enumeration should start. The total number of archives displayed
                depends on the server-side page size preference. you can use "-1"
                here to get the full, unpaged data.
        :param sort_by: Namespace by which you want to sort the results, or title
                if you want to sort by title. (Default value is title.)
        :param order: Order of the sort, either asc or desc. default is asc
        :return: SearchResult
        """
        params = {
            'key': self.key,
            'category': category,
            'filter': filter,
            'start': start,
            'sortby': sort_by,
            'order': order
        }

        resp = requests.get(f"{self.server}/api/search", params=params,
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, SearchResult)

    def get_random_archives(self,
                            category: str = "",
                            filter: str = "",
                            count: int = 5) -> list[Archive]:
        """
        Get randomly selected Archives from the given filter and/or category.
        :param category: ID of the category you want to restrict this search to.
        :param filter: Search query. You can use special characters. See the doc.
        :param count: How many archives you want to pull randomly. Defaults to 5.
                If the search doesn't return enough data to match your count,
                you will get the full search shuffled randomly.
        :return: randomly selected Archives
        """
        params = {
            'key': self.key,
            'category': category,
            'filter': filter,
            'count': count
        }
        resp = requests.get(f"{self.server}/api/search/random", params=params,
                            headers=self.build_headers())
        list = JsonUtils.to_obj(resp.text)['data']
        return [JsonUtils.to_obj(JsonUtils.to_str(o), Archive) for o in list]

    def discard_search_cache(self) -> dict:
        """
        Discard the cache containing previous user searches.
        :return: operation result
        """
        # TODO: untested
        resp = requests.delete(f"{self.server}/api/search/cache", params={'key': self.key},
                               headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)
