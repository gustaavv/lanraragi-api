from requests import Response

from lanraragi_api.base.base import BaseAPICall


class OPDSAPI(BaseAPICall):
    """
    Endpoints related to OPDS catalog generation and serving.
    """

    def get_opds_catalog(
        self, archive_id: str | None = None, category_id: str | None = None
    ) -> str:
        """
        Get the Archive Index as an OPDS 1.2 Catalog with PSE 1.1 compatibility.
        :param category_id: Category ID. If passed, the OPDS catalog will be
        filtered to only show archives from this category.
        :param archive_id: Backward-compatible argument for getting one OPDS item.
        :return: XML string
        """
        if archive_id:
            return self.get_opds_item(archive_id)

        path = "/api/opds"
        resp = self.request("GET", path, params={"category": category_id})
        return resp.text

    def get_opds_item(self, id: str) -> str:
        """
        Get one OPDS item entry by archive ID.
        :param id: ID of an archive.
        :return: XML string
        """
        resp = self.request("GET", f"/api/opds/{id}")
        return resp.text

    def get_opds_page(self, id: str, page: int | None = None) -> Response:
        """
        Get an OPDS-PSE image page for an archive.
        :param id: ID of an archive.
        :param page: Optional page number.
        :return: response object with image bytes
        """
        return self.request("GET", f"/api/opds/{id}/pse", params={"page": page})
