from requests import Response

from lanraragi_api.base.base import BaseAPICall


class OPDSAPI(BaseAPICall):
    """Endpoints related to OPDS catalog generation and serving.

    Shared request and error behavior is documented on ``BaseAPICall``.
    """

    def get_opds_catalog(
        self, archive_id: str | None = None, category_id: str | None = None
    ) -> str:
        """Get the Archive Index as an OPDS 1.2 Catalog with PSE 1.1 compatibility.

        Args:
            archive_id: ID of a single archive. When set, the request is
                forwarded to ``get_opds_item`` and one OPDS entry is returned
                instead of the catalog. Defaults to None.
            category_id: Category ID. If passed, the OPDS catalog will be
                filtered to only show archives from this category. Defaults to
                None.

        Returns:
            str: OPDS catalog, or a single OPDS entry when ``archive_id`` is
                set, as an XML string.

        Raises:
            APIHttpError: Any non-2xx status code returned by the server.
        """
        if archive_id:
            return self.get_opds_item(archive_id)

        path = "/api/opds"
        resp = self.request("GET", path, params={"category": category_id})
        return resp.text

    def get_opds_item(self, id: str) -> str:
        """Return a specific OPDS item as XML.

        This shows only one ``<entry>`` for the given ID in the result, instead
        of all the archives.

        Args:
            id: ID of an archive.

        Returns:
            str: OPDS entry as an XML string.

        Raises:
            APIHttpError: Any non-2xx status code returned by the server.
        """
        resp = self.request("GET", f"/api/opds/{id}")
        return resp.text

    def get_opds_page(self, id: str, page: int | None = None) -> Response:
        """Return a specific image page for OPDS-PSE.

        Args:
            id: ID of an archive.
            page: Page number to fetch. Defaults to None, which lets the server
                pick the page.

        Returns:
            Response: Raw response holding the image bytes of the page.

        Raises:
            APIHttpError: Any non-2xx status code returned by the server.
        """
        return self.request("GET", f"/api/opds/{id}/pse", params={"page": page})
