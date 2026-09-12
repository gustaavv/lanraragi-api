import base64
from enum import Enum
from typing import Any

import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Auth(str, Enum):
    """Way the API key is sent to the server.

    Attributes:
        QUERY_PARAM: Send the key as the ``key`` query parameter.
        AUTH_HEADER: Send the key as a base64-encoded ``Authorization`` bearer
            header.
    """

    QUERY_PARAM = "query param"
    AUTH_HEADER = "auth header"


class DictLikeModel(BaseModel):
    """Compatibility helper for endpoints that previously returned dict.

    On top of the usual pydantic attribute access, models deriving from this
    class can be read like a dictionary, so callers written against the older
    ``dict`` based responses keep working.
    """

    def __getitem__(self, key: str):
        """Return the value of the field named ``key``.

        Args:
            key: Name of the field to read.

        Returns:
            The value of the requested field.

        Raises:
            KeyError: If the model has no field named ``key``.
        """
        data = self.model_dump()
        if key not in data:
            raise KeyError(key)
        return data[key]

    def get(self, key: str, default=None):
        """Return the value of the field named ``key``, or a default.

        Args:
            key: Name of the field to read.
            default: Value returned when the field does not exist. Defaults to
                None.

        Returns:
            The value of the requested field, or ``default``.
        """
        return self.model_dump().get(key, default)

    def keys(self):
        """Return the names of all fields of this model.

        Returns:
            A view of the field names.
        """
        return self.model_dump().keys()

    def items(self):
        """Return all fields of this model as name/value pairs.

        Returns:
            A view of ``(name, value)`` pairs.
        """
        return self.model_dump().items()


class OperationResponse(DictLikeModel):
    """Result of an operation endpoint.

    Attributes:
        operation: Name of the operation.
        error: Error message, if the operation failed.
        successMessage: Success message, if the server sent one.
        success: 1 if the operation was successful, else 0.
    """

    model_config = ConfigDict(extra="allow")

    operation: str = Field(...)
    error: str | None = Field(default=None)
    successMessage: str | None = Field(default=None)
    success: int = Field(...)


class MinionJobResponse(OperationResponse):
    """Result of an operation that queued a Minion job.

    Attributes:
        job: ID of the queued Minion job, if one was queued.
    """

    job: int | None = Field(default=None)


class APIError(Exception):
    """Base exception for all API client errors."""


class APIRequestError(APIError):
    """Raised when a request cannot be sent to the server.

    It covers transport level failures such as a refused connection or a
    timeout. HTTP error statuses are reported through ``APIHttpError`` instead.
    The message names the class of the underlying ``requests`` exception when
    one is available.

    Attributes:
        url: Absolute URL the request was sent to.
    """

    def __init__(self, url: str, error_type: str | None = None):
        suffix = f" ({error_type})" if error_type else ""
        super().__init__(f"Request to {url} failed{suffix}")
        self.url = url


class APIHttpError(APIError):
    """Raised when the server answers with an unexpected status code.

    Attributes:
        status_code: HTTP status code returned by the server.
        url: Absolute URL the request was sent to.
    """

    def __init__(self, status_code: int, url: str):
        super().__init__(f"HTTP {status_code} for {url}")
        self.status_code = status_code
        self.url = url


class APIResponseDecodeError(APIError):
    """Raised when a response body cannot be turned into the expected model.

    It is raised for a body that is not valid JSON for a JSON endpoint, and for
    a JSON payload that does not match the pydantic model of the endpoint.

    Attributes:
        url: Absolute URL the request was sent to.
    """

    def __init__(self, url: str, message: str):
        super().__init__(f"Failed to parse response from {url}: {message}")
        self.url = url


class APIOperationError(APIError):
    """Raised when an operation endpoint reports a failure.

    Only raised when raising is enabled, either through the client-level
    ``raise_on_operation_error`` setting or through the ``raise_on_failure``
    argument of a single call. Otherwise the failed operation is returned to the
    caller like any other result.

    Attributes:
        operation: Name of the operation reported by the server.
        message: Error message reported by the server, if it was kept.
        status_code: HTTP status code of the response, if one was returned.
        payload: Raw response payload, if the client was configured to keep it.
    """

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
    """Base class for every API section, handling transport and errors.

    Subclasses expose one method per endpoint. Those methods build their request
    through the ``request_*`` helpers below, which send the call and decode the
    payload into pydantic models.

    Args:
        server: Base URL of the LANraragi server, with or without a trailing
            slash.
        key: API key sent with every request. Defaults to None, which sends no
            credentials.
        auth_way: How the API key is transmitted. Defaults to
            ``Auth.AUTH_HEADER``.
        timeout: Timeout applied to every request, either a single value or a
            ``(connect, read)`` pair. Defaults to None, meaning no timeout.
        include_error_payload: Whether ``APIOperationError`` carries the raw
            response payload. Defaults to False.
        include_operation_error_message: Whether ``APIOperationError`` carries
            the error message reported by the server. Defaults to True.
        raise_on_operation_error: Whether a failed operation raises
            ``APIOperationError`` instead of being returned to the caller.
            Defaults to False.
        default_headers: Extra headers sent with every request. Defaults to
            None, which sends no extra headers.
        default_params: Extra query parameters sent with every request.
            Defaults to None, which sends no extra parameters.

    Raises:
        APIRequestError: From any endpoint method, when a request cannot be sent
            to the server because of a connection failure or a timeout.
    """

    def __init__(
        self,
        server: str,
        key: str | None = None,
        auth_way: Auth = Auth.AUTH_HEADER,
        timeout: float | tuple[int, int] | None = None,
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
        self.server = self.server.removesuffix("/")
        self.default_headers = dict(default_headers)
        self.default_params = dict(default_params)

        if key:
            if auth_way == Auth.QUERY_PARAM:
                self.default_params["key"] = self.key
            elif auth_way == Auth.AUTH_HEADER:
                base64_key = base64.b64encode(self.key.encode("utf-8")).decode("utf-8")
                self.default_headers["Authorization"] = f"Bearer {base64_key}"

    def build_headers(self, headers=None):
        """Merge the headers of a single request into the default headers.

        Headers of the request win over default headers of the same name, so a
        caller can override the authorization header for one call.

        Args:
            headers: Headers of the request. Defaults to None, which sends the
                default headers only.

        Returns:
            dict: Headers to send, defaults included.
        """
        if headers is None:
            headers = {}
        merged = dict(headers)
        for k in self.default_headers:
            if k in merged:
                continue
            merged[k] = self.default_headers[k]
        return merged

    def build_params(self, params=None):
        """Merge the query parameters of a single request into the defaults.

        Parameters of the request win over default parameters of the same name.

        Args:
            params: Query parameters of the request. Defaults to None, which
                sends the default parameters only.

        Returns:
            dict: Query parameters to send, defaults included.
        """
        if params is None:
            params = {}
        merged = dict(params)
        for k in self.default_params:
            if k in merged:
                continue
            merged[k] = self.default_params[k]
        return merged

    def _to_url(self, path: str) -> str:
        """Build the absolute URL of a request from its path.

        Args:
            path: Path of the request, with or without a leading slash.

        Returns:
            str: Absolute URL of the request.

        Raises:
            ValueError: If ``path`` is an absolute URL, or carries a query
                string or fragment.
        """
        if path.startswith(("http://", "https://")):
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
        timeout: float | tuple[int, int] | None = None,
        **kwargs,
    ) -> requests.Response:
        """Send an HTTP request and return the raw response.

        Args:
            method: HTTP method to use.
            path: Path of the request.
            params: Query parameters for this request. Defaults to None.
            headers: Headers for this request. Defaults to None.
            expected_statuses: Status codes considered a success. Defaults to
                None, which accepts every 2xx status.
            timeout: Timeout for this request, overriding the client timeout.
                Defaults to None, which uses the client timeout.
            **kwargs: Extra arguments forwarded to ``requests.request``, such as
                ``data``, ``json``, ``files`` or ``stream``.

        Returns:
            requests.Response: Response returned by the server.

        Raises:
            APIRequestError: If the request cannot be sent to the server.
            APIHttpError: If the status code of the response is not part of
                ``expected_statuses``.
        """
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
        """Decode the body of a response as JSON.

        Args:
            response: Response to decode.
            path: Path of the request, used in error messages.

        Returns:
            The decoded JSON payload.

        Raises:
            APIResponseDecodeError: If the body is not valid JSON.
        """
        url = self._to_url(path)
        try:
            return response.json()
        except ValueError as exc:
            raise APIResponseDecodeError(url, str(exc)) from exc

    def parse_model(self, model: type[BaseModel], payload: Any, path: str):
        """Validate a decoded payload against a pydantic model.

        Args:
            model: Model to validate the payload with.
            payload: Decoded JSON payload.
            path: Path of the request, used in error messages.

        Returns:
            BaseModel: Instance of ``model`` built from ``payload``.

        Raises:
            APIResponseDecodeError: If ``payload`` does not match ``model``.
        """
        url = self._to_url(path)
        try:
            return model.model_validate(payload)
        except ValidationError as exc:
            raise APIResponseDecodeError(url, str(exc)) from exc

    def parse_model_list(self, model: type[BaseModel], payload: Any, path: str):
        """Validate a decoded payload as a list of a pydantic model.

        Args:
            model: Model to validate every item of the payload with.
            payload: Decoded JSON payload, expected to be a list.
            path: Path of the request, used in error messages.

        Returns:
            list[BaseModel]: One instance of ``model`` per item.

        Raises:
            APIResponseDecodeError: If ``payload`` is not a list, or if any item
                does not match ``model``.
        """
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
        timeout: float | tuple[int, int] | None = None,
        **kwargs,
    ):
        """Send a request and decode its body as JSON.

        Args:
            method: HTTP method to use.
            path: Path of the request.
            params: Query parameters for this request. Defaults to None.
            headers: Headers for this request. Defaults to None.
            expected_statuses: Status codes considered a success. Defaults to
                None, which accepts every 2xx status.
            timeout: Timeout for this request, overriding the client timeout.
                Defaults to None, which uses the client timeout.
            **kwargs: Extra arguments forwarded to ``requests.request``.

        Returns:
            The decoded JSON payload.

        Raises:
            APIRequestError: If the request cannot be sent to the server.
            APIHttpError: If the status code of the response is not part of
                ``expected_statuses``.
            APIResponseDecodeError: If the body is not valid JSON.
        """
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
        timeout: float | tuple[int, int] | None = None,
        **kwargs,
    ):
        """Send a request and validate its JSON body against a model.

        Args:
            method: HTTP method to use.
            path: Path of the request.
            model: Model to validate the body with.
            params: Query parameters for this request. Defaults to None.
            headers: Headers for this request. Defaults to None.
            expected_statuses: Status codes considered a success. Defaults to
                None, which accepts every 2xx status.
            timeout: Timeout for this request, overriding the client timeout.
                Defaults to None, which uses the client timeout.
            **kwargs: Extra arguments forwarded to ``requests.request``.

        Returns:
            BaseModel: Instance of ``model`` built from the response body.

        Raises:
            APIRequestError: If the request cannot be sent to the server.
            APIHttpError: If the status code of the response is not part of
                ``expected_statuses``.
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``model``.
        """
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
        timeout: float | tuple[int, int] | None = None,
        **kwargs,
    ):
        """Send a request and validate its JSON body as a list of a model.

        Args:
            method: HTTP method to use.
            path: Path of the request.
            model: Model to validate every item of the body with.
            params: Query parameters for this request. Defaults to None.
            headers: Headers for this request. Defaults to None.
            expected_statuses: Status codes considered a success. Defaults to
                None, which accepts every 2xx status.
            timeout: Timeout for this request, overriding the client timeout.
                Defaults to None, which uses the client timeout.
            **kwargs: Extra arguments forwarded to ``requests.request``.

        Returns:
            list[BaseModel]: One instance of ``model`` per item of the body.

        Raises:
            APIRequestError: If the request cannot be sent to the server.
            APIHttpError: If the status code of the response is not part of
                ``expected_statuses``.
            APIResponseDecodeError: If the body is not a list of objects
                matching ``model``.
        """
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
        timeout: float | tuple[int, int] | None = None,
        **kwargs,
    ) -> OperationResponse:
        """Send a request whose body reports the result of an operation.

        The server reports most operation failures inside the body, through the
        ``success`` field, rather than through the status code. Every status
        from 200 to 599 is therefore accepted by default, and a failed
        operation is only turned into an exception when raising is enabled.

        Args:
            method: HTTP method to use.
            path: Path of the request.
            model: Model to validate the body with. Defaults to
                ``OperationResponse``.
            params: Query parameters for this request. Defaults to None.
            headers: Headers for this request. Defaults to None.
            expected_statuses: Status codes considered a success. Defaults to
                None, which accepts every status from 200 to 599.
            raise_on_failure: Whether to raise on a failed operation, overriding
                the ``raise_on_operation_error`` setting of the client. Defaults
                to None, which keeps the setting of the client.
            timeout: Timeout for this request, overriding the client timeout.
                Defaults to None, which uses the client timeout.
            **kwargs: Extra arguments forwarded to ``requests.request``.

        Returns:
            OperationResponse: Instance of ``model`` built from the response
                body.

        Raises:
            APIRequestError: If the request cannot be sent to the server.
            APIHttpError: If the status code of the response is not part of
                ``expected_statuses``.
            APIResponseDecodeError: If the body is not valid JSON, or does not
                match ``model``.
            APIOperationError: If the operation failed and raising is enabled.
        """
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
