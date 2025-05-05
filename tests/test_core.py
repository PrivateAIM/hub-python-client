import os
import string

import pytest

from flame_hub import HubAPIError
from tests.helpers import next_random_string, next_uuid, assert_eventually

pytestmark = pytest.mark.integration


def sync_master_images(core_client):
    try:
        core_client.sync_master_images()
    except HubAPIError as e:
        # ignore if command is locked, means the hub is probably syncing right now
        if not e.error_response.message.startswith("The command is locked"):
            # otherwise this is an unknown error and should be raised
            raise e


@pytest.fixture(scope="module")
def master_image(core_client):
    if len(core_client.get_master_images()) == 0:
        sync_master_images(core_client)

        def _check_master_images_available():
            assert len(core_client.get_master_images()) > 0

        assert_eventually(_check_master_images_available, max_retries=10, delay_millis=1000)

    default_master_image = os.getenv("PYTEST_DEFAULT_MASTER_IMAGE", "python/base")
    master_images = core_client.find_master_images(filter={"path": default_master_image})

    if len(master_images) != 1:
        raise ValueError(f"expected single master image named {default_master_image}, found {len(master_images)}")

    return master_images[0]


@pytest.fixture(scope="module")
def master_image_event_log(core_client):
    if len(core_client.get_master_image_event_logs()) == 0:
        sync_master_images(core_client)

        def _check_master_image_event_logs_available():
            assert len(core_client.get_master_image_event_logs()) > 0

        assert_eventually(_check_master_image_event_logs_available, max_retries=10, delay_millis=1000)

    return core_client.get_master_image_event_logs()[0]


@pytest.fixture()
def node(core_client, master_realm):
    new_node = core_client.create_node(next_random_string(), master_realm)
    yield new_node
    core_client.delete_node(new_node)


@pytest.fixture()
def project(core_client, master_image):
    new_project = core_client.create_project(next_random_string())
    yield new_project
    core_client.delete_project(new_project)


@pytest.fixture()
def project_node(core_client, node, project):
    new_project_node = core_client.create_project_node(project, node)
    yield new_project_node
    core_client.delete_project_node(new_project_node)


@pytest.fixture()
def analysis(core_client, project):
    new_analysis = core_client.create_analysis(project)
    yield new_analysis
    core_client.delete_analysis(new_analysis)


@pytest.fixture()
def analysis_node(core_client, analysis, project_node):
    new_analysis_node = core_client.create_analysis_node(analysis.id, project_node.node_id)
    yield new_analysis_node
    core_client.delete_analysis_node(new_analysis_node)


@pytest.fixture()
def analysis_buckets(core_client, analysis):
    def _check_analysis_buckets_present():
        all_analysis_bucket_types = {"CODE", "RESULT", "TEMP"}

        # Constrain to buckets created for this analysis.
        analysis_buckets = core_client.find_analysis_buckets(filter={"analysis_id": analysis.id})
        assert len(analysis_buckets) == len(all_analysis_bucket_types)

        # Check that a bucket for each type exists.
        analysis_bucket_types = set(a.type for a in analysis_buckets)
        assert all_analysis_bucket_types == analysis_bucket_types

    assert_eventually(_check_analysis_buckets_present)

    return {
        analysis_bucket.type: analysis_bucket
        for analysis_bucket in core_client.find_analysis_buckets(filter={"analysis_id": analysis.id})
    }


@pytest.fixture()
def analysis_bucket_file(core_client, storage_client, analysis_buckets, rng_bytes):
    # Type was chosen arbitrarily.
    analysis_bucket = analysis_buckets["CODE"]

    # Upload example file to referenced bucket.
    bucket_files = storage_client.upload_to_bucket(
        analysis_bucket.external_id, {"file_name": next_random_string(), "content": rng_bytes}
    )

    # Link uploaded file to analysis bucket.
    new_analysis_bucket_file = core_client.create_analysis_bucket_file(
        next_random_string(), bucket_files.pop(), analysis_bucket
    )
    yield new_analysis_bucket_file
    core_client.delete_analysis_bucket_file(new_analysis_bucket_file)


@pytest.fixture()
def registry(core_client):
    new_registry = core_client.create_registry(name=next_random_string(), host=next_random_string())
    yield new_registry
    core_client.delete_registry(new_registry)


@pytest.fixture()
def registry_project(core_client, registry):
    new_registry_project = core_client.create_registry_project(
        name=next_random_string(),
        registry_project_type="default",
        registry_id=registry,
        external_name=next_random_string(charset=string.ascii_lowercase + string.digits),
    )
    yield new_registry_project
    core_client.delete_registry_project(new_registry_project)


def test_get_nodes(core_client, node):
    assert len(core_client.get_nodes()) > 0


def test_get_node(core_client, node):
    assert node == core_client.get_node(node.id)


def test_find_nodes(core_client, node):
    assert core_client.find_nodes(filter={"id": node.id}) == [node]


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


def test_get_master_image_event_log(core_client, master_image_event_log):
    assert master_image_event_log == core_client.get_master_image_event_log(master_image_event_log.id)


def test_get_master_image_event_logs(core_client):
    _ = core_client.get_master_image_event_logs()


def test_find_master_image_event_logs(core_client, master_image_event_log):
    # Use "name" for filtering because there is no filter mechanism for attribute "id".
    assert master_image_event_log in core_client.find_master_image_event_logs(
        filter={"name": master_image_event_log.name}
    )


def test_get_projects(core_client, project):
    assert len(core_client.get_projects()) > 0


def test_find_projects(core_client, project):
    assert core_client.find_projects(filter={"id": project.id}) == [project]


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
    assert len(core_client.get_project_nodes()) > 0


def test_find_project_nodes(core_client, project_node):
    assert core_client.find_project_nodes(filter={"id": project_node.id}) == [project_node]


def test_get_project_node(core_client, project_node):
    assert project_node == core_client.get_project_node(project_node.id)


def test_update_project_node(core_client, project_node):
    new_comment = next_random_string()
    new_project_node = core_client.update_project_node(project_node.id, approval_status="rejected", comment=new_comment)

    assert new_project_node.approval_status == "rejected"
    assert new_project_node != project_node


def test_get_project_node_not_found(core_client):
    assert core_client.get_project_node(next_uuid()) is None


def test_get_analyses(core_client, analysis):
    assert len(core_client.get_analyses()) > 0


def test_find_analyses(core_client, analysis):
    assert core_client.find_analyses(filter={"id": analysis.id}) == [analysis]


def test_get_analysis(core_client, analysis):
    assert analysis == core_client.get_analysis(analysis.id)


def test_get_analysis_not_found(core_client):
    assert core_client.get_analysis(next_uuid()) is None


def test_update_analysis(core_client, analysis):
    new_name = next_random_string()
    new_analysis = core_client.update_analysis(analysis.id, name=new_name)

    assert analysis != new_analysis
    assert new_analysis.name == new_name


def test_analysis_node_update(core_client, analysis_node):
    new_analysis_node = core_client.update_analysis_node(analysis_node.id, run_status="starting")

    assert analysis_node != new_analysis_node
    assert new_analysis_node.run_status == "starting"


def test_get_analysis_nodes(core_client, analysis_node):
    assert len(core_client.get_analysis_nodes()) > 0


def test_find_analysis_nodes(core_client, analysis_node):
    assert core_client.find_analysis_nodes(filter={"id": analysis_node.id}) == [analysis_node]


def test_get_analysis_node(core_client, analysis_node):
    assert analysis_node == core_client.get_analysis_node(analysis_node.id)


def test_get_analysis_bucket(core_client, analysis_buckets):
    assert analysis_buckets["CODE"] == core_client.get_analysis_bucket(analysis_buckets["CODE"])


def test_get_analysis_buckets(core_client, analysis_buckets):
    assert len(core_client.get_analysis_buckets()) > 0


def test_get_analysis_bucket_file(core_client, analysis_bucket_file):
    assert analysis_bucket_file == core_client.get_analysis_bucket_file(analysis_bucket_file.id)


# TODO: Uncomment this when hub fixes requests for non-existent analysis bucket files.
# def test_get_analysis_bucket_file_not_found(core_client):
#    assert core_client.get_analysis_bucket_file(next_uuid()) is None


def test_get_analysis_bucket_files(core_client, analysis_bucket_file):
    assert len(core_client.get_analysis_bucket_files()) > 0


def test_find_analysis_bucket_files(core_client, analysis_bucket_file):
    assert [analysis_bucket_file] == core_client.find_analysis_bucket_files(filter={"id": analysis_bucket_file.id})


def test_update_analysis_bucket_file(core_client, analysis_bucket_file):
    new_analysis_bucket_file = core_client.update_analysis_bucket_file(analysis_bucket_file.id, is_entrypoint=True)

    assert new_analysis_bucket_file != analysis_bucket_file
    assert new_analysis_bucket_file.root is True


def test_get_registry(core_client, registry):
    assert registry == core_client.get_registry(registry.id)


def test_get_registry_not_found(core_client):
    assert core_client.get_registry(next_uuid()) is None


def test_get_registries(core_client, registry):
    assert len(core_client.get_registries()) > 0


def test_find_registries(core_client, registry):
    assert [registry] == core_client.find_registries(filter={"id": registry.id})


def test_update_registry(core_client, registry):
    new_name = next_random_string()
    new_registry = core_client.update_registry(registry.id, name=new_name)

    assert registry != new_registry
    assert new_registry.name == new_name


def test_get_registry_project(core_client, registry_project):
    assert registry_project == core_client.get_registry_project(registry_project.id)


def test_get_registry_project_not_found(core_client, registry_project):
    assert core_client.get_registry_project(next_uuid()) is None


def test_get_project_registries(core_client, registry_project):
    assert len(core_client.get_registry_projects()) > 0


def test_find_project_registries(core_client, registry_project):
    assert [registry_project] == core_client.find_registry_projects(filter={"id": registry_project.id})


def test_update_project_registry(core_client, registry_project):
    new_name = next_random_string()
    new_registry_project = core_client.update_registry_project(registry_project.id, name=new_name)

    assert registry_project != new_registry_project
    assert new_registry_project.name == new_name
