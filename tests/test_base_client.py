import pytest

from flame_hub.base_client import build_page_params, FilterOperator, build_filter_params, PageParams, build_sort_params

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
