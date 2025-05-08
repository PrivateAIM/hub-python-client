import typing as t
import uuid
from collections.abc import Iterable
from enum import Enum

import httpx
import typing_extensions as te
from pydantic import BaseModel, model_validator, ValidatorFunctionWrapHandler, ValidationError

from flame_hub._exceptions import new_hub_api_error_from_response
from flame_hub._auth_flows import PasswordAuth, RobotAuth

# sentinel to mark parameters as unset (as opposed to using None)
_UNSET = object()


class UpdateModel(BaseModel):
    """Base class for models where properties can be unset when passed into the class constructor.
    Before validation, this class prunes all properties which have the unset sentinel assigned to them.
    This way, they are considered unset by the base model."""

    @model_validator(mode="before")
    @classmethod
    def strip_unset_properties(cls, data: t.Any) -> t.Any:
        if isinstance(data, dict):
            props_to_delete = [k for k, v in data.items() if v == _UNSET]

            for prop in props_to_delete:
                del data[prop]

        return data


# base resource type which assumes BaseModel as the base class
ResourceT = t.TypeVar("ResourceT", bound=BaseModel)


# structural subtype which expects a BaseModel to have an id property
class UuidModel(t.Protocol[ResourceT]):
    id: uuid.UUID


# union which encompasses all types where a UUID can be extracted from
UuidIdentifiable = UuidModel | uuid.UUID | str


def obtain_uuid_from(uuid_identifiable: UuidIdentifiable) -> uuid.UUID:
    """Extract a UUID from a model containing an ID property, a string or a UUID object."""
    if isinstance(uuid_identifiable, BaseModel):
        uuid_identifiable = getattr(uuid_identifiable, "id")

    if isinstance(uuid_identifiable, str):
        return uuid.UUID(uuid_identifiable)

    if isinstance(uuid_identifiable, uuid.UUID):
        return uuid_identifiable

    raise ValueError(f"{uuid_identifiable} cannot be converted into a UUID")


def uuid_validator(value: t.Any, handler: ValidatorFunctionWrapHandler) -> uuid.UUID:
    """Callable for Pydantic's wrap validators to cast resource type instances and strings to UUIDs."""
    try:
        return handler(value)
    except ValidationError as e:
        try:
            return obtain_uuid_from(value)
        except ValueError:
            raise e


# resource for meta information on list responses
class ResourceListMeta(BaseModel):
    total: int


# resource for list responses
class ResourceList(BaseModel, t.Generic[ResourceT]):
    data: list[ResourceT]
    meta: ResourceListMeta


class SortParams(te.TypedDict, total=False):
    by: str
    order: t.Literal["ascending", "descending"]


# dict shape for specifying limit and offset for paginated queries
class PageParams(te.TypedDict, total=False):
    limit: int
    offset: int


# default limit and offset for paginated requests
_DEFAULT_PAGE_PARAMS: PageParams = {"limit": 50, "offset": 0}


# operators that are supported by the Hub API for filtering requests
class FilterOperator(str, Enum):
    eq = "="
    neq = "!"
    like = "~"
    lt = "<"
    le = "<="
    gt = ">"
    ge = ">="


FilterParams = dict[str, t.Any | tuple[FilterOperator, t.Any]]
IncludeParams = str | Iterable[str]
FieldParams = str | Iterable[str]


class FindAllKwargs(te.TypedDict, total=False):
    filter: FilterParams | None
    page: PageParams | None
    sort: SortParams | None


class ClientKwargs(te.TypedDict, total=False):
    client: httpx.Client | None


def build_page_params(page_params: PageParams = None, default_page_params: PageParams = None) -> dict:
    """Build a dictionary of query parameters based on provided pagination parameters."""
    # use empty dict if None is provided
    if default_page_params is None:
        default_page_params = _DEFAULT_PAGE_PARAMS

    if page_params is None:
        page_params = {}

    # overwrite default values with user-defined ones
    page_params = default_page_params | page_params

    return {f"page[{k}]": v for k, v in page_params.items()}


def build_filter_params(filter_params: FilterParams = None) -> dict:
    """Build a dictionary of query parameters based on provided filter parameters."""
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


def build_sort_params(sort_params: SortParams = None) -> dict:
    if sort_params is None:
        sort_params = {}

    query_params = {}

    # check if a property has been specified
    param_sort_by = sort_params.get("by", None)

    if param_sort_by is not None:
        # default sort order should be ascending
        param_sort_order = sort_params.get("order", "ascending")
        # property gets a "-" prepended if sorting in descending order
        param_sort_prefix = "-" if param_sort_order == "descending" else ""
        # construct the actual query params
        query_params["sort"] = param_sort_prefix + param_sort_by

    return query_params


def build_include_params(include_params: IncludeParams = None) -> dict:
    if include_params is None:
        include_params = ()  # empty tuple

    if isinstance(include_params, str):
        include_params = (include_params,)  # coalesce into tuple

    # unravel iterable and merge into tuple
    include_params = tuple(p for p in include_params)

    if len(include_params) == 0:
        return {}

    return {"include": ",".join(include_params)}


def build_field_params(field_params: FieldParams = None) -> dict:
    if field_params is None:
        field_params = ()  # empty tuple

    if isinstance(field_params, str):
        field_params = (field_params,)  # coalesce into tuple

    # unravel iterable and merge into tuple
    field_params = tuple(p for p in field_params)

    # only allow the addition of fields
    field_params = tuple(f"+{p}" for p in field_params)

    if len(field_params) == 0:
        return {}

    return {"fields": ",".join(field_params)}


def convert_path(path: Iterable[str | UuidIdentifiable]) -> tuple[str, ...]:
    path_parts = []

    for p in path:
        if isinstance(p, str):
            path_parts.append(p)
        else:
            path_parts.append(str(obtain_uuid_from(p)))

    return tuple(path_parts)


class BaseClient(object):
    def __init__(self, base_url: str = None, auth: PasswordAuth | RobotAuth = None, **kwargs: te.Unpack[ClientKwargs]):
        client = kwargs.get("client", None)
        self._client = client or httpx.Client(auth=auth, base_url=base_url)

    def _get_all_resources(
        self,
        resource_type: type[ResourceT],
        *path: str,
        fields: FieldParams = None,
        include: IncludeParams = None,
    ) -> list[ResourceT]:
        """Retrieve all resources of a certain type at the specified path.
        Default pagination parameters are applied."""
        return self._find_all_resources(resource_type, *path, fields=fields, include=include)

    def _find_all_resources(
        self,
        resource_type: type[ResourceT],
        *path: str,
        fields: FieldParams = None,
        include: IncludeParams = None,
        **params: te.Unpack[FindAllKwargs],
    ) -> list[ResourceT]:
        """Find all resources of a certain type at the specified path.
        Custom pagination and filter parameters can be applied."""
        # merge processed filter and page params
        page_params = params.get("page", None)
        filter_params = params.get("filter", None)
        sort_params = params.get("sort", None)

        request_params = (
            build_page_params(page_params)
            | build_filter_params(filter_params)
            | build_sort_params(sort_params)
            | build_include_params(include)
            | build_field_params(fields)
        )

        r = self._client.get("/".join(path), params=request_params)

        if r.status_code != httpx.codes.OK.value:
            raise new_hub_api_error_from_response(r)

        return ResourceList[resource_type](**r.json()).data

    def _create_resource(self, resource_type: type[ResourceT], resource: BaseModel, *path: str) -> ResourceT:
        """Create a resource of a certain type at the specified path."""
        r = self._client.post(
            "/".join(path),
            json=resource.model_dump(mode="json"),
        )

        if r.status_code != httpx.codes.CREATED.value:
            raise new_hub_api_error_from_response(r)

        return resource_type(**r.json())

    def _get_single_resource(
        self,
        resource_type: type[ResourceT],
        *path: str | UuidIdentifiable,
        fields: FieldParams = None,
        include: IncludeParams = None,
    ) -> ResourceT | None:
        """Get a resource of a certain type at the specified path."""
        request_params = build_field_params(fields) | build_include_params(include)

        r = self._client.get("/".join(convert_path(path)), params=request_params)

        if r.status_code == httpx.codes.NOT_FOUND.value:
            return None

        if r.status_code != httpx.codes.OK.value:
            raise new_hub_api_error_from_response(r)

        return resource_type(**r.json())

    def _update_resource(
        self,
        resource_type: type[ResourceT],
        resource: BaseModel,
        *path: str | UuidIdentifiable,
    ) -> ResourceT:
        """Update a resource of a certain type at the specified path."""
        r = self._client.post(
            "/".join(convert_path(path)),
            json=resource.model_dump(mode="json", exclude_none=False, exclude_unset=True),
        )

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_hub_api_error_from_response(r)

        return resource_type(**r.json())

    def _delete_resource(self, *path: str | UuidIdentifiable):
        """Delete a resource of a certain type at the specified path."""
        r = self._client.delete("/".join(convert_path(path)))

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_hub_api_error_from_response(r)
