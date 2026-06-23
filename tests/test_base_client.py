import typing as t
import uuid

import httpx
from pydantic import BaseModel, WrapValidator, Field, ValidationError
import pytest

from flame_hub._base_client import (
    build_page_params,
    build_filter_params,
    build_sort_params,
    build_include_params,
    uuid_validator,
    build_field_params,
    IsOptionalField,
    IsIncludable,
    get_field_names,
    get_includable_names,
    DEFAULT_PAGE_PARAMS,
    BaseClient,
    UNSET,
    UNSET_T,
    resolve_request_auth,
    _StaticAuthorization,
)
from flame_hub.types import FilterOperator
from flame_hub.models import Node, User, Bucket


@pytest.mark.parametrize(
    "page_params,expected",
    [
        (None, {"page[limit]": 50, "page[offset]": 0}),
        ({}, {"page[limit]": 50, "page[offset]": 0}),
        ({"limit": 100}, {"page[limit]": 100, "page[offset]": 0}),
        ({"offset": 100}, {"page[limit]": 50, "page[offset]": 100}),
        ({"limit": 100, "offset": 200}, {"page[limit]": 100, "page[offset]": 200}),
    ],
)
def test_build_page_params(page_params, expected):
    assert expected == build_page_params(page_params, DEFAULT_PAGE_PARAMS)


@pytest.mark.parametrize(
    "filter_params,expected",
    [
        (None, {}),
        ({}, {}),
        ({"id": "foo"}, {"filter[id]": "foo"}),
        ({"id": (FilterOperator.eq, "foo")}, {"filter[id]": "foo"}),
        ({"id": ("", "foo")}, {"filter[id]": "foo"}),
        ({"id": ("=", "foo")}, {"filter[id]": "foo"}),
        ({"id": (FilterOperator.like, "foo")}, {"filter[id]": "~foo"}),
        ({"id": ("~", "foo")}, {"filter[id]": "~foo"}),
        ({"id": (FilterOperator.lt, "20")}, {"filter[id]": "<20"}),
        ({"id": ("<", "20")}, {"filter[id]": "<20"}),
        ({"id": (FilterOperator.le, "20")}, {"filter[id]": "<=20"}),
        ({"id": ("<=", "20")}, {"filter[id]": "<=20"}),
        ({"id": (FilterOperator.gt, "20")}, {"filter[id]": ">20"}),
        ({"id": (">", "20")}, {"filter[id]": ">20"}),
        ({"id": (FilterOperator.ge, "20")}, {"filter[id]": ">=20"}),
        ({"id": (">=", "20")}, {"filter[id]": ">=20"}),
    ],
)
def test_build_filter_params(filter_params, expected):
    assert expected == build_filter_params(filter_params)


@pytest.mark.parametrize(
    "sort_params,expected",
    [
        (None, {}),
        ({}, {}),
        ({"by": "foobar"}, {"sort": "foobar"}),
        ({"by": "foobar", "order": "ascending"}, {"sort": "foobar"}),
        ({"by": "foobar", "order": "descending"}, {"sort": "-foobar"}),
    ],
)
def test_build_sort_params(sort_params, expected):
    assert expected == build_sort_params(sort_params)


@pytest.mark.parametrize(
    "include_params,expected",
    [
        (None, {}),
        ((), {}),
        ([], {}),
        ("foo", {"include": "foo"}),
        (("foo",), {"include": "foo"}),
        (("foo", "bar"), {"include": "foo,bar"}),
        (
            [
                "foo",
            ],
            {"include": "foo"},
        ),
        (["foo", "bar"], {"include": "foo,bar"}),
    ],
)
def test_build_include_params(include_params, expected):
    assert expected == build_include_params(include_params)


@pytest.mark.parametrize(
    "field_params,expected",
    [
        (None, {}),
        ((), {}),
        ([], {}),
        ("foo", {"fields": "+foo"}),
        (("foo",), {"fields": "+foo"}),
        (("foo", "bar"), {"fields": "+foo,+bar"}),
        (
            [
                "foo",
            ],
            {"fields": "+foo"},
        ),
        (["foo", "bar"], {"fields": "+foo,+bar"}),
    ],
)
def test_build_field_params(field_params, expected):
    assert expected == build_field_params(field_params)


class UpdateModel(BaseModel):
    name: str | UNSET_T = UNSET


@pytest.mark.parametrize(
    "model,json",
    [
        (UpdateModel(name="my_name"), {"name": "my_name"}),
        (UpdateModel(name=UNSET), {}),
        (UpdateModel(), {}),
    ],
)
def test_serializing_update_model(model, json):
    assert model.model_dump(mode="json", exclude_defaults=True) == json


class UUIDValidatorModel(BaseModel):
    id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]


@pytest.mark.parametrize("input_id", [None, uuid.uuid4(), str(uuid.uuid4()), UUIDValidatorModel(id=uuid.uuid4())])
def test_uuid_validator_with_valid_ids(input_id):
    UUIDValidatorModel(id=input_id)


@pytest.mark.parametrize("input_id", ["28b9959b-346b-4a85-8dd3-6bb2a29e773", 42, True])
def test_uuid_validator_with_invalid_ids(input_id):
    with pytest.raises(ValidationError):
        UUIDValidatorModel(id=input_id)


class NoFieldModel(BaseModel):
    bar: str


class FieldModel(NoFieldModel):
    foo: t.Annotated[str | None, IsOptionalField]


class ExtendedFieldModel(FieldModel):
    foo_bar: bool | None
    bar_foo: t.Annotated[int, IsOptionalField] = 0


@pytest.mark.parametrize(
    "model,fields",
    [
        (NoFieldModel, ()),
        (FieldModel, ("foo",)),
        (ExtendedFieldModel, ("bar_foo", "foo")),
    ],
)
def test_get_field_names(model, fields):
    assert get_field_names(model) == fields


class NoIncludeModel(BaseModel):
    bar: str


class IncludeModel(NoIncludeModel):
    foo: t.Annotated[str | None, IsIncludable]


class ExtendedIncludeModel(IncludeModel):
    foo_bar: bool | None
    bar_foo: t.Annotated[int, IsIncludable] = 0


@pytest.mark.parametrize(
    "model,includable_properties",
    [
        (NoIncludeModel, ()),
        (IncludeModel, ("foo",)),
        (ExtendedIncludeModel, ("bar_foo", "foo")),
    ],
)
def test_get_includable_names(model, includable_properties):
    assert get_includable_names(model) == includable_properties


@pytest.mark.integration
@pytest.mark.parametrize(
    "resource_type,base_url_fixture_name,path",
    [
        (Node, "core_base_url", "nodes"),
        (User, "auth_base_url", "users"),
        (Bucket, "storage_base_url", "buckets"),
    ],
)
def test_resource_list_meta_data(request, password_auth, resource_type, base_url_fixture_name, path):
    client = BaseClient(base_url=request.getfixturevalue(base_url_fixture_name), auth=password_auth)
    _, meta = client._find_all_resources(resource_type, path, meta=True)

    assert meta.total >= 0
    assert meta.limit == DEFAULT_PAGE_PARAMS["limit"]
    assert meta.offset == DEFAULT_PAGE_PARAMS["offset"]


def test_resolve_request_auth_use_client_default_passes_through():
    # The default sentinel is passed straight to httpx, which keeps the client's bound auth.
    assert resolve_request_auth(httpx.USE_CLIENT_DEFAULT) is httpx.USE_CLIENT_DEFAULT


def test_resolve_request_auth_none_disables_auth():
    # None is passed through to httpx, which disables auth (no Authorization header) for the request.
    assert resolve_request_auth(None) is None


def test_resolve_request_auth_string_wraps_header():
    resolved = resolve_request_auth("Bearer token123")
    assert isinstance(resolved, _StaticAuthorization)

    # the string is sent verbatim as the Authorization header
    request = next(resolved.auth_flow(httpx.Request("GET", "http://testserver")))
    assert request.headers["Authorization"] == "Bearer token123"


@pytest.mark.parametrize("auth", [httpx.BasicAuth("user", "pass"), ("user", "pass")])
def test_resolve_request_auth_passes_through_non_string_overrides(auth):
    assert resolve_request_auth(auth) is auth


class _AuthProbe(BaseModel):
    id: uuid.UUID


def _make_probe_client(recorder: dict) -> httpx.Client:
    """Build a client whose bound auth sets ``Bearer DEFAULT`` and which records the ``Authorization`` header of every
    request it handles.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        recorder["authorization"] = request.headers.get("Authorization")

        if request.method == "DELETE":
            return httpx.Response(httpx.codes.ACCEPTED.value)
        if request.method == "POST":
            return httpx.Response(httpx.codes.CREATED.value, json={"id": str(uuid.uuid4())})

        # GET for a single resource
        return httpx.Response(httpx.codes.OK.value, json={"id": str(uuid.uuid4())})

    return httpx.Client(
        auth=_StaticAuthorization("Bearer DEFAULT"),
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )


# (auth argument, expected Authorization header) covering every supported form
_AUTH_OVERRIDE_CASES = [
    (httpx.USE_CLIENT_DEFAULT, "Bearer DEFAULT"),  # default sentinel keeps the client's bound auth
    ("Bearer OVERRIDE", "Bearer OVERRIDE"),  # raw header value
    (_StaticAuthorization("Bearer VIA_AUTH"), "Bearer VIA_AUTH"),  # httpx.Auth instance
    (None, None),  # disable auth for this request (no Authorization header)
]


def test_auth_defaults_to_client_bound_auth_when_omitted():
    recorder = {}
    client = BaseClient(base_url="http://testserver", client=_make_probe_client(recorder))

    # omitting auth must behave like the default sentinel and keep the bound auth
    client._get_single_resource(_AuthProbe, "things", uuid.uuid4())

    assert recorder["authorization"] == "Bearer DEFAULT"


@pytest.mark.parametrize("auth,expected", _AUTH_OVERRIDE_CASES)
def test_get_single_resource_auth_override(auth, expected):
    recorder = {}
    client = BaseClient(base_url="http://testserver", client=_make_probe_client(recorder))

    client._get_single_resource(_AuthProbe, "things", uuid.uuid4(), auth=auth)

    assert recorder["authorization"] == expected


@pytest.mark.parametrize("auth,expected", _AUTH_OVERRIDE_CASES)
def test_create_resource_auth_override(auth, expected):
    recorder = {}
    client = BaseClient(base_url="http://testserver", client=_make_probe_client(recorder))

    client._create_resource(_AuthProbe, _AuthProbe(id=uuid.uuid4()), "things", auth=auth)

    assert recorder["authorization"] == expected


@pytest.mark.parametrize("auth,expected", _AUTH_OVERRIDE_CASES)
def test_delete_resource_auth_override(auth, expected):
    recorder = {}
    client = BaseClient(base_url="http://testserver", client=_make_probe_client(recorder))

    client._delete_resource("things", uuid.uuid4(), auth=auth)

    assert recorder["authorization"] == expected


@pytest.mark.parametrize("auth,expected", _AUTH_OVERRIDE_CASES)
def test_find_all_resources_auth_override(auth, expected):
    recorder = {}

    def handler(request: httpx.Request) -> httpx.Response:
        recorder["authorization"] = request.headers.get("Authorization")
        return httpx.Response(httpx.codes.OK.value, json={"data": [], "meta": {"total": 0}})

    probe_client = httpx.Client(
        auth=_StaticAuthorization("Bearer DEFAULT"),
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )
    client = BaseClient(base_url="http://testserver", client=probe_client)

    client._find_all_resources(_AuthProbe, "things", auth=auth)

    assert recorder["authorization"] == expected


@pytest.mark.parametrize("auth,expected", _AUTH_OVERRIDE_CASES)
def test_public_read_method_forwards_auth(auth, expected):
    # exercises the public client surface (get_*/find_* forward auth through to the request)
    from flame_hub import AuthClient

    recorder = {}

    def handler(request: httpx.Request) -> httpx.Response:
        recorder["authorization"] = request.headers.get("Authorization")
        return httpx.Response(httpx.codes.OK.value, json={"data": [], "meta": {"total": 0}})

    probe_client = httpx.Client(
        auth=_StaticAuthorization("Bearer DEFAULT"),
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )
    auth_client = AuthClient(client=probe_client)

    auth_client.find_realms(auth=auth)
    assert recorder["authorization"] == expected


@pytest.mark.parametrize("auth,expected", _AUTH_OVERRIDE_CASES)
def test_public_write_method_forwards_auth(auth, expected):
    # exercises the public client surface (create_*/delete_* forward auth through to the request)
    from flame_hub import AuthClient

    recorder = {}

    def handler(request: httpx.Request) -> httpx.Response:
        recorder["authorization"] = request.headers.get("Authorization")
        return httpx.Response(httpx.codes.ACCEPTED.value)

    probe_client = httpx.Client(
        auth=_StaticAuthorization("Bearer DEFAULT"),
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )
    auth_client = AuthClient(client=probe_client)

    auth_client.delete_realm(uuid.uuid4(), auth=auth)
    assert recorder["authorization"] == expected
