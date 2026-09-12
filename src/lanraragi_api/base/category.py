from pydantic import BaseModel, Field

from lanraragi_api.base.base import BaseAPICall, OperationResponse


class CategoryMetadata(BaseModel):
    """Metadata of a single Category.

    Attributes:
        archives: IDs of the archives of a static category, empty for a dynamic
            category.
        id: ID of the category.
        name: Name of the category.
        pinned: Whether this category should be pinned in the UI.
        search: Search filter of a dynamic category, empty for a static
            category.
    """

    archives: list[str] = Field(...)
    id: str = Field(...)
    name: str = Field(...)
    pinned: int | str | None = Field(default=None)
    search: str | None = Field(default=None)


class CategoryAPI(BaseAPICall):
    """Endpoints related to Categories.

    Shared request and error behavior is documented on ``BaseAPICall``.
    """

    def get_all_categories(self) -> list[CategoryMetadata]:
        """Get all the categories saved on the server.

        Returns:
            list[CategoryMetadata]: Metadata of every category on the server.

        Raises:
            APIHttpError: Any non-2xx status code returned by the server.
            APIResponseDecodeError: If the response body is not a list of
                objects matching ``CategoryMetadata``.
        """
        return self.request_model_list("GET", "/api/categories", CategoryMetadata)

    def get_category(self, id: str) -> CategoryMetadata | None:
        """Get the details of the specified category ID.

        Args:
            id: ID of the Category desired.

        Returns:
            CategoryMetadata | None: Details of the category, or None when the
                server answers with 400.

        Raises:
            APIHttpError: Any status code other than 200 and 400.

        Note:
            The 400 response of the server is turned into None instead of
            raising.
        """
        path = f"/api/categories/{id}"
        resp = self.request("GET", path, expected_statuses={200, 400})
        if resp.status_code == 400:
            return None
        return self.parse_model(
            CategoryMetadata, self.parse_json_response(resp, path), path
        )

    def create_category(
        self, name: str, search: str | None = None, pinned: bool | None = None
    ) -> OperationResponse:
        """Create a new Category.

        Args:
            name: Name of the Category.
            search: Matching predicate, if creating a Dynamic Category.
                Defaults to None.
            pinned: Whether the created category will be pinned. Defaults to
                None.

        Returns:
            OperationResponse: Result of the operation, with the ID of the
                created Category in the extra ``category_id`` field.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            A 400 response is returned in the operation result, with ``success``
            set to 0, instead of raising.
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
        self,
        id: str,
        name: str | None = None,
        search: str | None = None,
        pinned: bool | None = None,
    ) -> OperationResponse:
        """Modify a Category.

        Args:
            id: ID of the Category to update.
            name: New name of the Category. Defaults to None.
            search: Predicate. Trying to add a predicate to a category that
                already contains Archives will give you an error. Defaults to
                None.
            pinned: Add this argument to pin the Category. If you don't, the
                category will be unpinned on update. Defaults to None.

        Returns:
            OperationResponse: Result of the operation, with the ID of the
                updated Category in the extra ``category_id`` field.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            Failure responses such as 400 (error response) or 423 (Category
            locked for modification) are returned in the operation result, with
            ``success`` set to 0, instead of raising.
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
        """Remove a Category.

        Args:
            id: Category ID.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            A 423 response, sent when the Category is locked for modification,
            is returned in the operation result, with ``success`` set to 0,
            instead of raising.
        """
        return self.request_operation("DELETE", f"/api/categories/{id}")

    def add_archive_to_category(
        self, category_id: str, archive_id: str
    ) -> OperationResponse:
        """Add the specified Archive ID (see Archive API) to the given Category.

        Args:
            category_id: Category ID to add the Archive to.
            archive_id: Archive ID to add.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            A 423 response, sent when the Category is locked for modification,
            is returned in the operation result, with ``success`` set to 0,
            instead of raising.
        """
        return self.request_operation(
            "PUT", f"/api/categories/{category_id}/{archive_id}"
        )

    def remove_archive_from_category(
        self, category_id: str, archive_id: str
    ) -> OperationResponse:
        """Remove an Archive ID from a Category.

        Args:
            category_id: Category ID.
            archive_id: Archive ID.

        Returns:
            OperationResponse: Result of the operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            A 423 response, sent when the Category is locked for modification,
            is returned in the operation result, with ``success`` set to 0,
            instead of raising.
        """
        return self.request_operation(
            "DELETE", f"/api/categories/{category_id}/{archive_id}"
        )

    def get_bookmark_link(self) -> dict:
        """Retrieve the ID of the category linked to the bookmark feature.

        Returns:
            dict: Decoded response, with the linked category ID in
                ``category_id``, as an empty string if no category is linked.

        Raises:
            APIHttpError: Any non-2xx status code returned by the server.
            APIResponseDecodeError: If the response body is not valid JSON.
        """
        return self.request_json("GET", "/api/categories/bookmark_link")

    def update_bookmark_link(self, id: str) -> OperationResponse:
        """Link the bookmark feature to the specified static category.

        This determines which category archives are added to when using the
        bookmark button.

        Args:
            id: ID of the static category to link with the bookmark feature.

        Returns:
            OperationResponse: Result of the operation, with the ID of the
                linked category in the extra ``category_id`` field.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            Failure responses such as 400 (error response) or 404 (no category
            with the given ID) are returned in the operation result, with
            ``success`` set to 0, instead of raising.
        """
        return self.request_operation("PUT", f"/api/categories/bookmark_link/{id}")

    def disable_bookmark_feature(self) -> OperationResponse:
        """Disable the bookmark feature by removing the link to any category.

        Returns:
            OperationResponse: Result of the operation, with the ID of the
                previously linked category in the extra ``category_id`` field,
                as an empty string if no category was linked.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation("DELETE", "/api/categories/bookmark_link")
