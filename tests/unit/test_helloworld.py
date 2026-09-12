from lanraragi_api.base.base import Auth, BaseAPICall


def hello_world():
    return "hello, world"


def test_hello_world():
    assert hello_world() == "hello, world"


def test_default_params():
    api = BaseAPICall(server="someServer", key="abc", auth_way=Auth.QUERY_PARAM)
    assert api.default_params == {"key": "abc"}
