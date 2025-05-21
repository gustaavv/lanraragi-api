from typing import Optional, Any

import requests
from pydantic import BaseModel
from script_house.utils import JsonUtils

from lanraragi_api.base.base import BaseAPICall


class BasicJobStatus(BaseModel):
    state: str
    task: str
    error: Optional[str]
    notes: Optional[dict[str, str]]


class FullJobStatus(BaseModel):
    args: list[str] = []
    attempts: str
    children: list[Any] = []
    created: str
    delayed: str
    expires: Optional[str] = None
    finished: str
    id: str
    lax: int = 0
    notes: dict[Any, Any] = {}
    parents: list[Any] = []
    priority: str
    queue: str
    result: Optional[dict[Any, Any]]
    retried: Optional[Any]
    retries: str
    started: str
    state: str
    task: str
    worker: int


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
        resp = requests.get(f"{self.server}/api/minion/{job_id}", params=self.build_params(),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, BasicJobStatus)

    def get_full_status(self, job_id: str) -> FullJobStatus:
        """
        Get the status of a Minion Job. This API is there for internal usage
        mostly, but you can use it to get detailed status for jobs like plugin
        runs or URL downloads.
        :param job_id: ID of the Job.
        :return: FullJobStatus
        """
        resp = requests.get(f"{self.server}/api/minion/{job_id}/detail", params=self.build_params(),
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, FullJobStatus)
