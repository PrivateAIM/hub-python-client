import pytest

from tests.helpers import next_random_string, next_uuid

pytestmark = pytest.mark.integration


@pytest.fixture()
def realm(auth_client):
    new_realm = auth_client.create_realm(next_random_string())
    yield new_realm
    auth_client.delete_realm(new_realm)


def test_get_realm(auth_client, realm):
    assert realm == auth_client.get_realm(realm.id)


def test_get_realm_not_found(auth_client, realm):
    assert auth_client.get_realm(next_uuid()) is None


def test_update_realm(auth_client, realm):
    new_name = next_random_string()
    new_realm = auth_client.update_realm(realm.id, name=new_name)

    assert realm != new_realm
    assert new_realm.name == new_name
