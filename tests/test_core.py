import os
import string

import pytest

from tests.helpers import next_random_string, next_uuid


@pytest.fixture(scope="module")
def master_image(core_client):
    default_master_image = os.getenv("PYTEST_DEFAULT_MASTER_IMAGE", "python/base")
    master_images = [i for i in core_client.get_master_images().data if i.path == default_master_image]

    if len(master_images) != 1:
        raise ValueError(f"expected single master image named {default_master_image}, found {len(master_images)}")

    return master_images[0]


@pytest.fixture()
def node(core_client, master_realm):
    new_node = core_client.create_node(next_random_string(), master_realm)
    yield new_node
    core_client.delete_node(new_node)


@pytest.fixture()
def project(core_client, master_image):
    new_project = core_client.create_project(next_random_string(), master_image)
    yield new_project
    core_client.delete_project(new_project)


@pytest.fixture()
def project_node(core_client, node, project):
    new_project_node = core_client.create_project_node(project, node)
    yield new_project_node
    core_client.delete_project_node(new_project_node)


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


def test_get_projects(core_client, project):
    assert any(p.id == project.id for p in core_client.get_projects().data)


def test_get_project(core_client, project):
    assert project == core_client.get_project(project.id)


def test_get_project_not_found(core_client):
    assert core_client.get_project(next_uuid()) is None


def test_update_project(core_client, project):
    new_name = next_random_string()
    new_node = core_client.update_project(project.id, name=new_name)

    assert project != new_node
    assert new_node.name == new_name


def test_get_project_nodes(core_client, project_node):
    assert any(project_node.id == pn.id for pn in core_client.get_project_nodes().data)


def test_get_project_node(core_client, project_node):
    assert project_node == core_client.get_project_node(project_node.id)
