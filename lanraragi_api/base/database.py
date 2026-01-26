import requests
from pydantic import BaseModel, Field

from lanraragi_api.base.base import BaseAPICall


class TagStatistic(BaseModel):
    namespace: str = Field(...)
    text: str = Field(...)
    weight: int = Field(...)


class DatabaseAPI(BaseAPICall):
    """
    Query and modify the database.
    """

    def get_tag_statistics(self, min_weight: int = 1) -> list[TagStatistic]:
        """
        Get tags from the database, with a value symbolizing their prevalence.

        :param min_weight: Add this parameter if you want to only get tags
        whose weight is at least the given minimum.
        Default is 1 if not specified, to get all tags.
        :return: list of tag statistics
        """
        resp = requests.get(
            f"{self.server}/api/database/stats",
            params=self.build_params({"minweight": min_weight}),
            headers=self.build_headers(),
        )
        list = resp.json()
        return [TagStatistic(**t) for t in list]

    def clean_database(self) -> dict:
        """
        Cleans the Database, removing entries for files that are no longer on
        the filesystem.
        :return: operation result
        """
        resp = requests.post(
            f"{self.server}/api/database/clean",
            params=self.build_params(),
            headers=self.build_headers(),
        )
        return resp.json()

    def drop_database(self) -> dict:
        """
        Delete the entire database, including user preferences.

        This is a rather dangerous endpoint, invoking it might lock you out of
        the server as a client!
        :return: operation result
        """
        resp = requests.post(
            f"{self.server}/api/database/drop",
            params=self.build_params(),
            headers=self.build_headers(),
        )
        return resp.json()

    def get_backup(self) -> dict:
        """
        Scans the entire database and returns a backup in JSON form.

        This backup can be reimported manually through the Backup and Restore
        feature.

        :return: backup json file
        """
        resp = requests.get(
            f"{self.server}/api/database/backup",
            params=self.build_params(),
            headers=self.build_headers(),
        )
        return resp.json()

    def clear_all_new_flags(self) -> dict:
        """
        Clears the "New!" flag on all archives.
        :return: operation result
        """
        resp = requests.delete(
            f"{self.server}/api/database/isnew",
            params=self.build_params(),
            headers=self.build_headers(),
        )
        return resp.json()
