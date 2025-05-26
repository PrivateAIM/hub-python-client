import typing as t
import uuid

from pydantic import BaseModel, WrapValidator, Field, ValidationError
import pytest

from flame_hub._base_client import (
    build_page_params,
    build_filter_params,
    build_sort_params,
    UpdateModel,
    build_include_params,
    uuid_validator,
    build_field_params,
    IsField,
    get_field_names,
)
from flame_hub.types import FilterOperator, PageParams
from flame_hub.models import UNSET

_DEFAULT_PAGE_PARAMS: PageParams = {"limit": 50, "offset": 0}


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
    assert expected == build_page_params(page_params, _DEFAULT_PAGE_PARAMS)


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


class FooUpdateModel(UpdateModel):
    foo: str | None = None


def test_update_model_dump_if_not_set():
    assert FooUpdateModel().model_dump(mode="json", exclude_unset=True, exclude_none=False) == {}


def test_update_model_dump_if_none_set():
    assert FooUpdateModel(foo=None).model_dump(mode="json", exclude_unset=True, exclude_none=False) == {"foo": None}


def test_update_model_dump_if_unset():
    assert FooUpdateModel(foo=UNSET).model_dump(mode="json", exclude_unset=True, exclude_none=False) == {}


def test_update_model_dump_if_set():
    assert FooUpdateModel(foo="bar").model_dump(mode="json", exclude_unset=True, exclude_none=False) == {"foo": "bar"}


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
    foo: t.Annotated[str | None, IsField]


class ExtendedFieldModel(FieldModel):
    foo_bar: bool | None
    bar_foo: t.Annotated[int, IsField] = 0


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
