import typing as t
import uuid

import httpx
from pydantic import BaseModel, WrapValidator, Field, ValidationError
import pytest

from flame_hub import AuthClient
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
)
from flame_hub.types import FilterOperator
from flame_hub.models import Node, Realm, User, Bucket


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


def new_mock_client(body: t.Any, status_code: int = httpx.codes.OK.value) -> httpx.Client:
    """Create an HTTP client which answers every request with the same status code and body."""
    return httpx.Client(
        base_url="http://localhost",
        transport=httpx.MockTransport(lambda _: httpx.Response(status_code, json=body)),
    )


REALM_JSON = {
    "id": "36b6a1a4-2fdb-4ec3-a1a9-4b1f0aa0f9de",
    "name": "master",
    "displayName": "Master Realm",
    "description": None,
    "builtIn": True,
    "createdAt": "2026-07-20T09:25:01.000Z",
    "updatedAt": "2026-07-20T09:25:01.000Z",
}

NODE_JSON = {
    "id": "5a0a3b0e-e4a0-4a41-9d7f-e2b9dcdcf9c1",
    "name": "my-node",
    "external_name": None,
    "hidden": False,
    "realm_id": "9d6b7a44-3f66-4f8b-9d2e-9dd0d2d7b2c1",
    "registry_id": None,
    "type": "default",
    "public_key": None,
    "online": False,
    "registry_project_id": None,
    "robot_id": None,
    "client_id": None,
    "created_at": "2026-07-20T09:25:01.000Z",
    "updated_at": "2026-07-20T09:25:01.000Z",
}


@pytest.mark.parametrize(
    "status_code,call_client",
    [
        (httpx.codes.OK.value, lambda c: c.get_realm(REALM_JSON["id"])),
        (httpx.codes.CREATED.value, lambda c: c.create_realm(REALM_JSON["name"])),
        (httpx.codes.ACCEPTED.value, lambda c: c.update_realm(REALM_JSON["id"], name=REALM_JSON["name"])),
    ],
)
def test_auth_client_unwraps_single_resource(status_code, call_client):
    # authup wraps single resources as {"data": ..., "meta": ...} since 1.0.0-beta.57
    auth_client = AuthClient(client=new_mock_client({"data": REALM_JSON, "meta": {}}, status_code))

    assert call_client(auth_client) == Realm(**REALM_JSON)


def test_auth_client_rejects_unwrapped_single_resource():
    auth_client = AuthClient(client=new_mock_client(REALM_JSON))

    with pytest.raises(ValueError, match="data property"):
        auth_client.get_realm(REALM_JSON["id"])


def test_auth_client_keeps_list_response_untouched():
    auth_client = AuthClient(client=new_mock_client({"data": [REALM_JSON], "meta": {"total": 1}}))

    assert auth_client.get_realms() == [Realm(**REALM_JSON)]


def test_base_client_keeps_single_resource_untouched():
    # the FLAME Hub core and storage services respond with the resource itself
    client = BaseClient(base_url="http://localhost", client=new_mock_client(NODE_JSON))

    assert client._get_single_resource(Node, "nodes", NODE_JSON["id"]) == Node(**NODE_JSON)


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
