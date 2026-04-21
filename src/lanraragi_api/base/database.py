from pydantic import BaseModel, Field

from lanraragi_api.base.base import BaseAPICall, DictLikeModel, OperationResponse


class TagStatistic(BaseModel):
    namespace: str | None = Field(default=None)
    text: str = Field(...)
    weight: int = Field(...)


class BackupArchiveMetadata(DictLikeModel):
    arcid: str = Field(...)
    title: str = Field(...)
    tags: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    thumbhash: str | None = Field(default=None)
    filename: str = Field(...)


class BackupCategoryMetadata(DictLikeModel):
    archives: list[str] = Field(default_factory=list)
    catid: str = Field(...)
    name: str | None = Field(default=None)
    search: str | None = Field(default=None)


class BackupTankoubonMetadataJson(DictLikeModel):
    tankid: str = Field(...)
    name: str | None = Field(default=None)
    archives: list[str] = Field(default_factory=list)


class DatabaseBackup(DictLikeModel):
    archives: list[BackupArchiveMetadata] = Field(default_factory=list)
    categories: list[BackupCategoryMetadata] = Field(default_factory=list)
    tankoubons: list[BackupTankoubonMetadataJson] = Field(default_factory=list)


class DatabaseAPI(BaseAPICall):
    """
    Query and modify the database.
    """

    def get_tag_statistics(
        self,
        min_weight: int = 1,
        hide_excluded_namespaces: bool | None = None,
    ) -> list[TagStatistic]:
        """
        Get tags from the database, with a value symbolizing their prevalence.

        :param min_weight: Add this parameter if you want to only get tags
        whose weight is at least the given minimum.
        Default is 1 if not specified, to get all tags.
        :param hide_excluded_namespaces: Whether to hide tags that belong to
        excluded namespaces in server settings.
        :return: list of tag statistics
        """
        hide_excluded = None
        if hide_excluded_namespaces is not None:
            hide_excluded = "true" if hide_excluded_namespaces else "false"

        return self.request_model_list(
            "GET",
            "/api/database/stats",
            TagStatistic,
            params={
                "minweight": min_weight,
                "hide_excluded_namespaces": hide_excluded,
            },
        )

    def clean_database(self) -> OperationResponse:
        """
        Cleans the Database, removing entries for files that are no longer on
        the filesystem.
        :return: operation result
        """
        return self.request_operation("POST", "/api/database/clean")

    def drop_database(self) -> OperationResponse:
        """
        Delete the entire database, including user preferences.

        This is a rather dangerous endpoint, invoking it might lock you out of
        the server as a client!
        :return: operation result
        """
        return self.request_operation("POST", "/api/database/drop")

    def get_backup(self) -> DatabaseBackup:
        """
        Scans the entire database and returns a backup in JSON form.

        This backup can be reimported manually through the Backup and Restore
        feature.

        :return: backup json file
        """
        return self.request_model("GET", "/api/database/backup", DatabaseBackup)

    def clear_all_new_flags(self) -> OperationResponse:
        """
        Clears the "New!" flag on all archives.
        :return: operation result
        """
        return self.request_operation("DELETE", "/api/database/isnew")
