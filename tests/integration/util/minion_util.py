import time
from typing import Literal

from lanraragi_api.base import MinionAPI


def wait_minion_job_util(
    minionApi: MinionAPI,
    job_id: int,
    state: Literal["inactive", "active", "finished", "failed"],
    timeout: int = 60,
    interval: int = 1,
):
    start_time = time.time()

    while time.time() - start_time < timeout:
        resp = minionApi.get_basic_status(job_id)
        if resp.state == state:
            return
        time.sleep(interval)

    raise TimeoutError(
        f"Minion job {job_id} did not become {state} within {timeout} seconds."
    )
