import typing as t
import uuid

import httpx2 as httpx
from pydantic import BaseModel, WrapValidator, Field, ValidationError
import pytest

import flame_hub
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
    resolve_auth,
)
from flame_hub.auth import ClientAuth, PasswordAuth, StaticAuth
from flame_hub.types import FilterOperator
from flame_hub.models import Node, Realm, User, Bucket, RefreshToken, ClientCredentials
from tests.helpers import next_random_string


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
    "externalName": None,
    "hidden": False,
    "realmId": "9d6b7a44-3f66-4f8b-9d2e-9dd0d2d7b2c1",
    "registryId": None,
    "type": "default",
    "publicKey": None,
    "online": False,
    "registryProjectId": None,
    "clientId": None,
    "createdAt": "2026-07-20T09:25:01.000Z",
    "updatedAt": "2026-07-20T09:25:01.000Z",
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
    auth_client = flame_hub.AuthClient(client=new_mock_client({"data": REALM_JSON, "meta": {}}, status_code))

    assert call_client(auth_client) == Realm(**REALM_JSON)


def test_auth_client_rejects_unwrapped_single_resource():
    auth_client = flame_hub.AuthClient(client=new_mock_client(REALM_JSON))

    with pytest.raises(ValueError, match="data property"):
        auth_client.get_realm(REALM_JSON["id"])


def test_auth_client_keeps_list_response_untouched():
    auth_client = flame_hub.AuthClient(client=new_mock_client({"data": [REALM_JSON], "meta": {"total": 1}}))

    assert auth_client.get_realms() == [Realm(**REALM_JSON)]


def test_base_client_keeps_single_resource_untouched():
    # the base client makes no assumption about the envelope, so it passes the body through unchanged
    client = BaseClient(base_url="http://localhost", client=new_mock_client(NODE_JSON))

    assert client._get_single_resource(Node, "nodes", NODE_JSON["id"]) == Node(**NODE_JSON)


BUCKET_JSON = {
    "id": "0a6ff30e-2f6f-4a09-9d67-33f5b5a4bb3e",
    "name": "my-bucket",
    "region": None,
    "createdAt": "2026-07-20T09:25:01.000Z",
    "updatedAt": "2026-07-20T09:25:01.000Z",
    "actorId": None,
    "actorType": None,
    "realmId": None,
}

CLIENT_CREDENTIALS_JSON = {
    "id": "9b5d0b2c-19d7-4b7f-9a9a-4b1f0aa0f9de",
    "secret": "s3cr3t",
    "name": "my-node",
    "displayName": "My Node",
}


@pytest.mark.parametrize(
    "status_code,call_client",
    [
        (httpx.codes.OK.value, lambda c: c.get_node(NODE_JSON["id"])),
        (httpx.codes.CREATED.value, lambda c: c.create_node(NODE_JSON["name"], NODE_JSON["realmId"])),
        (httpx.codes.ACCEPTED.value, lambda c: c.update_node(NODE_JSON["id"], hidden=False)),
    ],
)
def test_core_client_unwraps_single_resource(status_code, call_client):
    # the FLAME Hub wraps records as {"data": ..., "meta": ...} since 0.13.0
    core_client = flame_hub.CoreClient(client=new_mock_client({"data": NODE_JSON, "meta": {}}, status_code))

    assert call_client(core_client) == Node(**NODE_JSON)


def test_core_client_rejects_unwrapped_single_resource():
    core_client = flame_hub.CoreClient(client=new_mock_client(NODE_JSON))

    with pytest.raises(ValueError, match="data property"):
        core_client.get_node(NODE_JSON["id"])


def test_core_client_unwraps_analysis_command_response():
    # POST /analyses/:id/command reads the body itself rather than going through _get_single_resource
    core_client = flame_hub.CoreClient(client=new_mock_client(NODE_JSON, httpx.codes.ACCEPTED.value))

    with pytest.raises(ValueError, match="data property"):
        core_client.send_analysis_command(uuid.uuid4(), "configurationLock")


@pytest.mark.parametrize(
    "call_client",
    [
        lambda c: c.get_node_client_credentials(NODE_JSON["id"]),
        lambda c: c.get_analysis_client_credentials(uuid.uuid4()),
    ],
)
def test_core_client_keeps_credentials_flat(call_client):
    # the credential routes are among the endpoints which deliberately respond without an envelope
    core_client = flame_hub.CoreClient(client=new_mock_client(CLIENT_CREDENTIALS_JSON))

    assert call_client(core_client) == ClientCredentials(**CLIENT_CREDENTIALS_JSON)


def test_core_client_keeps_list_response_untouched():
    core_client = flame_hub.CoreClient(client=new_mock_client({"data": [NODE_JSON], "meta": {"total": 1}}))

    assert core_client.get_nodes() == [Node(**NODE_JSON)]


def test_storage_client_unwraps_single_resource():
    storage_client = flame_hub.StorageClient(client=new_mock_client({"data": BUCKET_JSON, "meta": {}}))

    assert storage_client.get_bucket(BUCKET_JSON["id"]) == Bucket(**BUCKET_JSON)


def test_storage_client_rejects_unwrapped_single_resource():
    storage_client = flame_hub.StorageClient(client=new_mock_client(BUCKET_JSON))

    with pytest.raises(ValueError, match="data property"):
        storage_client.get_bucket(BUCKET_JSON["id"])


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


@pytest.mark.parametrize(
    "value",
    [
        ClientAuth(client_id=next_random_string(), client_secret=next_random_string()),
        PasswordAuth(username=next_random_string(), password=next_random_string()),
        StaticAuth(access_token=next_random_string()),
        None,
        httpx.USE_CLIENT_DEFAULT,
    ],
)
def test_resolve_auth_other_than_string(value):
    assert value is resolve_auth(value)


def test_resolve_auth_for_string():
    token = next_random_string()
    auth = resolve_auth(token)

    assert isinstance(auth, StaticAuth)
    assert token == auth._access_token


@pytest.mark.integration
def test_override_auth(core_base_url, auth_base_url, auth_admin_username, auth_admin_password):
    auth_client = httpx.Client(base_url=auth_base_url)
    r = auth_client.post(
        "token",
        json={
            "grant_type": "password",
            "username": auth_admin_username,
            "password": auth_admin_password,
        },
    )

    assert r.status_code == httpx.codes.OK.value

    token = RefreshToken(**r.json()).access_token

    recorder = {}

    def handler(request):
        recorder["auth_header"] = request.headers.get("Authorization")
        return request

    test_client = httpx.Client(
        base_url=core_base_url,
        auth=StaticAuth(access_token=next_random_string()),
        event_hooks={"request": [handler]},
    )
    core_client = flame_hub.CoreClient(client=test_client)

    node = core_client.create_node(name=next_random_string(), auth=token)

    assert recorder["auth_header"] == f"Bearer {token}"

    core_client.delete_node(node, auth=token)
