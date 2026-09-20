import json
from typing import Any

from lanraragi_api.api.base import BaseAPICall
from lanraragi_api.entity.minion import BasicJobStatus, FullJobStatus, MinionJobResponse


class MinionAPI(BaseAPICall):
    """Minion Job Queue APIs.

    Shared request and error behavior is documented on ``BaseAPICall``.
    """

    def get_basic_status(self, job_id: int | str) -> BasicJobStatus:
        """Check whether a Minion job succeeded or failed.

        Minion jobs are ran for various occasions like thumbnails, cache
        warmup and handling incoming files.

        For some jobs, you can check the notes field for progress information.
        Look at the Minion Guide for more details:
        https://docs.mojolicious.org/Minion/Guide#Job-progress

        Args:
            job_id: ID of the job to query status for.

        Returns:
            BasicJobStatus: Basic status of the job.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the body does not match
                ``BasicJobStatus``.
        """
        return self.request_model("GET", f"/api/minion/{job_id}", BasicJobStatus)

    def get_full_status(self, job_id: int | str) -> FullJobStatus:
        """Get the status of a Minion job.

        This API is there for internal usage mostly, but you can use it to get
        detailed status for jobs like plugin runs or URL downloads.

        Args:
            job_id: ID of the job.

        Returns:
            FullJobStatus: Detailed status of the job.

        Raises:
            APIHttpError: Any status code other than 200.
            APIResponseDecodeError: If the body does not match
                ``FullJobStatus``.
        """
        return self.request_model("GET", f"/api/minion/{job_id}/detail", FullJobStatus)

    def queue_minion_job(
        self,
        jobname: str,
        args: str | list[Any],
        priority: int = 0,
    ) -> MinionJobResponse:
        """Queue a job with the specified type and parameters.

        See LANraragi::Utils::Minion for all the available types of jobs and
        the parameters they require.

        There's no API contract in place for whether a job type exists on a
        given server version, so using this is not recommended unless you have
        a good reason to.

        Args:
            jobname: Type of the job to instantiate. Documented values are
                ``thumbnail_task``, ``tank_thumbnail_task``,
                ``page_thumbnails``, ``regen_all_thumbnails``,
                ``find_duplicates``, ``build_stat_hashes``, ``handle_upload``,
                ``download_url`` and ``run_plugin``.
            args: Arguments of the job, either a JSON array string or a list of
                values.
            priority: Priority of the Minion job. The higher the number, the
                more important the job is. Defaults to 0.

        Returns:
            MinionJobResponse: Result of the call, with the ID of the queued
                job.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``MinionJobResponse``.
            APIOperationError: If the operation failed and raising is enabled.
        """
        args_value = args if isinstance(args, str) else json.dumps(args)
        return self.request_operation(
            "POST",
            f"/api/minion/{jobname}/queue",
            model=MinionJobResponse,
            params={"args": args_value, "priority": priority},
        )
