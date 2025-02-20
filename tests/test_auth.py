import pytest

from tests.helpers import next_random_string, next_uuid

pytestmark = pytest.mark.integration


@pytest.fixture()
def realm(auth_client):
    new_realm = auth_client.create_realm(next_random_string())
    yield new_realm
    auth_client.delete_realm(new_realm)


@pytest.fixture()
def robot(auth_client, realm):
    new_robot = auth_client.create_robot(next_random_string(), realm, next_random_string(length=64))
    yield new_robot
    auth_client.delete_robot(new_robot)


def test_get_realm(auth_client, realm):
    assert realm == auth_client.get_realm(realm.id)


def test_get_realm_not_found(auth_client, realm):
    assert auth_client.get_realm(next_uuid()) is None


def test_update_realm(auth_client, realm):
    new_name = next_random_string()
    new_realm = auth_client.update_realm(realm.id, name=new_name)

    assert realm != new_realm
    assert new_realm.name == new_name


def test_get_robot(auth_client, robot):
    assert robot == auth_client.get_robot(robot.id)


def test_get_robot_not_found(auth_client, robot):
    assert auth_client.get_robot(next_uuid()) is None


def test_update_robot(auth_client, robot):
    new_name = next_random_string()
    new_robot = auth_client.update_robot(robot.id, name=new_name)

    assert robot != new_robot
    assert new_robot.name == new_name
