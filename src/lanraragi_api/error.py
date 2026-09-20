from typing import Any


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
        self.url: str = url


class APIHttpError(APIError):
    """Raised when the server answers with an unexpected status code.

    Attributes:
        status_code: HTTP status code returned by the server.
        url: Absolute URL the request was sent to.
    """

    def __init__(self, status_code: int, url: str):
        super().__init__(f"HTTP {status_code} for {url}")
        self.status_code: int = status_code
        self.url: str = url


class APIResponseDecodeError(APIError):
    """Raised when a response body cannot be turned into the expected model.

    It is raised for a body that is not valid JSON for a JSON endpoint, and for
    a JSON payload that does not match the pydantic model of the endpoint.

    Attributes:
        url: Absolute URL the request was sent to.
    """

    def __init__(self, url: str, message: str):
        super().__init__(f"Failed to parse response from {url}: {message}")
        self.url: str = url


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
        self.operation: str = operation
        self.message: str | None = message
        self.status_code: int | None = status_code
        self.payload: dict[str, Any] | None = payload
