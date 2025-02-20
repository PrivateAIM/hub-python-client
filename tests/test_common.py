import urllib.parse

import pytest

from flame_hub import common


def test_build_url():
    assert "http://privateaim.de/analysis?foo=bar#baz" == common.build_url(
        "http", "privateaim.de", "analysis", {"foo": "bar"}, "baz"
    )


_parse_result = urllib.parse.urlsplit("http://privateaim.de/analysis?foo=bar#baz")


@pytest.mark.parametrize(
    "parse_result,kwargs,expected",
    [
        [_parse_result, {}, "http://privateaim.de/analysis?foo=bar#baz"],
        [_parse_result, {"scheme": "https"}, "https://privateaim.de/analysis?foo=bar#baz"],
        [_parse_result, {"netloc": "foo.bar"}, "http://foo.bar/analysis?foo=bar#baz"],
        [_parse_result, {"path": "foobar"}, "http://privateaim.de/foobar?foo=bar#baz"],
        [_parse_result, {"query": {"baz": "bat"}}, "http://privateaim.de/analysis?foo=bar&baz=bat#baz"],
        [_parse_result, {"query": {"foo": "123"}}, "http://privateaim.de/analysis?foo=123#baz"],
        [_parse_result, {"query": {"filter[]": "123"}}, "http://privateaim.de/analysis?foo=bar&filter[]=123#baz"],
        [_parse_result, {"fragment": "abcdefg"}, "http://privateaim.de/analysis?foo=bar#abcdefg"],
    ],
)
def test_merge_parse_result(parse_result, kwargs, expected):
    assert expected == common.merge_parse_result(parse_result, **kwargs)


@pytest.mark.parametrize(
    "base_path,path,expected",
    [
        ["foo", "bar", "foo/bar"],
        ["foo/bar", "baz", "foo/bar/baz"],
        ["foo/bar/", "baz", "foo/bar/baz"],
        ["/foo/bar", "baz", "foo/bar/baz"],
        ["foo", "bar/baz", "foo/bar/baz"],
        ["foo", "bar/baz/", "foo/bar/baz"],
        ["foo", "/bar/baz", "foo/bar/baz"],
        ["foo", "", "foo"],
        ["foo/bar", "", "foo/bar"],
        ["", "foo", "foo"],
        ["", "foo/bar", "foo/bar"],
        ["", "", ""],
    ],
)
def test_join_url_path(base_path, path, expected):
    assert common.join_url_path(base_path, path) == expected
