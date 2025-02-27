__all__ = ["HubAPIError"]

import typing as t
from enum import Enum

import typing_extensions as te

import uuid

import httpx
from pydantic import BaseModel, Field, ValidationError, ConfigDict

from flame_hub.flow import PasswordAuth, RobotAuth

# base resource type which assumes BaseModel as the base class
ResourceT = t.TypeVar("ResourceT", bound=BaseModel)


# structural subtype which expects a BaseModel to have an id property
class UuidModel(t.Protocol[ResourceT]):
    id: uuid.UUID


# union which encompasses all types where a UUID can be extracted from
UuidIdentifiable = t.Union[UuidModel, uuid.UUID, str]


def obtain_uuid_from(uuid_identifiable: UuidIdentifiable) -> uuid.UUID:
    """Extract a UUID from a model containing an ID property, a string or a UUID object."""
    if isinstance(uuid_identifiable, BaseModel):
        uuid_identifiable = getattr(uuid_identifiable, "id")

    if isinstance(uuid_identifiable, str):
        return uuid.UUID(uuid_identifiable)

    if isinstance(uuid_identifiable, uuid.UUID):
        return uuid_identifiable

    raise ValueError(f"{uuid_identifiable} cannot be converted into a UUID")


# resource for meta information on list responses
class ResourceListMeta(BaseModel):
    total: int


# resource for list responses
class ResourceList(BaseModel, t.Generic[ResourceT]):
    data: list[ResourceT]
    meta: ResourceListMeta


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="allow")  # extra properties may be available
    status_code: t.Annotated[int, Field(validation_alias="statusCode")]
    code: str
    message: str


class HubAPIError(httpx.HTTPError):
    def __init__(self, message: str, request: httpx.Request, error: ErrorResponse = None) -> None:
        super().__init__(message)
        self._request = request
        self.error_response = error


def new_error_from_response(r: httpx.Response):
    error_response = None
    error_message = f"received status code {r.status_code}"

    try:
        error_response = ErrorResponse(**r.json())
        error_message = f"received status code {error_response.status_code} ({error_response.code}): "

        if error_response.message.strip() == "":
            error_message += "no error message present"
        else:
            error_message += error_response.message
    except ValidationError:
        # quietly dismiss this error
        pass

    return HubAPIError(error_message, r.request, error_response)


class PageParams(te.TypedDict, total=False):
    limit: int
    offset: int


_DEFAULT_PAGE_PARAMS: PageParams = {"limit": 50, "offset": 0}


class FilterOperator(str, Enum):
    eq = "="
    neq = "!"
    like = "~"
    lt = "<"
    le = "<="
    gt = ">"
    ge = ">="


_ALL_FILTER_OPERATOR_STRINGS = {f.value for f in FilterOperator}

FilterParams = dict[str, t.Union[t.Any, tuple[FilterOperator, t.Any]]]


def build_page_params(page_params: PageParams = None, default_page_params: PageParams = None):
    # use empty dict if None is provided
    if default_page_params is None:
        default_page_params = _DEFAULT_PAGE_PARAMS

    if page_params is None:
        page_params = {}

    # overwrite default values with user-defined ones
    page_params = default_page_params | page_params

    return {f"page[{k}]": v for k, v in page_params.items()}


def build_filter_params(filter_params: FilterParams = None):
    if filter_params is None:
        filter_params = {}

    query_params = {}

    for property_name, property_filter in filter_params.items():
        query_param_name = f"filter[{property_name}]"

        if not isinstance(property_filter, tuple):  # t.Any -> (FilterOperator, t.Any)
            property_filter = (FilterOperator.eq, property_filter)

        query_filter_op, query_filter_value = property_filter  # (FilterOperator | str, t.Any)

        if isinstance(query_filter_op, FilterOperator):  # FilterOperator -> str
            query_filter_op = query_filter_op.value

        # equals is replaced with an empty string
        if query_filter_op == "=":
            query_filter_op = ""

        query_params[query_param_name] = f"{query_filter_op}{query_filter_value}"

    return query_params


class BaseClient(object):
    def __init__(
        self, base_url: str = None, client: httpx.Client = None, auth: t.Union[PasswordAuth, RobotAuth] = None
    ):
        self._client = client or httpx.Client(auth=auth, base_url=base_url)

    def _get_all_resources(self, resource_type: type[ResourceT], *path: str):
        return self._find_all_resources(resource_type, None, None, *path)

    def _find_all_resources(
        self,
        resource_type: type[ResourceT],
        page_params: PageParams = None,
        filter_params: FilterParams = None,
        *path: str,
    ):
        # merge processed filter and page params
        request_params = build_page_params(page_params) | build_filter_params(filter_params)
        r = self._client.get("/".join(path), params=request_params)

        if r.status_code != httpx.codes.OK.value:
            raise new_error_from_response(r)

        return ResourceList[resource_type](**r.json())

    def _create_resource(self, resource_type: type[ResourceT], resource: BaseModel, *path: str) -> ResourceT:
        r = self._client.post(
            "/".join(path),
            json=resource.model_dump(mode="json"),
        )

        if r.status_code != httpx.codes.CREATED.value:
            raise new_error_from_response(r)

        return resource_type(**r.json())

    def _get_single_resource(
        self, resource_type: type[ResourceT], resource_id: UuidIdentifiable, *path: str
    ) -> ResourceT | None:
        path = (*path, str(obtain_uuid_from(resource_id)))
        r = self._client.get("/".join(path))

        if r.status_code == httpx.codes.NOT_FOUND.value:
            return None

        if r.status_code != httpx.codes.OK.value:
            raise new_error_from_response(r)

        return resource_type(**r.json())

    def _update_resource(
        self,
        resource_type: type[ResourceT],
        resource_id: UuidIdentifiable,
        resource: BaseModel,
        *path: str,
    ) -> ResourceT:
        path = (*path, str(obtain_uuid_from(resource_id)))

        r = self._client.post(
            "/".join(path),
            json=resource.model_dump(mode="json", exclude_none=True),
        )

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_error_from_response(r)

        return resource_type(**r.json())

    def _delete_resource(self, resource_id: t.Union[UuidModel, str, uuid.UUID], *path: str):
        path = (*path, str(obtain_uuid_from(resource_id)))

        r = self._client.delete("/".join(path))

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_error_from_response(r)
