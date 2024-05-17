import requests
from pydantic import BaseModel
from script_house.utils import JsonUtils

from lanraragi_api.base.base import BaseAPICall


class Category(BaseModel):
    archives: list[str]
    id: str
    last_used: str
    name: str
    pinned: str
    search: str


class CategoryAPI(BaseAPICall):
    """
    Everything dealing with Categories.
    """

    def get_all_categories(self) -> list[Category]:
        """
        Get all the categories saved on the server.
        :return:  list of categories
        """
        resp = requests.get(f"{self.server}/api/categories", params={'key': self.key},
                            headers=self.build_headers())
        list = JsonUtils.to_obj(resp.text)
        return [JsonUtils.to_obj(JsonUtils.to_str(o), Category) for o in list]

    def get_category(self, id: str) -> Category:
        """
        Get the details of the specified category ID.
        :param id: ID of the Category desired.
        :return:
        """
        resp = requests.get(f"{self.server}/api/categories/{id}", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, Category)

    def create_category(self, name: str, search: str = None, pinned: bool = None):
        """
        Create a new Category.
        :param name: Name of the Category.
        :param search: Matching predicate, if creating a Dynamic Category.
        :param pinned: whether the created category will  be pinned.
        :return:
        """
        pass

    def update_category(self, id: str, name: str = None, search: str = None, pinned: bool = None):
        pass

    def delete_category(self, id: str):
        pass

    def add_archive_to_category(self, category_id: str, archive_id: str):
        pass

    def remove_archive_from_category(self, category_id: str, archive_id: str):
        pass
