from pydantic import BaseModel, Field

from lanraragi_api.util.http import (
    HeaderType,
    ParamType,
    merge_headers,
    merge_params,
    normalize_params,
)


class TestHttpUtil:
    def test_merge_headers(self):
        class TestCase(BaseModel):
            old: HeaderType = Field(default={})
            new: HeaderType = Field(default={})
            target: HeaderType = Field(default={})

        test_cases: list[TestCase] = [
            TestCase(),
            TestCase(new={"k1": "v1"}, target={"k1": "v1"}),
            TestCase(old={"k1": "v1"}, target={"k1": "v1"}),
            TestCase(
                old={"k1": "v1"}, new={"k2": "v2"}, target={"k1": "v1", "k2": "v2"}
            ),
            TestCase(old={"k1": "v1"}, new={"k1": "v12"}, target={"k1": "v12"}),
            TestCase(
                old={"k1": "v1"},
                new={"k1": "v12", "k2": "v2"},
                target={"k1": "v12", "k2": "v2"},
            ),
            TestCase(
                old={"k1": "v1", "k2": "v2"},
                new={"k1": "v12", "k3": "v3"},
                target={"k1": "v12", "k2": "v2", "k3": "v3"},
            ),
        ]

        for tc in test_cases:
            assert tc.target == merge_headers(tc.old, tc.new)

    def test_merge_params(self):
        class TestCase(BaseModel):
            old: ParamType = Field(default={})
            new: ParamType = Field(default={})
            target: ParamType = Field(default={})

        test_cases: list[TestCase] = [
            TestCase(),
            TestCase(new={"k1": "v1"}, target={"k1": "v1"}),
            TestCase(old={"k1": "v1"}, target={"k1": "v1"}),
            TestCase(
                old={"k1": "v1"}, new={"k2": "v2"}, target={"k1": "v1", "k2": "v2"}
            ),
            TestCase(old={"k1": "v1"}, new={"k1": "v12"}, target={"k1": "v12"}),
            TestCase(
                old={"k1": "v1"},
                new={"k1": "v12", "k2": "v2"},
                target={"k1": "v12", "k2": "v2"},
            ),
            TestCase(
                old={"k1": "v1", "k2": "v2"},
                new={"k1": "v12", "k3": "v3"},
                target={"k1": "v12", "k2": "v2", "k3": "v3"},
            ),
        ]

        for tc in test_cases:
            assert tc.target == merge_params(tc.old, tc.new)

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
            assert tc.target == normalize_params(tc.input)
