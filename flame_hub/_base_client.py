from __future__ import annotations
import typing as t
import uuid
from collections.abc import Iterable
from enum import Enum

import httpx
import typing_extensions as te
from pydantic import BaseModel, model_validator, ValidatorFunctionWrapHandler, ValidationError, ConfigDict

from flame_hub._exceptions import new_hub_api_error_from_response
from flame_hub._auth_flows import PasswordAuth, RobotAuth


class _UNSET(object):
    """Sentinel to mark parameters as unset as opposed to using :any:`None`."""


class UpdateModel(BaseModel):
    """Base class for models that shall validate responses for requests that update resources.

    This base class is needed so that properties can be unset when passed into the class constructor. Before validation,
    this class prunes all properties which have the :py:class:`._UNSET` sentinel assigned to them. This way, they are
    considered unset by the base model.
    """

    @model_validator(mode="before")
    @classmethod
    def strip_unset_properties(cls, data: t.Any) -> t.Any:
        """Strips unset properties before validating property values.

        To strip all properties that have the :py:class:`._UNSET` sentinel assigned to them, this class method is
        decorated with Pydantic's model validator :py:func:`pydantic.model_validator` with :python:`mode="before"` so
        that properties are stripped before validation to avoid validation errors. If ``data`` is a dictionary, then its
        keys are property names and values are the corresponding property values.
        """
        if isinstance(data, dict):
            props_to_delete = [k for k, v in data.items() if v == _UNSET]

            for prop in props_to_delete:
                del data[prop]

        return data


ResourceT = t.TypeVar("ResourceT", bound=BaseModel)
"""Base resource type which assumes :py:class:`~pydantic.BaseModel` as the base class."""


class UuidModel(t.Protocol[ResourceT]):
    """Structural subtype which expects a :py:class:`~pydantic.BaseModel` to have an ``id`` attribute."""

    id: uuid.UUID


# union which encompasses all types where a UUID can be extracted from
UuidIdentifiable = UuidModel | uuid.UUID | str


def obtain_uuid_from(uuid_identifiable: UuidIdentifiable) -> uuid.UUID:
    """Extract a :py:class:`~uuid.UUID` from a model containing an ``id`` property, :py:class:`~uuid.UUID` object or a
    string.

    Raises
    ------
    :py:exc:`ValueError`
        If ``uuid_identifiable`` is neither an instance of :py:class:`~pydantic.BaseModel`, :py:class:`str` nor
        :py:class:`~uuid.UUID`.

    See Also
    --------
    :py:type:`.UuidIdentifiable`, :py:class:`.UuidModel`, :py:type:`~flame_hub._base_client.ResourceT`
    """

    if isinstance(uuid_identifiable, BaseModel):
        uuid_identifiable = getattr(uuid_identifiable, "id")

    if isinstance(uuid_identifiable, str):
        return uuid.UUID(uuid_identifiable)

    if isinstance(uuid_identifiable, uuid.UUID):
        return uuid_identifiable

    raise ValueError(f"{uuid_identifiable} cannot be converted into a UUID")


def uuid_validator(value: t.Any, handler: ValidatorFunctionWrapHandler) -> uuid.UUID:
    """Callable for Pydantic's wrap validator :py:class:`~pydantic.WrapValidator` to cast resource type instances and
    strings to :py:class:`~uuid.UUID`.

    This function tries to validate ``value`` with ``handler`` and if this raises a validation error, it tries to cast
    ``value`` to a UUID with :py:func:`~flame_hub._base_client.obtain_from_uuid`.

    Raises
    ------
    :py:exc:`~pydantic_core.ValidationError`
        If :py:func:`~flame_hub._base_client.obtain_from_uuid` raises a :py:exc:`ValueError`, the original
        :py:exc:`~pydantic_core.ValidationError` is raised.

    See Also
    --------
    :py:type:`.UuidIdentifiable`, :py:class:`.UuidModel`, :py:type:`~flame_hub._base_client.ResourceT`,\
    :py:func:`~flame_hub._base_client.obtain_from_uuid`
    """
    try:
        return handler(value)
    except ValidationError as e:
        try:
            return obtain_uuid_from(value)
        except ValueError:
            raise e


class ResourceListMeta(BaseModel):
    """Resource for meta information on list responses.

    See Also
    --------
    :py:meth:`._get_all_resources`, :py:meth:`._find_all_resources`
    """

    model_config = ConfigDict(extra="allow")
    """Based on the type of the request, additional attributes like ``limit`` or ``offset`` may be available."""
    total: int
    """The total amount of records of a specific resource type."""


class ResourceList(BaseModel, t.Generic[ResourceT]):
    """Resource for list responses.

    See Also
    --------
    :py:meth:`._get_all_resources`, :py:meth:`._find_all_resources`
    """

    data: list[ResourceT]
    """Attribute which holds all retrieved resources as a list."""
    meta: ResourceListMeta
    """Attribute which holds meta information about the result and the requested resource type."""


class SortParams(te.TypedDict, total=False):
    """Dict shape for specifying parameters for sorted queries.

    See Also
    --------
    :py:class:`.FindAllKwargs`, :py:meth:`._find_all_resources`
    """

    by: str
    """Name of the attribute to sort by."""
    order: t.Literal["ascending", "descending"]
    """Sort in either ascending or descending order."""


class PageParams(te.TypedDict, total=False):
    """Dict shape for specifying limit and offset for paginated queries.

    See Also
    --------
    :py:class:`.FindAllKwargs`, :py:meth:`._find_all_resources`
    """

    limit: int
    """Amount of returned resources."""
    offset: int
    """Amount of resources to skip before resources are added to the returned list."""


DEFAULT_PAGE_PARAMS: PageParams = {"limit": 50, "offset": 0}
"""Default ``limit`` and ``offset`` for paginated requests."""


class FilterOperator(str, Enum):
    """Operators that are supported by the Hub API for filtering requests.

    See Also
    --------
    :py:type:`~flame_hub.types.FilterParams`, :py:class:`.FindAllKwargs`, :py:meth:`._find_all_resources`
    """

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


class IsField(object):
    """Sentinel to annotate model attributes as optional fields."""


def get_field_names(model: type[ResourceT]) -> tuple[str, ...]:
    """Returns all optional field names for a given model.

    This function traverses a given ``model`` and all of its bases using the method resolution order. While traversing,
    all attributes are checked if they are annotated with the :py:class:`.IsField` sentinel which marks an optional
    field. The names of all annotated attributes are returned as a tuple.

    Parameters
    ----------
    model : :py:class:`type`\\[:py:type:`~flame_hub._base_client.ResourceT`]
        A resource model for which all field names should be retrieved. Note that fields are **not** consequently
        annotated for *Create* and *Update* models due to inheritance.

    Returns
    -------
    :py:class:`tuple`\\[:py:class:`str`, ...]
        Returns a tuple of all attribute names that are annotated with :py:class:`.IsField`.
    """
    fields = []
    for cls in model.mro():
        if not hasattr(cls, "__annotations__"):
            continue
        for name, annotation in cls.__annotations__.items():
            if t.get_origin(annotation) is t.Annotated:
                for metadata in annotation.__metadata__:
                    if metadata is IsField:
                        fields.append(name)
    return tuple(fields)


class FindAllKwargs(te.TypedDict, total=False):
    """Keyword arguments that can be used for finding resources.

    See Also
    --------
    :py:class:`.FilterOperator`, :py:type:`~flame_hub.types.FilterParams`, :py:type:`~flame_hub.types.PageParams`,\
    :py:type:`~flame_hub.types.SortParams`, :py:type:`flame_hub.types.FieldParams`, :py:meth:`._find_all_resources`
    """

    filter: FilterParams | None
    page: PageParams | None
    sort: SortParams | None
    fields: FieldParams | None
    meta: bool


class ClientKwargs(te.TypedDict, total=False):
    """Keyword arguments that can be used to instantiate a client.

    See Also
    --------
    :py:class:`.BaseClient`, :py:class:`.AuthClient`, :py:class:`.CoreClient`, :py:class:`.StorageClient`
    """

    client: httpx.Client | None


class GetKwargs(te.TypedDict, total=False):
    """Keyword arguments that can be used for getting resources.

    See Also
    --------
    :py:type:`~flame_hub.types.FieldParams`
    """

    fields: FieldParams | None
    meta: bool


def build_page_params(page_params: PageParams = None, default_page_params: PageParams = None) -> dict:
    """Build a dictionary of query parameters based on provided pagination parameters."""
    # use empty dict if None is provided
    if default_page_params is None:
        default_page_params = DEFAULT_PAGE_PARAMS

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
    """The base class for other client classes.

    This class implements fundamental methods to get, find, create, update and delete resources from a FLAME Hub
    instance. If the default instantiation of the internally used HTTP client should be bypassed, pass your own
    :py:class:`httpx.Client` via ``**kwargs`` to the class.

    Parameters
    ----------
    base_url : :py:class:`str`
        Base URL of the Hub service.
    auth : :py:class:`.PasswordAuth` | :py:class:`.RobotAuth`, optional
        Authenticator which is used to authenticate the client at the FLAME Hub instance. Defaults to :any:`None`.
    **kwargs : :py:class:`Unpack`\\[:py:class:`~flame_hub._base_client.ClientKwargs`]
        Currently used to pass an already instantiated HTTP client via the ``client`` keyword argument to bypass the
        default instantiation. This overrides ``base_url`` and ``auth``.

    See Also
    --------
    :py:class:`.AuthClient`, :py:class:`.CoreClient`, :py:class:`.StorageClient`
    """

    def __init__(self, base_url: str, auth: PasswordAuth | RobotAuth = None, **kwargs: te.Unpack[ClientKwargs]):
        client = kwargs.get("client", None)
        self._client = client or httpx.Client(auth=auth, base_url=base_url)

    def _get_all_resources(
        self,
        resource_type: type[ResourceT],
        *path: str,
        include: IncludeParams = None,
        **params: te.Unpack[GetKwargs],
    ) -> list[ResourceT] | tuple[list[ResourceT], ResourceListMeta]:
        """Retrieve all resources of a certain type at the specified path from the FLAME Hub.

        This method passes its arguments through to :py:meth:`_find_all_resources`. Check the documentation of that
        method for all information.

        See Also
        --------
        :py:meth:`_find_all_resources`, :py:meth:`_get_single_resource`

        Notes
        -----
        Default pagination parameters are applied as explained in the return section of :py:meth:`_find_all_resources`.
        """

        return self._find_all_resources(resource_type, *path, include=include, **params)

    def _find_all_resources(
        self,
        resource_type: type[ResourceT],
        *path: str,
        include: IncludeParams = None,
        **params: te.Unpack[FindAllKwargs],
    ) -> list[ResourceT] | tuple[list[ResourceT], ResourceListMeta]:
        """Find all resources at the specified path on the FLAME Hub that match certain criteria.

        This method accesses the endpoint ``*path`` and returns all resources of type ``resource_type`` that match
        certain criteria defined in ``**params``. Further fields and nested resources can be added to responses via the
        ``fields`` and ``include`` argument. Meta information can be returned with the ``meta`` argument.

        Parameters
        ----------
        resource_type : :py:class:`type`\\[:py:type:`~flame_hub._base_client.ResourceT`]
            A Pydantic subclass used to validate the response from the FLAME Hub. This should be a model that
            validates all attributes a resource can have. In other terms, do not pass one of the models that start with
            *Create* or *Update* since this method performs a ``GET`` request.
        *path : :py:class:`str`
            A string or multiple strings that define the endpoint.
        fields : :py:type:`~flame_hub.types.FieldParams`, optional
            Extend the default resource field selection by explicitly name one or more field names.
        include : :py:type:`~flame_hub.types.IncludeParams`, optional
            Extend the default resource fields by explicitly list resource names to nest in the response. See the
            :doc:`model specifications <models_api>` which resources can be included in other resources.
        **params : :py:obj:`~typing.Unpack` [:py:class:`.FindAllKwargs`]
            Further keyword arguments to define filtering, sorting and pagination conditions, adding optional fields
            to a response and returning meta information.

        Returns
        -------
        :py:class:`list`\\[:py:type:`~flame_hub._base_client.ResourceT`] | :py:class:`tuple`\\[:py:class:`list`\\[:py:type:`~flame_hub._base_client.ResourceT`], :py:class:`.ResourceListMeta`]
            All resources of type ``resource_type`` that match the criteria defined in ``**params``. If no criteria are
            defined, it returns the default paginated resources according to
            :py:const:`~flame_hub._base_client.DEFAULT_PAGE_PARAMS`. If :python:`meta=True`, this method returns meta
            information about the result and the requested resource type as a second value.

        Raises
        ------
        :py:exc:`.HubAPIError`
            If the status code of the response does not match 200.
        :py:exc:`~pydantic_core._pydantic_core.ValidationError`
            If the resources returned by the Hub instance do not validate with the given ``resource_type``.

        See Also
        --------
        :py:meth:`_get_all_resources`, :py:meth:`_get_single_resource`
        """

        # merge processed filter and page params
        page_params = params.get("page", None)
        filter_params = params.get("filter", None)
        sort_params = params.get("sort", None)
        field_params = params.get("fields", None)
        meta = params.get("meta", False)

        request_params = (
            build_page_params(page_params)
            | build_filter_params(filter_params)
            | build_sort_params(sort_params)
            | build_include_params(include)
            | build_field_params(field_params)
        )

        r = self._client.get("/".join(path), params=request_params)

        if r.status_code != httpx.codes.OK.value:
            raise new_hub_api_error_from_response(r)

        resource_list = ResourceList[resource_type](**r.json())

        if meta:
            return resource_list.data, resource_list.meta
        else:
            return resource_list.data

    def _create_resource(self, resource_type: type[ResourceT], resource: BaseModel, *path: str) -> ResourceT:
        """Create a resource of a certain type at the specified path.

        The FLAME Hub responds with the created resource which is then validated with ``resource_type`` and returned by
        this method.

        Parameters
        ----------
        resource_type : :py:class:`type`\\[:py:type:`~flame_hub._base_client.ResourceT`]
            A Pydantic subclass used to validate the response from the FLAME Hub. This should be a model that
            validates all attributes a resource can have. In other terms, do not pass one of the models that start with
            *Create* or *Update* since this method performs a ``GET`` request.
        resource : :py:class:`~pydantic.BaseModel`
            This has to be the corresponding creation model for ``resource_type``. All creation models follow a naming
            convention with a prefixed *Create*. See the :doc:`model specifications <models_api>` for a list of all
            available models.
        *path : :py:class:`str`
            Path to the endpoint where the resource should be created.

        Returns
        -------
        :py:type:`~flame_hub._base_client.ResourceT`
            Validated resource that was just created.

        Raises
        ------
        :py:exc:`.HubAPIError`
            If the status code of the response does not match 201.
        :py:exc:`~pydantic_core._pydantic_core.ValidationError`
            If the resource returned by the Hub instance does not validate with the given ``resource_type``.
        """
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
        include: IncludeParams = None,
        **params: te.Unpack[GetKwargs],
    ) -> ResourceT | None:
        """Get a single resource of a certain type at the specified path.

        This method accesses the endpoint ``*path`` and returns the resource of type ``resource_type``. In contrast to
        :py:meth:`._get_all_resources` ``*path`` must point to one specific resource of the specified type.

        Parameters
        ----------
        resource_type : :py:class:`type`\\[:py:type:`~flame_hub._base_client.ResourceT`]
            A Pydantic subclass used to validate the response from the FLAME Hub. This should be a model that validates
            all attributes a resource can have. In other terms, do not pass one of the models that start with *Create*
            or *Update* since this method performs a ``GET`` request.
        *path : :py:class:`str` | :py:class:`~flame_hub.types.UuidIdentifiable`
            A string or multiple strings that define the endpoint. Since the last component of the path is a UUID of
            a specific resource, it is also possible to pass in an :py:class:`~uuid.UUID` object or a model with an
            ``id`` attribute.
        fields : :py:type:`~flame_hub.types.FieldParams`, optional
            Extend the default resource field selection by explicitly name one or more field names.
        include : :py:type:`~flame_hub.types.IncludeParams`, optional
            Extend the default resource fields by explicitly list resource names to nest in the response. See the
            :doc:`model specifications <models_api>` which resources can be included in other resources.

        Returns
        -------
        :py:type:`~flame_hub._base_client.ResourceT` | :py:obj:`None`
            Returns the resource of type ``resource_type`` found under ``*path``. If there isn't a resource under that
            path, :py:obj:`None` is returned.

        Raises
        ------
        :py:exc:`.HubAPIError`
            If the status code of the response does not match 200 or 404.
        :py:exc:`~pydantic_core._pydantic_core.ValidationError`
            If the resource returned by the Hub instance does not validate with the given ``resource_type``.

        See Also
        --------
        :py:meth:`._get_all_resources`, :py:meth:`._find_all_resources`

        Notes
        -----
        ``meta`` has no relevance for this method.
        """
        field_params = params.get("fields", None)

        request_params = build_field_params(field_params) | build_include_params(include)

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
        """Update a resource of a certain type at the specified path.

        The FLAME Hub responds with the updated resource which is then validated with ``resource_type`` and returned by
        this method.

        Parameters
        ----------
        resource_type : :py:class:`type`\\[:py:type:`~flame_hub._base_client.ResourceT`]
            A Pydantic subclass used to validate the response from the FLAME Hub. This should be a model that validates
            all attributes a resource can have. In other terms, do not pass one of the models that start with *Create*
            or *Update* since this method performs a ``GET`` request.
        resource : :py:class:`~pydantic.BaseModel`
            This has to be the corresponding update model for ``resource_type``. All update models follow a naming
            convention with a prefixed *Update*. See the :doc:`model specifications <models_api>` for a list of all
            available models.
        *path : :py:class:`str` | :py:class:`~flame_hub.types.UuidIdentifiable`
            A string or multiple strings that define the endpoint. Since the last component of the path is a UUID of
            a specific resource, it is also possible to pass in an :py:class:`~uuid.UUID` object or a model with an
            ``id`` attribute.

        Returns
        -------
        :py:type:`~flame_hub._base_client.ResourceT`
            Validated resource that was just updated.

        Raises
        ------
        :py:exc:`.HubAPIError`
            If the status code of the response does not match 202.
        :py:exc:`~pydantic_core._pydantic_core.ValidationError`
            If the resource returned by the Hub instance does not validate with the given ``resource_type``.
        """
        r = self._client.post(
            "/".join(convert_path(path)),
            json=resource.model_dump(mode="json", exclude_none=False, exclude_unset=True),
        )

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_hub_api_error_from_response(r)

        return resource_type(**r.json())

    def _delete_resource(self, *path: str | UuidIdentifiable):
        """Delete a resource of a certain type at the specified path.

        Parameters
        ----------
        *path : :py:class:`str` | :py:class:`~flame_hub.types.UuidIdentifiable`
            A string or multiple strings that define the endpoint. Since the last component of the path is a UUID of
            a specific resource, it is also possible to pass in an :py:class:`~uuid.UUID` object or a model with an
            ``id`` attribute.

        Raises
        ------
        :py:exc:`.HubAPIError`
            If the status code of the response does not match 202.
        """
        r = self._client.delete("/".join(convert_path(path)))

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_hub_api_error_from_response(r)
