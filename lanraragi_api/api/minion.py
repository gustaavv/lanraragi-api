from typing import Optional, Any

import requests
from pydantic import BaseModel
from script_house.utils import JsonUtils

from ..common.base import BaseAPICall


class BasicJobStatus(BaseModel):
    state: Optional[str] = None
    task: Optional[str] = None
    error: Optional[str] = None


class DetailedJobStatus(BaseModel):
    args: list[str] = []
    attempts: str
    children: list[Any] = []
    created: str
    delayed: str
    finished: str
    id: str
    notes: dict[Any, Any] = {}
    parents: list[Any] = []
    priority: str
    queue: str
    result: dict[Any, Any] = {}
    retried: Optional[Any]
    retries: str
    started: str
    state: str
    task: str
    worker: int


class MinionAPI(BaseAPICall):
    """
    Control the built-in Minion Job Queue.

    Minion jobs are ran for various occasions like thumbnails, cache
    warmup and handling incoming files.
    """

    def get_basic_status(self, job_id: str) -> BasicJobStatus:
        """
        For a given Minion job ID, check whether it succeeded or failed.

        :param job_id: ID of the Job.
        :return:
        """
        resp = requests.get(f"{self.server}/api/minion/{job_id}", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, BasicJobStatus)

    def get_full_status(self, job_id: str) -> DetailedJobStatus:
        """
        Get the status of a Minion Job. This API is there for internal usage
        mostly, but you can use it to get detailed status for jobs like plugin
        runs or URL downloads.
        :param job_id: ID of the Job.
        :return:
        """
        resp = requests.get(f"{self.server}/api/minion/{job_id}/detail", params={'key': self.key},
                            headers=self.build_headers())
        return JsonUtils.to_obj(resp.text, DetailedJobStatus)
