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


@pytest.fixture()
def user_permission(auth_client, user, permission):
    new_user_permission = auth_client.create_user_permission(user, permission)
    yield new_user_permission
    auth_client.delete_user_permission(new_user_permission)


@pytest.fixture()
def user_role(auth_client, user, role):
    new_user_role = auth_client.create_user_role(user, role)
    yield new_user_role
    auth_client.delete_user_role(new_user_role)


@pytest.fixture()
def robot_permission(auth_client, robot, permission):
    new_robot_permission = auth_client.create_robot_permission(robot, permission)
    yield new_robot_permission
    auth_client.delete_robot_permission(new_robot_permission)


@pytest.fixture()
def robot_role(auth_client, robot, role):
    new_robot_role = auth_client.create_robot_role(robot, role)
    yield new_robot_role
    auth_client.delete_robot_role(new_robot_role)


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


def test_get_robot(auth_client, robot):
    robot_get = auth_client.get_robot(robot)

    assert robot_get.id == robot.id


def test_get_robot_not_found(auth_client, robot):
    assert auth_client.get_robot(next_uuid()) is None


def test_update_robot(auth_client, robot):
    new_name = next_random_string()
    new_robot = auth_client.update_robot(robot.id, name=new_name)

    assert robot != new_robot
    assert new_robot.name == new_name


def test_get_robots(auth_client, robot):
    robots_get = auth_client.get_robots()

    assert len(robots_get) > 0


def test_find_robots(auth_client, robot):
    robots_find = auth_client.find_robots(filter={"id": robot.id})

    assert [robot.id] == [r.id for r in robots_find]
    assert all(r.realm is not None for r in robots_find)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2660")
def test_get_permission(auth_client, permission):
    perm_get = auth_client.get_permission(permission.id)

    assert perm_get.id == permission.id
    assert perm_get.realm is not None


def test_get_permission_not_found(auth_client):
    assert auth_client.get_permission(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2659")
def test_get_permissions(auth_client):
    perms_get = auth_client.get_permissions()

    assert len(perms_get) > 0
    assert all(p.realm is not None for p in perms_get)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2659")
def test_find_permissions(auth_client, permission):
    perms_find = auth_client.find_permissions(filter={"id": permission.id})

    assert [permission.id] == [p.id for p in perms_find]
    assert all(p.realm is not None for p in perms_find)


def test_update_permission(auth_client, permission):
    new_name = next_random_string()
    new_permission = auth_client.update_permission(permission.id, name=new_name)

    assert permission != new_permission
    assert new_permission.name == new_name


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2662")
def test_get_role(auth_client, role):
    role_get = auth_client.get_role(role.id)

    assert role_get.id == role.id
    assert role_get.realm is not None


def test_get_role_not_found(auth_client):
    assert auth_client.get_role(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2661")
def test_get_roles(auth_client, role):
    roles_get = auth_client.get_roles()

    assert len(roles_get) > 0
    assert all(r.realm is not None for r in roles_get)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2661")
def test_find_roles(auth_client, role):
    roles_find = auth_client.find_roles(filter={"id": role.id})

    assert [role.id] == [r.id for r in roles_find]
    assert all(r.realm is not None for r in roles_find)


def test_update_role(auth_client, role):
    new_name = next_random_string()
    new_role = auth_client.update_role(role.id, name=new_name)

    assert role != new_role
    assert new_role.name == new_name


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2643")
def test_get_role_permission(auth_client, role_permission):
    role_perm_get = auth_client.get_role_permission(role_permission.id)

    assert role_perm_get.id == role_permission.id
    assert role_perm_get.role is not None
    assert role_perm_get.permission is not None


def test_get_role_permission_not_found(auth_client):
    assert auth_client.get_role_permission(next_uuid()) is None


def test_get_role_permissions(auth_client, role_permission):
    role_perms_get = auth_client.get_role_permissions()

    assert len(role_perms_get) > 0
    assert all(rp.role is not None for rp in role_perms_get)
    assert all(rp.permission is not None for rp in role_perms_get)


def test_find_role_permissions(auth_client, role_permission):
    # Use "role_id" for filtering because there is no filter mechanism for attribute "id".
    role_perms_find = auth_client.find_role_permissions(filter={"role_id": role_permission.role_id})

    assert [role_permission.id] == [rp.id for rp in role_perms_find]
    assert all(rp.role is not None for rp in role_perms_find)
    assert all(rp.permission is not None for rp in role_perms_find)


def test_get_user(auth_client, user):
    user_get = auth_client.get_user(user.id)

    assert user_get.id == user.id
    assert user_get.realm is not None


def test_get_user_not_found(auth_client):
    assert auth_client.get_user(next_uuid()) is None


def test_get_users(auth_client, user):
    users_get = auth_client.get_users()

    assert len(users_get) > 0
    assert all(u.realm is not None for u in users_get)


def test_find_users(auth_client, user):
    users_find = auth_client.find_users(filter={"id": user.id})

    assert [user.id] == [u.id for u in users_find]
    assert all(u.realm is not None for u in users_find)


def test_update_user(auth_client, user):
    new_name = next_random_string()
    new_user = auth_client.update_user(user.id, name=new_name)

    assert user != new_user
    assert new_name == new_user.name


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2644")
def test_get_user_permission(auth_client, user_permission):
    user_perm_get = auth_client.get_user_permission(user_permission.id)

    assert user_perm_get.id == user_permission.id
    assert user_perm_get.user is not None
    assert user_perm_get.permission is not None


def test_get_user_permission_not_found(auth_client):
    assert auth_client.get_user_permission(next_uuid()) is None


def test_get_user_permissions(auth_client, user_permission):
    user_perms_get = auth_client.get_user_permissions()

    assert len(user_perms_get) > 0
    assert all(up.user is not None for up in user_perms_get)
    assert all(up.permission is not None for up in user_perms_get)


def test_find_user_permissions(auth_client, user_permission):
    # Use "user_id" for filtering because there is no filter mechanism for attribute "id".
    user_perms_find = auth_client.find_user_permissions(filter={"user_id": user_permission.user_id})

    assert len(user_perms_find) > 0
    assert all(up.user is not None for up in user_perms_find)
    assert all(up.permission is not None for up in user_perms_find)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2645")
def test_get_user_role(auth_client, user_role):
    user_role_get = auth_client.get_user_role(user_role.id)

    assert user_role_get.id == user_role.id
    assert user_role_get.user is not None
    assert user_role_get.role is not None


def test_get_user_role_not_found(auth_client):
    assert auth_client.get_user_role(next_uuid()) is None


def test_get_user_roles(auth_client, user_role):
    user_roles_get = auth_client.get_user_roles()

    assert len(user_roles_get) > 0
    assert all(ur.user is not None for ur in user_roles_get)
    assert all(ur.role is not None for ur in user_roles_get)


def test_find_user_roles(auth_client, user_role):
    # Use "user_id" for filtering because there is no filter mechanism for attribute "id".
    user_roles_find = auth_client.find_user_roles(filter={"user_id": user_role.user_id})

    assert len(user_roles_find) > 0
    assert all(ur.user is not None for ur in user_roles_find)
    assert all(ur.role is not None for ur in user_roles_find)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2647")
def test_get_robot_permission(auth_client, robot_permission):
    robot_perm_get = auth_client.get_robot_permission(robot_permission.id)

    assert robot_perm_get.id == robot_permission.id
    assert robot_perm_get.permission is not None
    assert robot_perm_get.robot is not None


def test_get_robot_permission_not_found(auth_client):
    assert auth_client.get_permission(next_uuid()) is None


def test_get_robot_permissions(auth_client, robot_permission):
    robot_perms_get = auth_client.get_robot_permissions()

    assert len(robot_perms_get) > 0
    assert all(rp.robot is not None for rp in robot_perms_get)
    assert all(rp.permission is not None for rp in robot_perms_get)


def test_find_robot_permissions(auth_client, robot_permission):
    # Use "robot_id" for filtering because there is no filter mechanism for attribute "id".
    robot_perms_find = auth_client.find_robot_permissions(filter={"robot_id": robot_permission.robot_id})

    assert [robot_permission.id] == [rp.id for rp in robot_perms_find]
    assert all(rp.robot is not None for rp in robot_perms_find)
    assert all(rp.permission is not None for rp in robot_perms_find)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2650")
def test_get_robot_role(auth_client, robot_role):
    robot_role_get = auth_client.get_robot_role(robot_role.id)

    assert robot_role_get.id == robot_role.id
    assert robot_role_get.robot is not None
    assert robot_role_get.role is not None


def test_get_robot_role_not_found(auth_client):
    assert auth_client.get_robot_role(next_uuid()) is None


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2649")
def test_get_robot_roles(auth_client, robot_role):
    robot_roles_get = auth_client.get_robot_roles()

    assert len(robot_roles_get) > 0
    assert all(rr.robot is not None for rr in robot_roles_get)
    assert all(rr.role is not None for rr in robot_roles_get)


@pytest.mark.xfail(reason="bug in authup, see https://github.com/authup/authup/issues/2649")
def test_find_robot_roles(auth_client, robot_role):
    # Use "robot_id" for filtering because there is no filter mechanism for attribute "id".
    robot_roles_find = auth_client.find_robot_roles(filter={"robot_id": robot_role.robot_id})

    assert [robot_role.id] == [rr.id for rr in robot_roles_find]
    assert all(rr.robot is not None for rr in robot_roles_find)
    assert all(rr.role is not None for rr in robot_roles_find)
