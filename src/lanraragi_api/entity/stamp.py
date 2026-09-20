from pydantic import BaseModel, Field

from lanraragi_api.entity.base import DictLikeModel, OperationResponse


class StampsData(BaseModel):
    """JSON object for the Stamp model.

    Attributes:
        id: ID of the stamp.
        position: Position of the stamp in the page in normalized coordinates
            (0-100).
        content: Text of the stamp.
    """

    id: str | None = Field(default=None)
    position: str = Field(...)
    content: str = Field(...)


class StampsResponse(DictLikeModel):
    """Response listing the pages that contain at least one stamp.

    Attributes:
        result: Page indices of the archive that contain a stamp.
    """

    result: list[str] = Field(default_factory=list)


class AddStampResponse(OperationResponse):
    """Result of the operation that adds a stamp to a page.

    Attributes:
        stamp_id: ID of the created stamp.
    """

    stamp_id: str | None = Field(default=None)
