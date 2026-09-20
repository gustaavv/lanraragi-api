from typing import Any

from pydantic import BaseModel, Field

from lanraragi_api.entity.base import OperationResponse


class MinionJobResponse(OperationResponse):
    """Result of an operation that queued a Minion job.

    Attributes:
        job: ID of the queued Minion job, if one was queued.
    """

    job: int | None = Field(default=None)


class BasicJobStatus(BaseModel):
    """Basic status of a Minion job.

    Attributes:
        state: State of the job, one of ``inactive``, ``active``,
            ``finished`` or ``failed``.
        task: Name of the task the job runs.
        error: Error message of the job, if any.
        notes: Arbitrary data attached to the job.
    """

    state: str = Field(...)
    task: str = Field(...)
    error: str | None = Field(default=None)
    notes: dict[Any, Any] | None = Field(default=None)


class FullJobStatus(BaseModel):
    """Detailed status of a Minion job.

    Attributes:
        args: Arguments the job was queued with.
        attempts: Number of attempts made to run the job.
        children: IDs of child jobs attached to the job.
        created: Timestamp when the job was created.
        delayed: Timestamp until which the job is delayed.
        expires: Timestamp when the job expires, if it was given one.
        finished: Timestamp when the job finished.
        id: ID of the job.
        lax: Whether the job runs in lax mode.
        notes: Arbitrary data attached to the job.
        parents: IDs of parent jobs attached to the job.
        priority: Priority of the job.
        queue: Queue the job belongs to.
        result: Result data of the job, if it produced any.
        retried: Information about the retry of the job, if it was retried.
        retries: Number of retries allowed for the job.
        started: Timestamp when the job started.
        state: State of the job.
        task: Name of the task the job runs.
        worker: ID of the worker that ran the job.
    """

    args: list[Any] = Field(default_factory=list)
    attempts: str = Field(...)
    children: list[Any] = Field(default_factory=list)
    created: str = Field(...)
    delayed: str = Field(...)
    expires: str | None = Field(default=None)
    finished: str | None = Field(default=None)
    id: str = Field(...)
    lax: int = Field(default=0)
    notes: dict[Any, Any] = Field(default_factory=dict)
    parents: list[Any] = Field(default_factory=list)
    priority: str = Field(...)
    queue: str = Field(...)
    result: dict[Any, Any] | None = Field(default=None)
    retried: Any | None = Field(default=None)
    retries: str = Field(...)
    started: str = Field(...)
    state: str = Field(...)
    task: str = Field(...)
    worker: int = Field(...)
