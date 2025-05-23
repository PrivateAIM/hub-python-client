import os
import string
import typing as t

import pytest

from flame_hub import HubAPIError
from flame_hub.types import NodeType
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
    default_master_image = os.getenv("PYTEST_DEFAULT_MASTER_IMAGE", "python/base")

    if len(core_client.find_master_images(filter={"path": default_master_image})) != 1:
        sync_master_images(core_client)

        def _check_default_master_image_available():
            assert len(core_client.find_master_images(filter={"path": default_master_image})) == 1

        assert_eventually(_check_default_master_image_available, max_retries=10, delay_millis=1000)

    return core_client.find_master_images(filter={"path": default_master_image})[0]


@pytest.fixture(scope="module")
def master_image_group(core_client, master_image):
    if len(core_client.find_master_image_groups(filter={"virtual_path": master_image.group_virtual_path})) != 1:
        sync_master_images(core_client)

        def _check_default_master_image_group_available():
            assert (
                len(core_client.find_master_image_groups(filter={"virtual_path": master_image.group_virtual_path})) == 1
            )

        assert_eventually(_check_default_master_image_group_available, max_retries=10, delay_millis=1000)

    return core_client.find_master_image_groups(filter={"virtual_path": master_image.group_virtual_path})[0]


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
def analysis(core_client, project, master_image):
    new_analysis = core_client.create_analysis(project, master_image_id=master_image.id)
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
    # Use the analysis bucket for code files so that the created bucket file can be used as an entrypoint to be able
    # to generate analysis logs.
    analysis_bucket = analysis_buckets["CODE"]

    # Upload example file to referenced bucket.
    bucket_files = storage_client.upload_to_bucket(
        analysis_bucket.external_id, {"file_name": next_random_string(), "content": rng_bytes}
    )

    # Link uploaded file to analysis bucket.
    new_analysis_bucket_file = core_client.create_analysis_bucket_file(
        next_random_string(), bucket_files.pop(), analysis_bucket, is_entrypoint=True
    )
    yield new_analysis_bucket_file
    core_client.delete_analysis_bucket_file(new_analysis_bucket_file)


@pytest.fixture()
def configured_analysis(core_client, registry, analysis, master_realm, analysis_bucket_file):
    # An analysis needs at least one default and one aggregator node.
    nodes = []
    for node_type in t.get_args(NodeType):
        new_node = core_client.create_node(
            name=next_random_string(),
            realm_id=master_realm,
            node_type=node_type,
            registry_id=registry.id,
        )
        nodes.append(new_node)
        core_client.create_project_node(analysis.project_id, new_node)
        core_client.create_analysis_node(analysis, new_node)
    core_client.send_analysis_command(analysis.id, command="configurationLock")
    return analysis


@pytest.fixture()
def analysis_log(core_client, configured_analysis):
    core_client.send_analysis_command(configured_analysis, "buildStart")

    def _check_analysis_logs_present():
        assert len(core_client.find_analysis_logs(filter={"analysis_id": configured_analysis.id})) > 0

    assert_eventually(_check_analysis_logs_present)

    return core_client.find_analysis_logs(filter={"analysis_id": configured_analysis.id})[0]


@pytest.fixture()
def analysis_node_log(core_client, analysis_node):
    new_analysis_node_log = core_client.create_analysis_node_log(
        analysis_node.analysis_id, analysis_node.node_id, error=False
    )
    yield new_analysis_node_log
    core_client.delete_analysis_node_log(new_analysis_node_log.id)


@pytest.fixture()
def registry(core_client):
    new_registry = core_client.create_registry(
        name=next_random_string(),
        host=next_random_string(),
        account_secret=next_random_string(),
    )
    yield new_registry
    core_client.delete_registry(new_registry)


@pytest.fixture()
def registry_fields():
    return ("account_secret",)


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


@pytest.fixture(scope="session")
def registry_project_fields():
    return "account_id", "account_name", "account_secret"


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


def test_get_master_image(core_client, master_image):
    assert master_image == core_client.get_master_image(master_image.id)


def test_get_master_images(core_client, master_image):
    assert len(core_client.get_master_images()) > 0


def test_get_master_image_group(core_client, master_image_group):
    assert master_image_group == core_client.get_master_image_group(master_image_group.id)


def test_get_master_image_groups(core_client, master_image_group):
    assert len(core_client.get_master_image_groups()) > 0


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
    project_nodes_get = core_client.get_project_nodes()

    assert len(project_nodes_get) > 0
    assert all(pn.project is not None for pn in project_nodes_get)
    assert all(pn.node is not None for pn in project_nodes_get)


def test_find_project_nodes(core_client, project_node):
    # Use "project_id" instead of "id" because filtering for ids does not work.
    project_nodes_find = core_client.find_project_nodes(filter={"project_id": project_node.project_id})

    assert [project_node.id] == [pn.id for pn in project_nodes_find]
    assert all(pn.project is not None for pn in project_nodes_find)
    assert all(pn.node is not None for pn in project_nodes_find)


def test_get_project_node(core_client, project_node):
    project_node_get = core_client.get_project_node(project_node.id)

    assert project_node_get.id == project_node.id
    assert project_node_get.project is not None
    assert project_node_get.node is not None


def test_update_project_node(core_client, project_node):
    new_comment = next_random_string()
    new_project_node = core_client.update_project_node(project_node.id, approval_status="rejected", comment=new_comment)

    assert new_project_node.approval_status == "rejected"
    assert new_project_node != project_node


def test_get_project_node_not_found(core_client):
    assert core_client.get_project_node(next_uuid()) is None


def test_get_analyses(core_client, analysis):
    analyses_get = core_client.get_analyses()

    assert len(analyses_get) > 0
    assert all(a.project is not None for a in analyses_get)


def test_find_analyses(core_client, analysis):
    analyses_find = core_client.find_analyses(filter={"id": analysis.id})

    assert [analysis.id] == [a.id for a in analyses_find]
    assert all(a.project is not None for a in analyses_find)


def test_get_analysis(core_client, analysis):
    analysis_get = core_client.get_analysis(analysis.id)

    assert analysis_get.id == analysis.id
    assert analysis_get.project is not None


def test_get_analysis_not_found(core_client):
    assert core_client.get_analysis(next_uuid()) is None


def test_update_analysis(core_client, analysis):
    new_name = next_random_string()
    new_analysis = core_client.update_analysis(analysis.id, name=new_name)

    assert analysis != new_analysis
    assert new_analysis.name == new_name


def test_unlock_analysis(core_client, configured_analysis):
    assert (
        core_client.send_analysis_command(configured_analysis.id, command="configurationUnlock").configuration_locked
        is False
    )
    assert (
        core_client.send_analysis_command(configured_analysis.id, command="configurationLock").configuration_locked
        is True
    )


def test_build_analysis(core_client, configured_analysis):
    assert core_client.send_analysis_command(configured_analysis.id, command="buildStart").build_status == "starting"
    assert core_client.send_analysis_command(configured_analysis.id, command="buildStop").build_status == "stopping"


def test_build_status_analysis(core_client, configured_analysis):
    core_client.send_analysis_command(configured_analysis.id, command="buildStart")
    core_client.send_analysis_command(configured_analysis.id, command="buildStatus")

    def _check_checking_event_in_logs():
        logs = core_client.find_analysis_logs(filter={"analysis_id": configured_analysis.id})
        assert "checking" in [log.event for log in logs]

    assert_eventually(_check_checking_event_in_logs)


def test_analysis_node_update(core_client, analysis_node):
    new_analysis_node = core_client.update_analysis_node(analysis_node.id, run_status="starting")

    assert analysis_node != new_analysis_node
    assert new_analysis_node.run_status == "starting"


def test_get_analysis_nodes(core_client, analysis_node):
    analysis_nodes_get = core_client.get_analysis_nodes()

    assert len(analysis_nodes_get) > 0
    assert all(an.analysis is not None for an in analysis_nodes_get)
    assert all(an.node is not None for an in analysis_nodes_get)


def test_find_analysis_nodes(core_client, analysis_node):
    # Use "analysis_id" instead of "id" because filtering for ids does not work.
    analysis_nodes_find = core_client.find_analysis_nodes(filter={"analysis_id": analysis_node.analysis_id})

    assert [analysis_node.id] == [an.id for an in analysis_nodes_find]
    assert all(an.analysis is not None for an in analysis_nodes_find)
    assert all(an.node is not None for an in analysis_nodes_find)


def test_get_analysis_node(core_client, analysis_node):
    analysis_node_get = core_client.get_analysis_node(analysis_node.id)

    assert analysis_node_get.id == analysis_node.id
    assert analysis_node_get.analysis is not None
    assert analysis_node.node is not None


def test_get_analysis_node_not_found(core_client):
    assert core_client.get_analysis_node(next_uuid()) is None


def test_get_analysis_node_log(core_client, analysis_node_log):
    assert analysis_node_log == core_client.get_analysis_node_log(analysis_node_log.id)


def test_get_analysis_node_log_not_found(core_client):
    assert core_client.get_analysis_node_log(next_uuid()) is None


def test_get_analysis_node_logs(core_client, analysis_node_log):
    assert len(core_client.get_analysis_node_logs()) > 0


def test_find_analysis_node_logs(core_client, analysis_node_log):
    # Use "node_id" for filtering because there is no filter mechanism for attribute "id".
    assert [analysis_node_log] == core_client.find_analysis_node_logs(filter={"node_id": analysis_node_log.node_id})


def test_update_analysis_node_log(core_client, analysis_node_log):
    new_status = next_random_string()
    new_analysis_node_log = core_client.update_analysis_node_log(analysis_node_log.id, status=new_status)

    assert new_analysis_node_log != analysis_node_log
    assert new_status == new_analysis_node_log.status


def test_get_analysis_bucket(core_client, analysis_buckets):
    analysis_bucket_get = core_client.get_analysis_bucket(analysis_buckets["CODE"].id)

    assert analysis_bucket_get.id == analysis_buckets["CODE"].id
    assert analysis_bucket_get.analysis is not None


def test_get_analysis_buckets(core_client, analysis_buckets):
    analysis_buckets_get = core_client.get_analysis_buckets()

    assert len(analysis_buckets_get) > 0
    assert all(ab.analysis is not None for ab in analysis_buckets_get)


def test_get_analysis_bucket_file(core_client, analysis_bucket_file):
    analysis_bucket_file_get = core_client.get_analysis_bucket_file(analysis_bucket_file.id)

    assert analysis_bucket_file_get.id == analysis_bucket_file.id
    assert analysis_bucket_file_get.analysis is not None
    assert analysis_bucket_file.bucket is not None


def test_get_analysis_bucket_file_not_found(core_client):
    assert core_client.get_analysis_bucket_file(next_uuid()) is None


def test_get_analysis_bucket_files(core_client, analysis_bucket_file):
    analysis_bucket_files_get = core_client.get_analysis_bucket_files()

    assert len(analysis_bucket_files_get) > 0
    assert all(abf.analysis is not None for abf in analysis_bucket_files_get)
    assert all(abf.bucket is not None for abf in analysis_bucket_files_get)


def test_find_analysis_bucket_files(core_client, analysis_bucket_file):
    # Use "analysis_id" instead of "id" because filtering for ids does not work.
    analysis_bucket_files_find = core_client.find_analysis_bucket_files(
        filter={"analysis_id": analysis_bucket_file.analysis_id}
    )

    assert [analysis_bucket_file.id] == [abf.id for abf in analysis_bucket_files_find]
    assert all(abf.analysis is not None for abf in analysis_bucket_files_find)
    assert all(abf.bucket is not None for abf in analysis_bucket_files_find)


def test_update_analysis_bucket_file(core_client, analysis_bucket_file):
    new_analysis_bucket_file = core_client.update_analysis_bucket_file(
        analysis_bucket_file.id, is_entrypoint=not analysis_bucket_file.root
    )

    assert new_analysis_bucket_file != analysis_bucket_file
    assert new_analysis_bucket_file.root is not analysis_bucket_file.root


def test_get_registry(core_client, registry, registry_fields):
    registry_get = core_client.get_registry(registry.id, fields=registry_fields)

    assert registry_get.id == registry.id
    assert all(field in registry_get.model_fields_set for field in registry_fields)


def test_get_registry_not_found(core_client):
    assert core_client.get_registry(next_uuid()) is None


def test_get_registries(core_client, registry, registry_fields):
    registries_get = core_client.get_registries(fields=registry_fields)

    assert len(registries_get) > 0
    assert all(field in r.model_fields_set for r in registries_get for field in registry_fields)


def test_find_registries(core_client, registry, registry_fields):
    registries_find = core_client.find_registries(filter={"id": registry.id}, fields=registry_fields)

    assert [registry.id] == [r.id for r in registries_find]
    assert all(field in r.model_fields_set for r in registries_find for field in registry_fields)


def test_update_registry(core_client, registry):
    new_name = next_random_string()
    new_registry = core_client.update_registry(registry.id, name=new_name)

    assert registry != new_registry
    assert new_registry.name == new_name


def test_registry_setup(core_client, registry):
    core_client.send_registry_command(registry.id, command="setup")

    def _check_setup():
        registry_projects = core_client.find_registry_projects(filter={"registry_id": registry.id})
        assert len(registry_projects) == 3
        assert {"incoming", "outgoing", "masterImages"} == set(rp.type for rp in registry_projects)

    assert_eventually(_check_setup)


def test_get_registry_project(core_client, registry_project, registry_project_fields):
    registry_project_get = core_client.get_registry_project(registry_project.id, fields=registry_project_fields)

    assert registry_project.id == registry_project_get.id
    assert registry_project_get.registry is not None
    assert all(field in registry_project_get.model_fields_set for field in registry_project_fields)


def test_get_registry_project_not_found(core_client, registry_project):
    assert core_client.get_registry_project(next_uuid()) is None


def test_get_project_registries(core_client, registry_project, registry_project_fields):
    registry_projects_get = core_client.get_registry_projects(fields=registry_project_fields)

    assert len(registry_projects_get) > 0
    assert all(rp.registry is not None for rp in registry_projects_get)
    assert all(field in rp.model_fields_set for rp in registry_projects_get for field in registry_project_fields)


def test_find_project_registries(core_client, registry_project, registry_project_fields):
    registry_projects_find = core_client.find_registry_projects(
        filter={"id": registry_project.id}, fields=registry_project_fields
    )

    assert [registry_project.id] == [rp.id for rp in registry_projects_find]
    assert all(rp.registry is not None for rp in registry_projects_find)
    assert all(field in rp.model_fields_set for rp in registry_projects_find for field in registry_project_fields)


def test_update_project_registry(core_client, registry_project):
    new_name = next_random_string()
    new_registry_project = core_client.update_registry_project(registry_project.id, name=new_name)

    assert registry_project != new_registry_project
    assert new_registry_project.name == new_name


def test_get_analysis_log(core_client, analysis_log):
    analysis_log_get = core_client.get_analysis_log(analysis_log.id)

    assert analysis_log_get.id == analysis_log.id
    assert analysis_log_get.analysis is not None


def test_get_analysis_log_not_found(core_client):
    assert core_client.get_analysis_log(next_uuid()) is None


def test_get_analysis_logs(core_client, analysis_log):
    analysis_logs_get = core_client.get_analysis_logs()

    assert len(analysis_logs_get) > 0
    assert all(al.analysis is not None for al in analysis_logs_get)


def test_delete_analysis_log(core_client, analysis_log):
    core_client.delete_analysis_log(analysis_log.id)
    assert core_client.get_analysis_log(analysis_log.id) is None
