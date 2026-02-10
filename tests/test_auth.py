import pytest

from flame_hub import get_field_names, get_includable_names
from flame_hub.models import (
    User,
    Robot,
    Permission,
    Role,
    RolePermission,
    UserPermission,
    UserRole,
    RobotPermission,
    RobotRole,
    Client,
)
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


@pytest.fixture(scope="session")
def robot_fields():
    return get_field_names(Robot)


@pytest.fixture(scope="session")
def robot_includables():
    return get_includable_names(Robot)


@pytest.fixture()
def permission(auth_client):
    new_permission = auth_client.create_permission(next_random_string())
    yield new_permission
    auth_client.delete_permission(new_permission)


@pytest.fixture(scope="session")
def permission_includables():
    return get_includable_names(Permission)


@pytest.fixture()
def role(auth_client):
    new_role = auth_client.create_role(next_random_string())
    yield new_role
    auth_client.delete_role(new_role)


@pytest.fixture(scope="session")
def role_includables():
    return get_includable_names(Role)


@pytest.fixture()
def role_permission(auth_client, role, permission):
    new_role_permission = auth_client.create_role_permission(role, permission)
    yield new_role_permission
    auth_client.delete_role_permission(new_role_permission)


@pytest.fixture(scope="session")
def role_permission_includables():
    return get_includable_names(RolePermission)


@pytest.fixture()
def user(auth_client):
    new_user = auth_client.create_user(name=next_random_string(), email=f"{next_random_string()}@test.com")
    yield new_user
    auth_client.delete_user(new_user)


@pytest.fixture(scope="session")
def user_fields():
    return get_field_names(User)


@pytest.fixture(scope="session")
def user_includables():
    return get_includable_names(User)


@pytest.fixture()
def user_permission(auth_client, user, permission):
    new_user_permission = auth_client.create_user_permission(user, permission)
    yield new_user_permission
    auth_client.delete_user_permission(new_user_permission)


@pytest.fixture(scope="session")
def user_permission_includables():
    return get_includable_names(UserPermission)


@pytest.fixture()
def user_role(auth_client, user, role):
    new_user_role = auth_client.create_user_role(user, role)
    yield new_user_role
    auth_client.delete_user_role(new_user_role)


@pytest.fixture(scope="session")
def user_role_includables():
    return get_includable_names(UserRole)


@pytest.fixture()
def robot_permission(auth_client, robot, permission):
    new_robot_permission = auth_client.create_robot_permission(robot, permission)
    yield new_robot_permission
    auth_client.delete_robot_permission(new_robot_permission)


@pytest.fixture(scope="session")
def robot_permission_includables():
    return get_includable_names(RobotPermission)


@pytest.fixture()
def robot_role(auth_client, robot, role):
    new_robot_role = auth_client.create_robot_role(robot, role)
    yield new_robot_role
    auth_client.delete_robot_role(new_robot_role)


@pytest.fixture(scope="session")
def robot_role_includables():
    return get_includable_names(RobotRole)


@pytest.fixture()
def client(auth_client, realm):
    new_client = auth_client.create_client(name=next_random_string(), realm_id=realm)
    yield new_client
    auth_client.delete_client(client_id=new_client)


@pytest.fixture(scope="session")
def client_includables():
    return get_includable_names(Client)


@pytest.fixture(scope="session")
def client_fields():
    return get_field_names(Client)


def test_get_realm(auth_client, realm):
    assert realm == auth_client.get_realm(realm.id)


def test_get_realm_not_found(auth_client, realm):
    assert auth_client.get_realm(next_uuid()) is None


def test_update_realm(auth_client, realm):
    new_name = next_random_string()
    new_realm = auth_client.update_realm(realm.id, name=new_name)

    assert realm != new_realm
    assert new_realm.name == new_name


def test_get_realms(auth_client, realm):
    assert len(auth_client.get_realms()) > 0


def test_find_realms(auth_client, realm):
    assert [realm] == auth_client.find_realms(filter={"id": realm.id})


def test_get_robot(auth_client, robot, robot_fields, robot_includables):
    robot_get = auth_client.get_robot(robot, fields=robot_fields)

    assert robot_get.id == robot.id
    assert all(field in robot_get.model_fields_set for field in robot_fields)
    assert all(includable in robot_get.model_fields_set for includable in robot_includables)


def test_get_robot_not_found(auth_client, robot):
    assert auth_client.get_robot(next_uuid()) is None


def test_update_robot(auth_client, robot):
    new_name = next_random_string()
    new_robot = auth_client.update_robot(robot.id, name=new_name)

    assert robot != new_robot
    assert new_robot.name == new_name


def test_get_robots(auth_client, robot, robot_fields, robot_includables):
    robots_get = auth_client.get_robots(fields=robot_fields)

    assert len(robots_get) > 0
    assert all(field in r.model_fields_set for r in robots_get for field in robot_fields)
    assert all(includable in r.model_fields_set for r in robots_get for includable in robot_includables)


def test_find_robots(auth_client, robot, robot_fields, robot_includables):
    robots_find = auth_client.find_robots(filter={"id": robot.id}, fields=robot_fields)

    assert [robot.id] == [r.id for r in robots_find]
    assert all(includable in r.model_fields_set for r in robots_find for includable in robot_includables)
    assert all(field in r.model_fields_set for r in robots_find for field in robot_fields)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2660")
def test_get_permission(auth_client, permission, permission_includables):
    perm_get = auth_client.get_permission(permission.id)

    assert perm_get.id == permission.id
    assert all(includable in perm_get.model_fields_set for includable in permission_includables)


def test_get_permission_not_found(auth_client):
    assert auth_client.get_permission(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2659")
def test_get_permissions(auth_client, permission_includables):
    perms_get = auth_client.get_permissions()

    assert len(perms_get) > 0
    assert all(includable in p.model_fields_set for p in perms_get for includable in permission_includables)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2659")
def test_find_permissions(auth_client, permission, permission_includables):
    perms_find = auth_client.find_permissions(filter={"id": permission.id})

    assert [permission.id] == [p.id for p in perms_find]
    assert all(includable in p.model_fields_set for p in perms_find for includable in permission_includables)


def test_update_permission(auth_client, permission):
    new_name = next_random_string()
    new_permission = auth_client.update_permission(permission.id, name=new_name)

    assert permission != new_permission
    assert new_permission.name == new_name


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2662")
def test_get_role(auth_client, role, role_includables):
    role_get = auth_client.get_role(role.id)

    assert role_get.id == role.id
    assert all(includable in role_get.model_fields_set for includable in role_includables)


def test_get_role_not_found(auth_client):
    assert auth_client.get_role(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2661")
def test_get_roles(auth_client, role, role_includables):
    roles_get = auth_client.get_roles()

    assert len(roles_get) > 0
    assert all(includable in r.model_fields_set for r in roles_get for includable in role_includables)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2661")
def test_find_roles(auth_client, role, role_includables):
    roles_find = auth_client.find_roles(filter={"id": role.id})

    assert [role.id] == [r.id for r in roles_find]
    assert all(includable in r.model_fields_set for r in roles_find for includable in role_includables)


def test_update_role(auth_client, role):
    new_name = next_random_string()
    new_role = auth_client.update_role(role.id, name=new_name)

    assert role != new_role
    assert new_role.name == new_name


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2643")
def test_get_role_permission(auth_client, role_permission, role_permission_includables):
    role_perm_get = auth_client.get_role_permission(role_permission.id)

    assert role_perm_get.id == role_permission.id
    assert all(includable in role_perm_get.model_fields_set for includable in role_permission_includables)


def test_get_role_permission_not_found(auth_client):
    assert auth_client.get_role_permission(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup")
def test_get_role_permissions(auth_client, role_permission, role_permission_includables):
    role_perms_get = auth_client.get_role_permissions()

    assert len(role_perms_get) > 0
    assert all(includable in rp.model_fields_set for rp in role_perms_get for includable in role_permission_includables)


@pytest.mark.xfail(reason="bug in authup")
def test_find_role_permissions(auth_client, role_permission, role_permission_includables):
    # Use "role_id" for filtering because there is no filter mechanism for attribute "id".
    role_perms_find = auth_client.find_role_permissions(filter={"role_id": role_permission.role_id})

    assert [role_permission.id] == [rp.id for rp in role_perms_find]
    assert all(
        includable in rp.model_fields_set for rp in role_perms_find for includable in role_permission_includables
    )


def test_get_user(auth_client, user, user_fields, user_includables):
    user_get = auth_client.get_user(user.id, fields=user_fields)

    assert user_get.id == user.id
    assert all(includable in user_get.model_fields_set for includable in user_includables)
    assert all(field in user_get.model_fields_set for field in user_fields)


def test_get_user_not_found(auth_client):
    assert auth_client.get_user(next_uuid()) is None


def test_get_users(auth_client, user, user_fields, user_includables):
    users_get = auth_client.get_users(fields=user_fields)

    assert len(users_get) > 0
    assert all(includable in u.model_fields_set for u in users_get for includable in user_includables)
    assert all(field in u.model_fields_set for u in users_get for field in user_fields)


def test_find_users(auth_client, user, user_fields, user_includables):
    users_find = auth_client.find_users(filter={"id": user.id}, fields=user_fields)

    assert [user.id] == [u.id for u in users_find]
    assert all(includable in u.model_fields_set for u in users_find for includable in user_includables)
    assert all(field in u.model_fields_set for u in users_find for field in user_fields)


def test_update_user(auth_client, user):
    new_name = next_random_string()
    new_user = auth_client.update_user(user.id, name=new_name)

    assert user != new_user
    assert new_name == new_user.name


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2644")
def test_get_user_permission(auth_client, user_permission, user_permission_includables):
    user_perm_get = auth_client.get_user_permission(user_permission.id)

    assert user_perm_get.id == user_permission.id
    assert all(includable in user_perm_get.model_fields_set for includable in user_permission_includables)


def test_get_user_permission_not_found(auth_client):
    assert auth_client.get_user_permission(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup")
def test_get_user_permissions(auth_client, user_permission, user_permission_includables):
    user_perms_get = auth_client.get_user_permissions()

    assert len(user_perms_get) > 0
    assert all(includable in up.model_fields_set for up in user_perms_get for includable in user_permission_includables)


@pytest.mark.xfail(reason="bug in authup")
def test_find_user_permissions(auth_client, user_permission, user_permission_includables):
    # Use "user_id" for filtering because there is no filter mechanism for attribute "id".
    user_perms_find = auth_client.find_user_permissions(filter={"user_id": user_permission.user_id})

    assert len(user_perms_find) > 0
    assert all(
        includable in up.model_fields_set for up in user_perms_find for includable in user_permission_includables
    )


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2645")
def test_get_user_role(auth_client, user_role, user_role_includables):
    user_role_get = auth_client.get_user_role(user_role.id)

    assert user_role_get.id == user_role.id
    assert all(includable in user_role_get.model_fields_set for includable in user_role_includables)


def test_get_user_role_not_found(auth_client):
    assert auth_client.get_user_role(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup")
def test_get_user_roles(auth_client, user_role, user_role_includables):
    user_roles_get = auth_client.get_user_roles()

    assert len(user_roles_get) > 0
    assert all(includable in ur.model_fields_set for ur in user_roles_get for includable in user_role_includables)


@pytest.mark.xfail(reason="bug in authup")
def test_find_user_roles(auth_client, user_role, user_role_includables):
    # Use "user_id" for filtering because there is no filter mechanism for attribute "id".
    user_roles_find = auth_client.find_user_roles(filter={"user_id": user_role.user_id})

    assert len(user_roles_find) > 0
    assert all(includable in ur.model_fields_set for ur in user_roles_find for includable in user_role_includables)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2647")
def test_get_robot_permission(auth_client, robot_permission, robot_permission_includables):
    robot_perm_get = auth_client.get_robot_permission(robot_permission.id)

    assert robot_perm_get.id == robot_permission.id
    assert all(includable in robot_perm_get.model_fields_set for includable in robot_permission_includables)


def test_get_robot_permission_not_found(auth_client):
    assert auth_client.get_permission(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup")
def test_get_robot_permissions(auth_client, robot_permission, robot_permission_includables):
    robot_perms_get = auth_client.get_robot_permissions()

    assert len(robot_perms_get) > 0
    assert all(
        includable in rp.model_fields_set for rp in robot_perms_get for includable in robot_permission_includables
    )


@pytest.mark.xfail(reason="bug in authup")
def test_find_robot_permissions(auth_client, robot_permission, robot_permission_includables):
    # Use "robot_id" for filtering because there is no filter mechanism for attribute "id".
    robot_perms_find = auth_client.find_robot_permissions(filter={"robot_id": robot_permission.robot_id})

    assert [robot_permission.id] == [rp.id for rp in robot_perms_find]
    assert all(
        includable in rp.model_fields_set for rp in robot_perms_find for includable in robot_permission_includables
    )


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2650")
def test_get_robot_role(auth_client, robot_role, robot_role_includables):
    robot_role_get = auth_client.get_robot_role(robot_role.id)

    assert robot_role_get.id == robot_role.id
    assert all(includable in robot_role_get.model_fields_set for includable in robot_role_includables)


def test_get_robot_role_not_found(auth_client):
    assert auth_client.get_robot_role(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2649")
def test_get_robot_roles(auth_client, robot_role, robot_role_includables):
    robot_roles_get = auth_client.get_robot_roles()

    assert len(robot_roles_get) > 0
    assert all(includable in rr.model_fields_set for rr in robot_roles_get for includable in robot_role_includables)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2649")
def test_find_robot_roles(auth_client, robot_role, robot_role_includables):
    # Use "robot_id" for filtering because there is no filter mechanism for attribute "id".
    robot_roles_find = auth_client.find_robot_roles(filter={"robot_id": robot_role.robot_id})

    assert [robot_role.id] == [rr.id for rr in robot_roles_find]
    assert all(includable in rr.model_fields_set for rr in robot_roles_find for includable in robot_role_includables)


def test_get_client(auth_client, client, client_includables, client_fields):
    client_get = auth_client.get_client(client_id=client, fields=client_fields)

    assert client_get.id == client.id
    assert all(includable in client_get.model_fields_set for includable in client_includables)
    assert all(field in client_get.model_fields_set for field in client_fields)


def test_get_client_not_found(auth_client):
    assert auth_client.get_client(client_id=next_uuid()) is None


def test_get_clients(auth_client, client, client_includables, client_fields):
    clients_get = auth_client.get_clients(fields=client_fields)

    assert len(clients_get) > 0
    assert all(includable in c.model_fields_set for c in clients_get for includable in client_includables)
    assert all(field in c.model_fields_set for c in clients_get for field in client_fields)


def test_find_clients(auth_client, client, client_includables, client_fields):
    # Use "name" for filtering because there is no filter mechanism for attribute "id".
    clients_find = auth_client.find_clients(filter={"name": client.name}, fields=client_fields)

    assert [client.id] == [c.id for c in clients_find]
    assert all(includable in c.model_fields_set for c in clients_find for includable in client_includables)
    assert all(field in c.model_fields_set for c in clients_find for field in client_fields)


def test_update_client(auth_client, client):
    new_name = next_random_string()
    new_client = auth_client.update_client(client_id=client, name=new_name)

    assert client != new_client
    assert new_client.name == new_name
