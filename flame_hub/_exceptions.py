import typing as t
from json import JSONDecodeError

import httpx
from pydantic import ValidationError, BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    """Configuration so that extra properties may be available."""
    status_code: t.Annotated[int, Field(validation_alias="statusCode")]
    """The status code of the response. This attribute is mapped to the :python:`"statusCode"` field of the response."""
    code: str
    """Written equivalent for ``status_code``."""
    message: str
    """The error message."""


class HubAPIError(httpx.HTTPError):
    """Base error for any unexpected response returned by the Hub API.

    Parameters
    ----------
    message : :py:class:`str`
        The error message.
    request : :py:class:`httpx.Request`
        The request which caused the error.
    error : :py:class:`.ErrorResponse`, optional
        Parsed response to enrich the error with additional information.

    See Also
    --------
    :py:exc:`.HubAPIError`, :py:func:`.new_hub_api_error_from_response`
    """

    def __init__(self, message: str, request: httpx.Request, error: ErrorResponse = None) -> None:
        super().__init__(message)
        self._request = request
        self.error_response = error


def new_hub_api_error_from_response(r: httpx.Response) -> HubAPIError:
    """Create a new :py:exc:`.HubAPIError` from a response.

    If present, this function will use the response body to add context to the error message. The response body is
    parsed by the :py:class:`.ErrorResponse` model and is available using the ``error_response`` property of the
    returned error.

    Parameters
    ----------
    r : :py:class:`httpx.Response`
        The response to create a new :py:exc:`.HubAPIError` for.

    Returns
    -------
    :py:exc:`.HubAPIError`
        A new :py:class:`.HubAPIError` instance which is enriched with information from the response ``r``.

    See Also
    --------
    :py:exc:`.HubAPIError`, :py:class:`.ErrorResponse`
    """
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
