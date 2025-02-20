import httpx
import pytest

pytestmark = pytest.mark.integration


def test_password_auth_reissue(client, auth_base_url):
    # get a copy of the current access token
    old_token = client.auth._current_token.access_token
    # reset expiration timestamp to force token request with refresh token
    client.auth._current_token_expires_at = 0

    r = client.get(auth_base_url)
    assert r.status_code == httpx.codes.OK.value

    # check that the token has indeed changed
    assert client.auth._current_token.access_token != old_token
