import httpx
import pytest

from flame_hub import RobotAuth
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
    client.auth._current_token_expires_at = 0

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
