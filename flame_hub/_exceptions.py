import typing as t
from json import JSONDecodeError

import httpx
from pydantic import ValidationError, BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="allow")  # extra properties may be available
    status_code: t.Annotated[int, Field(validation_alias="statusCode")]
    code: str
    message: str


class HubAPIError(httpx.HTTPError):
    """Base error for any unexpected response returned by the Hub API."""

    def __init__(self, message: str, request: httpx.Request, error: ErrorResponse = None) -> None:
        super().__init__(message)
        self._request = request
        self.error_response = error


def new_hub_api_error_from_response(r: httpx.Response) -> HubAPIError:
    """Create a new error from a response.
    If present, this function will use the response body to add context to the error message.
    The parsed response body is available using the error_response property of the returned error."""
    error_response = None
    error_message = f"received status code {r.status_code}"

    try:
        error_response = ErrorResponse(**r.json())
        error_message = f"received status code {error_response.status_code} ({error_response.code}): "

        if error_response.message.strip() == "":
            error_message += "no error message present"
        else:
            error_message += error_response.message
    except (ValidationError, JSONDecodeError):
        # quietly dismiss this error
        pass

    return HubAPIError(error_message, r.request, error_response)
