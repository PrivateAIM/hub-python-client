import time
import urllib.parse


def build_url(scheme="", netloc="", path="", query: dict[str, str | list[str]] = None, fragment=""):
    """
    Build a URL consisting of multiple parts.
    The function signature is identical to that of `urllib.parse.urlunsplit`, except that query parameters can be
    passed in as a dictionary and are automatically encoded.
    Furthermore, square brackets are not encoded to support the filtering mechanisms of the FLAME Hub API.

    Args:
        scheme: URL scheme specifier
        netloc: network location part
        path: hierarchical path
        query: query component
        fragment: fragment identifier

    Returns:
        combination of all parameters into a complete URL
    """
    if query is None:
        query = {}

    return urllib.parse.urlunsplit(
        (
            scheme,
            netloc,
            path,
            # square brackets must not be encoded to support central filtering stuff
            urllib.parse.urlencode(query, safe="[]", doseq=True),
            fragment,
        ),
    )


def merge_parse_result(
    parse_result: urllib.parse.SplitResult,
    scheme="",
    netloc="",
    path="",
    query: dict[str, str | list[str]] = None,
    fragment="",
):
    return build_url(
        scheme or parse_result.scheme,
        netloc or parse_result.netloc,
        path or parse_result.path,
        {
            **urllib.parse.parse_qs(parse_result.query),
            **(query or {}),
        },
        fragment or parse_result.fragment,
    )


def join_url_path(base_path: str, path: str) -> str:
    base_path = base_path.strip("/").split("/")
    path = path.strip("/").split("/")

    return "/".join([p for p in base_path + path if p != ""])


def now():
    """
    Get current Epoch time in seconds.

    :return:
    """
    return int(time.time())
