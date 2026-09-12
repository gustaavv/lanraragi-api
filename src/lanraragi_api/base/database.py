from os.path import isfile

from pydantic import BaseModel, Field
from requests import Response

from lanraragi_api.base.base import (
    BaseAPICall,
    DictLikeModel,
    MinionJobResponse,
    OperationResponse,
)


class TagStatistic(BaseModel):
    """Prevalence of a single tag in the database.

    Attributes:
        namespace: Namespace of the tag, if it has one.
        text: The tag itself.
        weight: Weight of the tag in the database.
    """

    namespace: str | None = Field(default=None)
    text: str = Field(...)
    weight: int = Field(...)


class BackupArchiveMetadata(DictLikeModel):
    """Archive metadata as returned in a database backup.

    Attributes:
        arcid: Unique identifier for the archive.
        title: Title of the archive.
        tags: Comma-separated list of tags associated with the archive.
        summary: Summary description of the archive.
        thumbhash: Thumbnail hash, or null if not set.
        filename: Filename of the archive.
    """

    arcid: str = Field(...)
    title: str = Field(...)
    tags: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    thumbhash: str | None = Field(default=None)
    filename: str = Field(...)


class BackupCategoryMetadata(DictLikeModel):
    """Category metadata as returned in a database backup.

    Attributes:
        archives: Array of archive IDs.
        catid: ID of the category.
        name: Name of the category.
        search: Category search filter.
    """

    archives: list[str] = Field(default_factory=list)
    catid: str = Field(...)
    name: str | None = Field(default=None)
    search: str | None = Field(default=None)


class BackupTankoubonMetadataJson(DictLikeModel):
    """Tankoubon metadata as returned in a database backup.

    Attributes:
        tankid: ID of the tankoubon.
        name: Name of the tankoubon.
        summary: Summary of the tankoubon.
        tags: Tags associated with the tankoubon.
        archives: Array of archive IDs.
    """

    tankid: str = Field(...)
    name: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    tags: str | None = Field(default=None)
    archives: list[str] = Field(default_factory=list)


class DatabaseBackup(DictLikeModel):
    """Full backup of the database in JSON form.

    Attributes:
        archives: Array of archive metadata.
        categories: Array of category metadata.
        tankoubons: Array of tankoubon metadata.
    """

    archives: list[BackupArchiveMetadata] = Field(default_factory=list)
    categories: list[BackupCategoryMetadata] = Field(default_factory=list)
    tankoubons: list[BackupTankoubonMetadataJson] = Field(default_factory=list)


class DatabaseAPI(BaseAPICall):
    """Database management APIs.

    Shared request and error behavior is documented on ``BaseAPICall``.
    """

    def get_tag_statistics(
        self,
        min_weight: int = 1,
        hide_excluded_namespaces: bool | None = None,
    ) -> list[TagStatistic]:
        """Get tags from the database, with a value symbolizing their prevalence.

        Args:
            min_weight: Only get tags whose weight is at least the given
                minimum. Defaults to 1, which gets all tags.
            hide_excluded_namespaces: Set to True to exclude tags whose
                namespace is configured in the server settings. Defaults to
                None, which returns all tags.

        Returns:
            list[TagStatistic]: One entry per tag, with its namespace, text and
                weight.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the response body is not valid JSON, or
                if it is not a list of ``TagStatistic`` objects.
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
        """Clean the Database.

        Entries for files that are no longer on the filesystem are hidden and
        then removed. They are only unlinked at first, so they do not appear in
        the UI; a subsequent run of this cleanup deletes the unlinked entries.

        Returns:
            OperationResponse: Result of the cleanup, including the amount of
                ``deleted`` and ``unlinked`` entries reported by the server.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation("POST", "/api/database/clean")

    def drop_database(self) -> OperationResponse:
        """Delete the entire database, including user preferences.

        This is a rather dangerous endpoint: invoking it might lock you out of
        the server as a client.

        Returns:
            OperationResponse: Result of the database drop.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation("POST", "/api/database/drop")

    def get_backup(self) -> DatabaseBackup:
        """Scan the entire database and return a backup in JSON form.

        Consider using ``queue_backup`` if your database is large, as this
        basic GET endpoint might time out if it takes too long to generate the
        backup.

        This backup can be reimported manually through the Backup and Restore
        feature.

        Returns:
            DatabaseBackup: Archive, category and tankoubon metadata of the
                entire database.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``DatabaseBackup``.
        """
        return self.request_model("GET", "/api/database/backup", DatabaseBackup)

    def queue_backup(self) -> MinionJobResponse:
        """Queue a Minion job to generate a backup JSON file.

        Use the returned job ID to check progress, then download the file once
        the job is complete through ``download_backup``.

        Returns:
            MinionJobResponse: Enqueued job, whose ``job`` field holds the ID
                of the Minion job.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``MinionJobResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation(
            "POST", "/api/database/backup", model=MinionJobResponse
        )

    def download_backup(self, jobid: int, format: str | None = None) -> Response:
        """Download the backup JSON file generated by a completed backup job.

        Args:
            jobid: ID of the completed backup job.
            format: Format of the returned backup. ``json`` returns the backup
                as a JSON response, while ``file`` returns it as a file.
                Defaults to None, which the server treats as ``file``.

        Returns:
            Response: Raw response of the server, holding the backup file or
                JSON payload.

        Raises:
            APIHttpError: 400 if the job is not found or not completed yet, or
                any other non-2xx status code.
        """
        return self.request(
            "GET",
            f"/api/database/backup/{jobid}",
            params={"format": format},
        )

    def queue_restore(self, file_path: str) -> MinionJobResponse:
        """Queue a Minion job to restore from a backup JSON file.

        Use the returned job ID to check progress.

        Args:
            file_path: Path to the backup JSON file to restore. Backslashes are
                normalized to forward slashes before the file is looked up.

        Returns:
            MinionJobResponse: Enqueued job, whose ``job`` field holds the ID
                of the Minion job.

        Raises:
            FileNotFoundError: If ``file_path`` does not point to an existing
                file.
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``MinionJobResponse``.
            APIOperationError: If the operation failed and raising is enabled.

        Note:
            A 400 response, returned for an invalid request such as a malformed
            backup file, is returned in the operation result, with ``success``
            set to 0, instead of raising.
        """
        file_path = file_path.replace("\\", "/")

        if not isfile(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

        with open(file_path, "rb") as backup_file:
            return self.request_operation(
                "POST",
                "/api/database/restore",
                model=MinionJobResponse,
                files={
                    "file": (
                        file_path.split("/")[-1],
                        backup_file,
                        "application/octet-stream",
                    )
                },
            )

    def clear_all_new_flags(self) -> OperationResponse:
        """Clear the "New!" flag on all archives.

        Returns:
            OperationResponse: Result of the flag clearing operation.

        Raises:
            APIResponseDecodeError: If the response body is not valid JSON, or
                does not match ``OperationResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        return self.request_operation("DELETE", "/api/database/isnew")
