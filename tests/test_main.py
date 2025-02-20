import httpx
import pytest

from flame_hub.main import add


def test_add():
    assert add(1, 1) == 2
    assert add(-1, 1) == 0
    assert add(2, 0) == 2


@pytest.mark.integration
def test_sanity(nginx):
    # will be a redirect to login page
    assert httpx.get("http://localhost:3000").status_code == 302
