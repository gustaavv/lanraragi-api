from typing import Any

import pytest
from pydantic import BaseModel, Field

from lanraragi_api.base.base import BaseAPICall

HeaderType = dict[str, Any]
ParamType = dict[str, Any]


class TestBaseAPICall:
    def test_build_headers(self):
        class TestCase(BaseModel):
            default: HeaderType = Field(default={})
            new: HeaderType = Field(default={})
            target: HeaderType = Field(default={})

        test_cases: list[TestCase] = [
            TestCase(),
            TestCase(new={"k1": "v1"}, target={"k1": "v1"}),
            TestCase(default={"k1": "v1"}, target={"k1": "v1"}),
            TestCase(
                default={"k1": "v1"}, new={"k2": "v2"}, target={"k1": "v1", "k2": "v2"}
            ),
            TestCase(default={"k1": "v1"}, new={"k1": "v12"}, target={"k1": "v12"}),
            TestCase(
                default={"k1": "v1"},
                new={"k1": "v12", "k2": "v2"},
                target={"k1": "v12", "k2": "v2"},
            ),
            TestCase(
                default={"k1": "v1", "k2": "v2"},
                new={"k1": "v12", "k3": "v3"},
                target={"k1": "v12", "k2": "v2", "k3": "v3"},
            ),
        ]

        for tc in test_cases:
            api = BaseAPICall("", default_headers=tc.default)
            assert tc.target == api.build_headers(tc.new)

    def test_normalize_params(self):
        class TestCase(BaseModel):
            input: ParamType = Field(default={})
            target: ParamType = Field(default={})

        test_cases: list[TestCase] = [
            TestCase(),
            TestCase(input={"k1": "v1"}, target={"k1": "v1"}),
            TestCase(input={"k1": None}),
            TestCase(input={"k1": True}, target={"k1": "true"}),
            TestCase(input={"k1": False}, target={"k1": "false"}),
            TestCase(
                input={"k1": None, "k2": True, "k3": 123},
                target={"k2": "true", "k3": 123},
            ),
        ]

        for tc in test_cases:
            api = BaseAPICall("")
            assert tc.target == api._normalize_params(tc.input)  # pyright: ignore[reportPrivateUsage]

    def test_build_params(self):
        class TestCase(BaseModel):
            default: ParamType = Field(default={})
            new: ParamType = Field(default={})
            target: ParamType = Field(default={})

        test_cases: list[TestCase] = [
            TestCase(),
            TestCase(new={"k1": "v1"}, target={"k1": "v1"}),
            TestCase(default={"k1": "v1"}, target={"k1": "v1"}),
            TestCase(
                default={"k1": "v1"}, new={"k2": "v2"}, target={"k1": "v1", "k2": "v2"}
            ),
            TestCase(default={"k1": "v1"}, new={"k1": "v12"}, target={"k1": "v12"}),
            TestCase(
                default={"k1": "v1"},
                new={"k1": "v12", "k2": "v2"},
                target={"k1": "v12", "k2": "v2"},
            ),
            TestCase(
                default={"k1": "v1", "k2": "v2"},
                new={"k1": "v12", "k3": "v3"},
                target={"k1": "v12", "k2": "v2", "k3": "v3"},
            ),
            TestCase(
                default={"k1": "v1", "k2": "v2"},
                new={"k1": None, "k3": "v3"},
                target={"k2": "v2", "k3": "v3"},
            ),
            TestCase(
                default={"k1": "v1", "k2": True},
                new={"k1": False, "k3": "v3"},
                target={"k1": "false", "k2": "true", "k3": "v3"},
            ),
        ]

        for tc in test_cases:
            api = BaseAPICall("", default_params=tc.default)
            assert tc.target == api.build_params(tc.new)

    def test_to_url(self):
        class TestCase(BaseModel):
            server_url: str = Field(...)
            path: str = Field(...)
            will_raise: bool = Field(default=False)
            raise_type: type = Field(default=Exception)
            raise_msg: str = Field(default="")
            target: str | None = Field(default="")

        test_cases: list[TestCase] = [
            TestCase(
                server_url="http://some.url.local/",
                path="api/archive",
                target="http://some.url.local/api/archive",
            ),
            TestCase(
                server_url="https://some.url.local",
                path="/api/archive",
                target="https://some.url.local/api/archive",
            ),
            TestCase(
                server_url="127.0.0.1",
                path="/api/archive",
                target="127.0.0.1/api/archive",
            ),
            TestCase(
                server_url="https://some.url.local",
                path="https://some.url.local/api/archive",
                will_raise=True,
                raise_type=ValueError,
                raise_msg="absolute URLs",
            ),
            TestCase(
                server_url="http://some.url.local",
                path="http://some.url.local/api/archive",
                will_raise=True,
                raise_type=ValueError,
                raise_msg="absolute URLs",
            ),
            TestCase(
                server_url="https://some.url.local",
                path="/api/archive?a=b",
                will_raise=True,
                raise_type=ValueError,
                raise_msg="include query or fragment",
            ),
            TestCase(
                server_url="https://some.url.local",
                path="/api/archive#/a/b",
                will_raise=True,
                raise_type=ValueError,
                raise_msg="include query or fragment",
            ),
        ]

        for tc in test_cases:
            api = BaseAPICall(tc.server_url)
            if tc.will_raise:
                with pytest.raises(tc.raise_type, match=tc.raise_msg):
                    _ = api._to_url(tc.path)  # pyright: ignore[reportPrivateUsage]
            else:
                assert tc.target == api._to_url(tc.path)  # pyright: ignore[reportPrivateUsage]
