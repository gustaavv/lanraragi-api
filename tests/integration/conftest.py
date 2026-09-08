import pytest


@pytest.fixture
def sample_user():
    return {"username": "dev_user", "role": "admin"}
