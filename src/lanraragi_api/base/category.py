from typing import Optional

from pydantic import BaseModel, Field

from lanraragi_api.base.base import BaseAPICall, OperationResponse


class CategoryMetadata(BaseModel):
    archives: list[str] = Field(...)
    id: str = Field(...)
    name: str = Field(...)
    pinned: int | str | None = Field(default=None)
    search: str | None = Field(default=None)


class CategoryAPI(BaseAPICall):
    """
    Everything dealing with Categories.
    """

    def get_all_categories(self) -> list[CategoryMetadata]:
        """
        Get all the categories saved on the server.
        :return:  list of categories
        """
        return self.request_model_list("GET", "/api/categories", CategoryMetadata)

    def get_category(self, id: str) -> Optional[CategoryMetadata]:
        """
        Get the details of the specified category ID.
        :param id: ID of the Category desired.
        :return: category
        """
        path = f"/api/categories/{id}"
        resp = self.request("GET", path, expected_statuses={200, 400})
        if resp.status_code == 400:
            return None
        return self.parse_model(
            CategoryMetadata, self.parse_json_response(resp, path), path
        )

    def create_category(
        self, name: str, search: str = None, pinned: bool = None
    ) -> OperationResponse:
        """
        Create a new Category.

        :param name: Name of the Category.
        :param search: Matching predicate, if creating a Dynamic Category.
        :param pinned: whether the created category will  be pinned.
        :return: operation result
        """
        return self.request_operation(
            "PUT",
            "/api/categories",
            data={
                "name": name,
                "search": search,
                "pinned": pinned,
            },
        )

    def update_category(
        self, id: str, name: str = None, search: str = None, pinned: bool = None
    ) -> OperationResponse:
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
        return self.request_operation(
            "PUT",
            f"/api/categories/{id}",
            data={
                "name": name,
                "search": search,
                "pinned": pinned,
            },
        )

    def delete_category(self, id: str) -> OperationResponse:
        """
        Remove a Category.
        :param id: Category ID
        :return: operation result
        """
        return self.request_operation("DELETE", f"/api/categories/{id}")

    def add_archive_to_category(
        self, category_id: str, archive_id: str
    ) -> OperationResponse:
        """
        Adds the specified Archive ID (see Archive API) to the given Category.
        :param category_id: Category ID to add the Archive to.
        :param archive_id: Archive ID to add.
        :return: operation result
        """
        return self.request_operation(
            "PUT", f"/api/categories/{category_id}/{archive_id}"
        )

    def remove_archive_from_category(
        self, category_id: str, archive_id: str
    ) -> OperationResponse:
        """
        Remove an Archive ID from a Category.
        :param category_id: Category ID
        :param archive_id: Archive ID
        :return: operation result
        """
        return self.request_operation(
            "DELETE", f"/api/categories/{category_id}/{archive_id}"
        )

    def get_bookmark_link(self) -> dict:
        """
        Retrieves the ID of the category currently linked to the bookmark
        feature. Returns an empty string if no category is linked.
        :return: operation result
        """
        return self.request_json("GET", "/api/categories/bookmark_link")

    def update_bookmark_link(self, id: str) -> OperationResponse:
        """
        Links the bookmark feature to the specified static category. This
        determines which category archives are added to when using the bookmark
        button.
        :param id: ID of the static category to link with the bookmark feature.
        :return: operation result
        """
        return self.request_operation("PUT", f"/api/categories/bookmark_link/{id}")

    def disable_bookmark_feature(self) -> OperationResponse:
        """
        Disables the bookmark feature by removing the link to any category.
        Returns the ID of the previously linked category.
        :return: operation result
        """
        return self.request_operation("DELETE", "/api/categories/bookmark_link")

