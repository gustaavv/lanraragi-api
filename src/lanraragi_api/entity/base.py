from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


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

    def get(self, key: str, default: None = None):
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

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

    operation: str = Field(...)
    error: str | None = Field(default=None)
    successMessage: str | None = Field(default=None)
    success: int = Field(...)
