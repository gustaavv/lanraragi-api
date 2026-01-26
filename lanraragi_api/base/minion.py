from typing import Optional, Any

import requests
from pydantic import BaseModel, Field

from lanraragi_api.base.base import BaseAPICall


class BasicJobStatus(BaseModel):
    state: str = Field(...)
    task: str = Field(...)
    error: Optional[str] = Field(default=None)
    notes: Optional[dict[str, str]] = Field(default=None)


class FullJobStatus(BaseModel):
    args: list[str] = Field(default_factory=list)
    attempts: str = Field(...)
    children: list[Any] = Field(default_factory=list)
    created: str = Field(...)
    delayed: str = Field(...)
    expires: Optional[str] = Field(default=None)
    finished: str = Field(...)
    id: str = Field(...)
    lax: int = Field(default=0)
    notes: dict[Any, Any] = Field(default_factory=dict)
    parents: list[Any] = Field(default_factory=list)
    priority: str = Field(...)
    queue: str = Field(...)
    result: Optional[dict[Any, Any]] = Field(default=None)
    retried: Optional[Any] = Field(default=None)
    retries: str = Field(...)
    started: str = Field(...)
    state: str = Field(...)
    task: str = Field(...)
    worker: int = Field(...)


class MinionAPI(BaseAPICall):
    """
    Control the built-in Minion Job Queue.
    """

    def get_basic_status(self, job_id: str) -> BasicJobStatus:
        """
        For a given Minion job ID, check whether it succeeded or failed.

        Minion jobs are ran for various occasions like thumbnails, cache warmup
        and handling incoming files.

        For some jobs, you can check the notes field for progress information.
        Look at https://docs.mojolicious.org/Minion/Guide#Job-progress for
        more information.

        :param job_id: ID of the Job.
        :return: BasicJobStatus
        """
        resp = requests.get(
            f"{self.server}/api/minion/{job_id}",
            params=self.build_params(),
            headers=self.build_headers(),
        )
        return BasicJobStatus(**resp.json())

    def get_full_status(self, job_id: str) -> FullJobStatus:
        """
        Get the status of a Minion Job. This API is there for internal usage
        mostly, but you can use it to get detailed status for jobs like plugin
        runs or URL downloads.
        :param job_id: ID of the Job.
        :return: FullJobStatus
        """
        resp = requests.get(
            f"{self.server}/api/minion/{job_id}/detail",
            params=self.build_params(),
            headers=self.build_headers(),
        )
        return FullJobStatus(**resp.json())
