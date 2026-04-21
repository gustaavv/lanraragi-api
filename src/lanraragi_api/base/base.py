import base64
from enum import Enum
from typing import Any

import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Auth(str, Enum):
    QUERY_PARAM = "query param"
    AUTH_HEADER = "auth header"


class DictLikeModel(BaseModel):
    """Compatibility helper for endpoints that previously returned dict."""

    def __getitem__(self, key: str):
        data = self.model_dump()
        if key not in data:
            raise KeyError(key)
        return data[key]

    def get(self, key: str, default=None):
        return self.model_dump().get(key, default)

    def keys(self):
        return self.model_dump().keys()

    def items(self):
        return self.model_dump().items()


class OperationResponse(DictLikeModel):
    model_config = ConfigDict(extra="allow")

    operation: str = Field(...)
    error: str | None = Field(default=None)
    successMessage: str | None = Field(default=None)
    success: int = Field(...)


class MinionJobResponse(OperationResponse):
    job: int | None = Field(default=None)


class APIError(Exception):
    """Base exception for all API client errors."""


class APIRequestError(APIError):
    def __init__(self, url: str, error_type: str | None = None):
        suffix = f" ({error_type})" if error_type else ""
        super().__init__(f"Request to {url} failed{suffix}")
        self.url = url


class APIHttpError(APIError):
    def __init__(self, status_code: int, url: str):
        super().__init__(f"HTTP {status_code} for {url}")
        self.status_code = status_code
        self.url = url


class APIResponseDecodeError(APIError):
    def __init__(self, url: str, message: str):
        super().__init__(f"Failed to parse response from {url}: {message}")
        self.url = url


class APIOperationError(APIError):
    def __init__(
        self,
        operation: str,
        message: str | None,
        status_code: int | None = None,
        payload: dict[str, Any] | None = None,
    ):
        error_message = message or "operation failed without an error message"
        prefix = f"Operation '{operation}' failed"
        if status_code is not None:
            prefix = f"{prefix} with HTTP {status_code}"
        super().__init__(f"{prefix}: {error_message}")
        self.operation = operation
        self.message = message
        self.status_code = status_code
        self.payload = payload


class BaseAPICall:
    def __init__(
        self,
        server: str,
        key: str = None,
        auth_way: Auth = Auth.AUTH_HEADER,
        timeout: int | float | tuple[int, int] | None = None,
        include_error_payload: bool = False,
        include_operation_error_message: bool = True,
        raise_on_operation_error: bool = False,
        default_headers=None,
        default_params=None,
    ):
        if default_params is None:
            default_params = {}
        if default_headers is None:
            default_headers = {}

        self.auth_way = auth_way
        self.key = key
        self.server = server
        self.timeout = timeout
        self.include_error_payload = include_error_payload
        self.include_operation_error_message = include_operation_error_message
        self.raise_on_operation_error = raise_on_operation_error
        if self.server.endswith("/"):
            self.server = self.server[:-1]
        self.default_headers = dict(default_headers)
        self.default_params = dict(default_params)

        if key:
            if auth_way == Auth.QUERY_PARAM:
                self.default_params["key"] = self.key
            elif auth_way == Auth.AUTH_HEADER:
                base64_key = base64.b64encode(self.key.encode("utf-8")).decode("utf-8")
                self.default_headers["Authorization"] = f"Bearer {base64_key}"

    def build_headers(self, headers=None):
        if headers is None:
            headers = {}
        merged = dict(headers)
        for k in self.default_headers:
            if k in merged:
                continue
            merged[k] = self.default_headers[k]
        return merged

    def build_params(self, params=None):
        if params is None:
            params = {}
        merged = dict(params)
        for k in self.default_params:
            if k in merged:
                continue
            merged[k] = self.default_params[k]
        return merged

    def _to_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            raise ValueError("absolute URLs are not allowed")
        if "?" in path or "#" in path:
            raise ValueError("path must not include query or fragment")
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.server}{path}"

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_statuses: set[int] | None = None,
        timeout: int | float | tuple[int, int] | None = None,
        **kwargs,
    ) -> requests.Response:
        url = self._to_url(path)

        try:
            resp = requests.request(
                method=method.upper(),
                url=url,
                params=self.build_params(params),
                headers=self.build_headers(headers),
                timeout=self.timeout if timeout is None else timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise APIRequestError(url, exc.__class__.__name__)

        if expected_statuses is None:
            is_ok = 200 <= resp.status_code < 300
        else:
            is_ok = resp.status_code in expected_statuses
        if not is_ok:
            raise APIHttpError(resp.status_code, url)

        return resp

    def parse_json_response(self, response: requests.Response, path: str):
        url = self._to_url(path)
        try:
            return response.json()
        except ValueError as exc:
            raise APIResponseDecodeError(url, str(exc)) from exc

    def parse_model(self, model: type[BaseModel], payload: Any, path: str):
        url = self._to_url(path)
        try:
            return model.model_validate(payload)
        except ValidationError as exc:
            raise APIResponseDecodeError(url, str(exc)) from exc

    def parse_model_list(self, model: type[BaseModel], payload: Any, path: str):
        if not isinstance(payload, list):
            raise APIResponseDecodeError(self._to_url(path), "response is not a list")
        return [self.parse_model(model, item, path) for item in payload]

    def request_json(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_statuses: set[int] | None = None,
        timeout: int | float | tuple[int, int] | None = None,
        **kwargs,
    ):
        resp = self.request(
            method=method,
            path=path,
            params=params,
            headers=headers,
            expected_statuses=expected_statuses,
            timeout=timeout,
            **kwargs,
        )
        return self.parse_json_response(resp, path)

    def request_model(
        self,
        method: str,
        path: str,
        model: type[BaseModel],
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_statuses: set[int] | None = None,
        timeout: int | float | tuple[int, int] | None = None,
        **kwargs,
    ):
        payload = self.request_json(
            method=method,
            path=path,
            params=params,
            headers=headers,
            expected_statuses=expected_statuses,
            timeout=timeout,
            **kwargs,
        )
        return self.parse_model(model, payload, path)

    def request_model_list(
        self,
        method: str,
        path: str,
        model: type[BaseModel],
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_statuses: set[int] | None = None,
        timeout: int | float | tuple[int, int] | None = None,
        **kwargs,
    ):
        payload = self.request_json(
            method=method,
            path=path,
            params=params,
            headers=headers,
            expected_statuses=expected_statuses,
            timeout=timeout,
            **kwargs,
        )
        return self.parse_model_list(model, payload, path)

    def request_operation(
        self,
        method: str,
        path: str,
        model: type[OperationResponse] = OperationResponse,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_statuses: set[int] | None = None,
        raise_on_failure: bool | None = None,
        timeout: int | float | tuple[int, int] | None = None,
        **kwargs,
    ) -> OperationResponse:
        if expected_statuses is None:
            expected_statuses = set(range(200, 600))

        resp = self.request(
            method=method,
            path=path,
            params=params,
            headers=headers,
            expected_statuses=expected_statuses,
            timeout=timeout,
            **kwargs,
        )
        payload = self.parse_json_response(resp, path)
        operation = self.parse_model(model, payload, path)
        should_raise = self.raise_on_operation_error
        if raise_on_failure is not None:
            should_raise = raise_on_failure

        if should_raise and (resp.status_code >= 400 or operation.success != 1):
            operation_payload = None
            if self.include_error_payload and isinstance(payload, dict):
                operation_payload = payload
            raise APIOperationError(
                operation.operation,
                operation.error if self.include_operation_error_message else None,
                status_code=resp.status_code,
                payload=operation_payload,
            )
        return operation
