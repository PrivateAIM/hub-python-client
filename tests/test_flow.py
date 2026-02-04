import httpx
import pytest

from flame_hub import HubAPIError
from flame_hub.auth import RobotAuth, PasswordAuth, ClientAuth
from tests.helpers import next_random_string

pytestmark = pytest.mark.integration


def test_password_auth_reissue(password_auth, auth_base_url):
    # instantiate client
    client = httpx.Client(auth=password_auth)
    r = client.get(auth_base_url)
    assert r.status_code == httpx.codes.OK.value

    # get a copy of the current access token
    old_token = client.auth._current_token.access_token
    # reset expiration timestamp to force token request with refresh token
    client.auth._current_token_expires_at_nanos = 0

    r = client.get(auth_base_url)
    assert r.status_code == httpx.codes.OK.value

    # check that the token has indeed changed
    assert client.auth._current_token.access_token != old_token


def test_robot_auth(auth_client, auth_base_url, master_realm):
    robot_secret = next_random_string(length=64)
    robot = auth_client.create_robot(next_random_string(), master_realm, robot_secret)
    robot_id = str(robot.id)

    robot_auth = RobotAuth(
        robot_id=robot_id,
        robot_secret=robot_secret,
        base_url=auth_base_url,
    )

    client = httpx.Client(auth=robot_auth)

    # check that auth flow works
    r = client.get(auth_base_url)
    assert r.status_code == httpx.codes.OK.value

    auth_client.delete_robot(robot)


def test_client_auth(auth_client, auth_base_url, master_realm):
    client_secret = next_random_string(length=64)
    client_resource = auth_client.create_client(name=next_random_string(), realm_id=master_realm, secret=client_secret)
    client_id = str(client_resource.id)

    client_auth = ClientAuth(
        client_id=client_id,
        client_secret=client_secret,
        base_url=auth_base_url,
    )

    client = httpx.Client(auth=client_auth)

    # Check that the auth flow works.
    r = client.get(auth_base_url)
    assert r.status_code == httpx.codes.OK.value

    auth_client.delete_client(client_resource)


def test_client_auth_raise_error(nginx, auth_base_url):
    # Use random client_id and client_secret.
    client_auth = ClientAuth(client_id=next_random_string(), client_secret=next_random_string(), base_url=auth_base_url)
    client = httpx.Client(auth=client_auth)

    # This call should fail.
    with pytest.raises(HubAPIError) as e:
        client.get(auth_base_url)

    assert "The client credentials are invalid" in str(e.value)
    assert e.value.error_response.status_code == httpx.codes.BAD_REQUEST.value


def test_password_auth_raise_error(nginx, auth_base_url):
    # use random username and password
    pw_auth = PasswordAuth(next_random_string(), next_random_string(), auth_base_url)
    client = httpx.Client(auth=pw_auth)

    # this call should fail
    with pytest.raises(HubAPIError) as e:
        client.get(auth_base_url)

    assert "The user credentials are invalid" in str(e.value)
    assert e.value.error_response.status_code == httpx.codes.BAD_REQUEST.value


def test_robot_auth_raise_error(nginx, auth_base_url):
    # use random id and secret
    robot_auth = RobotAuth(next_random_string(), next_random_string(), auth_base_url)
    client = httpx.Client(auth=robot_auth)

    # this call should fail
    with pytest.raises(HubAPIError) as e:
        client.get(auth_base_url)

    assert "The robot credentials are invalid" in str(e.value)
    assert e.value.error_response.status_code == httpx.codes.BAD_REQUEST.value


def test_password_auth_reissue_raise_error(password_auth, auth_base_url):
    # instantiate client
    client = httpx.Client(auth=password_auth)
    # fetch refresh token
    r = client.get(auth_base_url)
    assert r.status_code == httpx.codes.OK.value

    # need to create a new instance as to avoid modifying the password_auth fixture
    # otherwise this will affect other tests
    new_client = httpx.Client(auth=PasswordAuth(password_auth._username, password_auth._password, auth_base_url))

    # copy existing token and reset expiration timestamp
    new_client.auth._current_token = client.auth._current_token.model_copy()
    new_client.auth._current_token_expires_at_nanos = 0

    # overwrite refresh token
    new_client.auth._current_token.refresh_token = "foobar"

    # technically it would be better to have a properly signed JWT as the refresh token but
    # that would require forging it. no clue how to feasibly do that.
    with pytest.raises(HubAPIError) as e:
        new_client.get(auth_base_url)

    assert "The JWT is invalid" in str(e.value)
    assert e.value.error_response.status_code == httpx.codes.BAD_REQUEST.value
