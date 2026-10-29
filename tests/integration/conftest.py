import os
import subprocess

import pytest

from lanraragi_api import LANraragiAPI
from script.integration_test_setup.config_lrr import ConfigLRRArgs, run


@pytest.fixture(scope="session")
def api() -> LANraragiAPI:
    # TODO: see script/integration_test_setup/config_lrr.py#set_custom_config
    apikey = "123456"
    # TODO: see script/integration_test_setup/compose.yml
    server = "http://localhost:33333"
    api = LANraragiAPI(server, key=apikey)
    return api


def integration_test_setup(content_dir: str):
    _ = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            "script/integration_test_setup/compose.yml",
            "up",
            "-d",
            "--quiet-pull",
        ],
        text=True,
        check=True,
        env=os.environ | {"LRR_TEST_CONTENT_FOLDER": content_dir},
    )
    run(
        ConfigLRRArgs(
            base_url="http://localhost:33333", lrr_container_name="lrr_api_test_lrr"
        )
    )


def integration_test_teardown(content_dir: str):
    _ = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            "script/integration_test_setup/compose.yml",
            "down",
            "-v",
        ],
        text=True,
        check=True,
        env=os.environ | {"LRR_TEST_CONTENT_FOLDER": content_dir},
    )
