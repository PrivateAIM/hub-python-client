import string

import pytest

from tests.helpers import next_random_string, next_uuid


@pytest.fixture()
def node(core_client, master_realm):
    new_node = core_client.create_node(next_random_string(), master_realm)
    yield new_node
    core_client.delete_node(new_node)


def test_get_nodes(core_client, node):
    assert any(node.id == n.id for n in core_client.get_nodes().data)


def test_get_node(core_client, node):
    assert node == core_client.get_node(node.id)


def test_get_node_not_found(core_client):
    assert core_client.get_node(next_uuid()) is None


def test_update_node(core_client, node):
    # only accepts lowercase letters and numbers
    new_name = next_random_string(charset=string.ascii_lowercase + string.digits)
    new_node = core_client.update_node(node.id, external_name=new_name)

    assert node != new_node
    assert new_node.external_name == new_name


def test_get_master_images(core_client):
    _ = core_client.get_master_images()


def test_get_master_image_groups(core_client):
    _ = core_client.get_master_image_groups()
