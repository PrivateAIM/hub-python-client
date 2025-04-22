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


@pytest.fixture()
def permission(auth_client):
    new_permission = auth_client.create_permission(next_random_string())
    yield new_permission
    auth_client.delete_permission(new_permission)


@pytest.fixture()
def role(auth_client):
    new_role = auth_client.create_role(next_random_string())
    yield new_role
    auth_client.delete_role(new_role)


@pytest.fixture()
def role_permission(auth_client, role, permission):
    new_role_permission = auth_client.create_role_permission(role, permission)
    yield new_role_permission
    auth_client.delete_role_permission(new_role_permission)


@pytest.fixture()
def user(auth_client):
    new_user = auth_client.create_user(next_random_string())
    yield new_user
    auth_client.delete_user(new_user)


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


def test_get_permission(auth_client, permission):
    assert permission == auth_client.get_permission(permission.id)


def test_get_permission_not_found(auth_client):
    assert auth_client.get_permission(next_uuid()) is None


def test_get_permissions(auth_client):
    assert len(auth_client.get_permissions()) > 0


def test_find_permissions(auth_client, permission):
    assert [permission] == auth_client.find_permissions(filter={"id": permission.id})


def test_update_permission(auth_client, permission):
    new_name = next_random_string()
    new_permission = auth_client.update_permission(permission.id, name=new_name)

    assert permission != new_permission
    assert new_permission.name == new_name


def test_get_role(auth_client, role):
    assert role == auth_client.get_role(role.id)


def test_get_role_not_found(auth_client):
    assert auth_client.get_role(next_uuid()) is None


def test_get_roles(auth_client, role):
    assert len(auth_client.get_roles()) > 0


def test_find_roles(auth_client, role):
    assert [role] == auth_client.find_roles(filter={"id": role.id})


def test_update_role(auth_client, role):
    new_name = next_random_string()
    new_role = auth_client.update_role(role.id, name=new_name)

    assert role != new_role
    assert new_role.name == new_name


def test_get_role_permission(auth_client, role_permission):
    assert role_permission == auth_client.get_role_permission(role_permission.id)


def test_get_role_permission_not_found(auth_client):
    assert auth_client.get_role_permission(next_uuid()) is None


def test_get_role_permissions(auth_client, role_permission):
    assert len(auth_client.get_role_permissions()) > 0


def test_find_role_permissions(auth_client, role_permission):
    # Use role_id for filtering because there is no filter mechanism
    assert [role_permission] == auth_client.find_role_permissions(filter={"role_id": role_permission.role_id})


def test_get_user(auth_client, user):
    assert user == auth_client.get_user(user.id)


def test_get_user_not_found(auth_client):
    assert auth_client.get_user(next_uuid()) is None


def test_get_users(auth_client, user):
    assert len(auth_client.get_users()) > 0


def test_find_users(auth_client, user):
    assert [user] == auth_client.find_users(filter={"id": user.id})


def test_update_user(auth_client, user):
    new_name = next_random_string()
    new_user = auth_client.update_user(user.id, name=new_name)

    assert user != new_user
    assert new_name == new_user.name
