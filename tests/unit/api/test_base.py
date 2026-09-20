import pytest
from pydantic import BaseModel, Field

from lanraragi_api.api.base import BaseAPICall


class TestBaseAPICall:
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
