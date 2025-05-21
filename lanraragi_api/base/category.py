from typing import Optional

import requests
from pydantic import BaseModel
from script_house.utils import JsonUtils

from lanraragi_api.base.base import BaseAPICall


class Category(BaseModel):
    archives: list[str]
    id: str
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
        resp = requests.get(f"{self.server}/api/categories", params=self.build_params(),
                            headers=self.build_headers())
        list = JsonUtils.to_obj(resp.text)
        return [JsonUtils.to_obj(JsonUtils.to_str(o), Category) for o in list]

    def get_category(self, id: str) -> Optional[Category]:
        """
        Get the details of the specified category ID.
        :param id: ID of the Category desired.
        :return: category
        """
        resp = requests.get(f"{self.server}/api/categories/{id}", params=self.build_params(),
                            headers=self.build_headers())
        if resp.status_code == 400:
            return None
        return JsonUtils.to_obj(resp.text, Category)

    def create_category(self, name: str, search: str = None, pinned: bool = None):
        """
        Create a new Category.

        :param name: Name of the Category.
        :param search: Matching predicate, if creating a Dynamic Category.
        :param pinned: whether the created category will  be pinned.
        :return: operation result
        """
        resp = requests.put(f"{self.server}/api/categories",
                            params=self.build_params({
                                'name': name,
                                'search': search,
                                'pinned': pinned if pinned else None,
                            }),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def update_category(self, id: str, name: str = None, search: str = None, pinned: bool = None):
        """
        Modify a Category.
        :param id: ID of the Category to update.
        :param name: New name of the Category
        :param search: Predicate. Trying to add a predicate to a category that
        already contains Archives will give you an error.
        :param pinned: Add this argument to pin the Category. If you don't, the
        category will be unpinned on update.
        :return: operation result
        """
        resp = requests.put(f"{self.server}/api/categories/{id}",
                            params=self.build_params({
                                'name': name,
                                'search': search,
                                'pinned': pinned if pinned else None,
                            }),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def delete_category(self, id: str) -> dict:
        """
        Remove a Category.
        :param id: Category ID
        :return: operation result
        """
        resp = requests.delete(f"{self.server}/api/categories/{id}",
                               params=self.build_params(), headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def add_archive_to_category(self, category_id: str, archive_id: str):
        """
        Adds the specified Archive ID (see Archive API) to the given Category.
        :param category_id: Category ID to add the Archive to.
        :param archive_id: Archive ID to add.
        :return: operation result
        """
        resp = requests.put(f"{self.server}/api/categories/{category_id}/{archive_id}",
                            params=self.build_params(), headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def remove_archive_from_category(self, category_id: str, archive_id: str) -> dict:
        """
        Remove an Archive ID from a Category.
        :param category_id: Category ID
        :param archive_id: Archive ID
        :return: operation result
        """
        resp = requests.delete(f"{self.server}/api/categories/{category_id}/{archive_id}",
                               params=self.build_params(), headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def get_bookmark_link(self) -> dict:
        """
        Retrieves the ID of the category currently linked to the bookmark
        feature. Returns an empty string if no category is linked.
        :return: operation result
        """
        resp = requests.get(f"{self.server}/api/categories/bookmark_link",
                            params=self.build_params(), headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def update_bookmark_link(self, id: str) -> dict:
        """
        Links the bookmark feature to the specified static category. This
        determines which category archives are added to when using the bookmark
        button.
        :param id: ID of the static category to link with the bookmark feature.
        :return: operation result
        """
        resp = requests.put(f"{self.server}/api/categories/bookmark_link/{id}",
                            params=self.build_params(), headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)

    def disable_bookmark_feature(self):
        """
        Disables the bookmark feature by removing the link to any category.
        Returns the ID of the previously linked category.
        :return: operation result
        """
        resp = requests.delete(f"{self.server}/api/categories/bookmark_link",
                               params=self.build_params(), headers=self.build_headers())
        return JsonUtils.to_obj(resp.text)
