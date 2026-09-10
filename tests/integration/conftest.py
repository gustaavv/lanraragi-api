import pytest

from lanraragi_api import LANraragiAPI


@pytest.fixture
def api():
    # TODO: see script/integration_test_setup/config_lrr.py#set_custom_config
    apikey = "123456"
    # TODO: see script/integration_test_setup/compose.yml
    server = "http://localhost:33333"
    api = LANraragiAPI(server, key=apikey)
    return api
