import os
import random
import string
import typing as t

import pytest

from flame_hub import HubAPIError, get_field_names, get_includable_names
from flame_hub.types import NodeType
from flame_hub.models import (
    Registry,
    RegistryProject,
    Node,
    Project,
    ProjectNode,
    Analysis,
    AnalysisNode,
    AnalysisBucket,
    AnalysisBucketFile,
)
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


@pytest.fixture()
def node(core_client, master_realm):
    new_node = core_client.create_node(next_random_string(), master_realm)
    yield new_node
    core_client.delete_node(new_node)


@pytest.fixture(scope="session")
def node_includables():
    return get_includable_names(Node)


@pytest.fixture()
def project(core_client, master_image):
    new_project = core_client.create_project(next_random_string())
    yield new_project
    core_client.delete_project(new_project)


@pytest.fixture(scope="session")
def project_includables():
    return get_includable_names(Project)


@pytest.fixture()
def project_node(core_client, node, project):
    new_project_node = core_client.create_project_node(project, node)
    yield new_project_node
    core_client.delete_project_node(new_project_node)


@pytest.fixture(scope="session")
def project_node_includables():
    return get_includable_names(ProjectNode)


@pytest.fixture()
def analysis(core_client, project, master_image):
    args = [
        {"value": next_random_string()},
        {"value": next_random_string(), "position": random.choice(("before", "after"))},
    ]
    new_analysis = core_client.create_analysis(
        project,
        master_image_id=master_image.id,
        image_command_arguments=args,
    )
    yield new_analysis
    core_client.delete_analysis(new_analysis)


@pytest.fixture(scope="session")
def analysis_includables():
    return get_includable_names(Analysis)


@pytest.fixture()
def analysis_node(core_client, analysis, project_node):
    new_analysis_node = core_client.create_analysis_node(analysis.id, project_node.node_id)
    yield new_analysis_node
    core_client.delete_analysis_node(new_analysis_node)


@pytest.fixture(scope="session")
def analysis_node_includables():
    return get_includable_names(AnalysisNode)


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


@pytest.fixture(scope="session")
def analysis_bucket_includables():
    return get_includable_names(AnalysisBucket)


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


@pytest.fixture(scope="session")
def analysis_bucket_file_includables():
    return get_includable_names(AnalysisBucketFile)


@pytest.fixture()
def configured_analysis(core_client, registry, analysis, master_realm, analysis_bucket_file):
    # An analysis needs at least one default node,  one aggregator node, a base image and an entrypoint to be lockable.
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

    # It takes some time until an analysis is lockable.
    def _check_analysis_lockable():
        try:
            core_client.send_analysis_command(analysis.id, command="configurationLock")
        except HubAPIError as e:
            assert False, e
        else:
            assert True

    assert_eventually(_check_analysis_lockable)

    yield analysis

    for node in nodes:
        core_client.delete_node(node)


@pytest.fixture()
def analysis_log(core_client, configured_analysis):
    core_client.send_analysis_command(configured_analysis, "buildStart")

    def _check_analysis_logs_present():
        assert len(core_client.find_analysis_logs(filter={"analysis_id": configured_analysis.id})) > 0

    assert_eventually(_check_analysis_logs_present)

    return core_client.find_analysis_logs(filter={"analysis_id": configured_analysis.id})[0]


@pytest.fixture()
def registry(core_client):
    new_registry = core_client.create_registry(
        name=next_random_string(),
        host=next_random_string(),
        account_secret=next_random_string(),
    )
    yield new_registry
    core_client.delete_registry(new_registry)


@pytest.fixture(scope="session")
def registry_fields():
    return get_field_names(Registry)


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
    return get_field_names(RegistryProject)


@pytest.fixture(scope="session")
def registry_project_includables():
    return get_includable_names(RegistryProject)


def test_get_nodes(core_client, node, node_includables):
    nodes_get = core_client.get_nodes()

    assert len(nodes_get) > 0
    assert all(includable in n.model_fields_set for n in nodes_get for includable in node_includables)


def test_get_node(core_client, node, node_includables):
    node_get = core_client.get_node(node.id)

    assert node_get.id == node.id
    assert all(includable in node_get.model_fields_set for includable in node_includables)


def test_find_nodes(core_client, node, node_includables):
    nodes_find = core_client.find_nodes(filter={"id": node.id})

    assert [n.id for n in nodes_find] == [node.id]
    assert all(includable in n.model_fields_set for n in nodes_find for includable in node_includables)


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


def test_get_projects(core_client, project, project_includables):
    projects_get = core_client.get_projects()

    assert len(projects_get) > 0
    assert all(includable in p.model_fields_set for p in projects_get for includable in project_includables)


def test_find_projects(core_client, project, project_includables):
    projects_find = core_client.find_projects(filter={"id": project.id})

    assert [project.id] == [p.id for p in projects_find]
    assert all(includable in p.model_fields_set for p in projects_find for includable in project_includables)


def test_get_project(core_client, project, project_includables):
    project_get = core_client.get_project(project.id)

    assert project_get.id == project.id
    assert all(includable in project_get.model_fields_set for includable in project_includables)


def test_get_project_not_found(core_client):
    assert core_client.get_project(next_uuid()) is None


def test_update_project(core_client, project):
    new_name = next_random_string()
    new_node = core_client.update_project(project.id, name=new_name)

    assert project != new_node
    assert new_node.name == new_name


def test_get_project_nodes(core_client, project_node, project_node_includables):
    project_nodes_get = core_client.get_project_nodes()

    assert len(project_nodes_get) > 0
    assert all(includable in pn.model_fields_set for pn in project_nodes_get for includable in project_node_includables)


def test_find_project_nodes(core_client, project_node, project_node_includables):
    # Use "project_id" instead of "id" because filtering for ids does not work.
    project_nodes_find = core_client.find_project_nodes(filter={"project_id": project_node.project_id})

    assert [project_node.id] == [pn.id for pn in project_nodes_find]
    assert all(
        includable in pn.model_fields_set for pn in project_nodes_find for includable in project_node_includables
    )


def test_get_project_node(core_client, project_node, project_node_includables):
    project_node_get = core_client.get_project_node(project_node.id)

    assert project_node_get.id == project_node.id
    assert all(includable in project_node_get.model_fields_set for includable in project_node_includables)


def test_update_project_node(core_client, project_node):
    new_comment = next_random_string()
    new_project_node = core_client.update_project_node(project_node.id, approval_status="rejected", comment=new_comment)

    assert new_project_node.approval_status == "rejected"
    assert new_project_node != project_node


def test_get_project_node_not_found(core_client):
    assert core_client.get_project_node(next_uuid()) is None


@pytest.mark.xfail(reason="bug in FLAME hub")
def test_get_analyses(core_client, analysis, analysis_includables):
    analyses_get = core_client.get_analyses()

    assert len(analyses_get) > 0
    assert all(includable in a.model_fields_set for a in analyses_get for includable in analysis_includables)


@pytest.mark.xfail(reason="bug in FLAME hub")
def test_find_analyses(core_client, analysis, analysis_includables):
    analyses_find = core_client.find_analyses(filter={"id": analysis.id})

    assert [analysis.id] == [a.id for a in analyses_find]
    assert all(includable in a.model_fields_set for a in analyses_find for includable in analysis_includables)


@pytest.mark.xfail(reason="bug in FLAME hub")
def test_get_analysis(core_client, analysis, analysis_includables):
    analysis_get = core_client.get_analysis(analysis.id)

    assert analysis_get.id == analysis.id
    assert all(includable in analysis_get.model_fields_set for includable in analysis_includables)


def test_get_analysis_not_found(core_client):
    assert core_client.get_analysis(next_uuid()) is None


def test_update_analysis(core_client, analysis):
    args = [
        {"value": next_random_string()},
        {"value": next_random_string(), "position": random.choice(("before", "after"))},
    ]
    new_name = next_random_string()
    new_analysis = core_client.update_analysis(analysis.id, name=new_name, image_command_arguments=args)

    assert analysis != new_analysis
    assert new_analysis.name == new_name
    assert new_analysis.image_command_arguments == args  # Note that args is modified during updating the analysis.


def test_create_analysis_without_arguments(core_client, project):
    analysis = core_client.create_analysis(project_id=project.id, image_command_arguments=None)

    assert analysis.image_command_arguments == []

    core_client.delete_analysis(analysis)


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
        assert "configured" in [log.labels.get("event", None) for log in logs]

    assert_eventually(_check_checking_event_in_logs)


def test_update_analysis_node(core_client, analysis_node):
    new_analysis_node = core_client.update_analysis_node(
        analysis_node.id,
        run_status="starting",
    )

    assert analysis_node != new_analysis_node
    assert new_analysis_node.run_status == "starting"


def test_get_analysis_nodes(core_client, analysis_node, analysis_node_includables):
    analysis_nodes_get = core_client.get_analysis_nodes()

    assert len(analysis_nodes_get) > 0
    assert all(
        includable in an.model_fields_set for an in analysis_nodes_get for includable in analysis_node_includables
    )


def test_find_analysis_nodes(core_client, analysis_node, analysis_node_includables):
    # Use "analysis_id" instead of "id" because filtering for ids does not work.
    analysis_nodes_find = core_client.find_analysis_nodes(filter={"analysis_id": analysis_node.analysis_id})

    assert [analysis_node.id] == [an.id for an in analysis_nodes_find]
    assert all(
        includable in an.model_fields_set for an in analysis_nodes_find for includable in analysis_node_includables
    )


def test_get_analysis_node(core_client, analysis_node, analysis_node_includables):
    analysis_node_get = core_client.get_analysis_node(analysis_node.id)

    assert analysis_node_get.id == analysis_node.id
    assert all(includable in analysis_node_get.model_fields_set for includable in analysis_node_includables)


def test_get_analysis_node_not_found(core_client):
    assert core_client.get_analysis_node(next_uuid()) is None


def test_analysis_node_logs(core_client, analysis_node):
    core_client.create_analysis_node_log(
        analysis_id=analysis_node.analysis_id, node_id=analysis_node.node_id, level="info", message="test"
    )

    def _check_analysis_node_logs_present():
        assert (
            len(
                core_client.find_analysis_node_logs(
                    filter={"analysis_id": analysis_node.analysis_id, "node_id": analysis_node.node_id}
                )
            )
            == 1
        )

    assert_eventually(_check_analysis_node_logs_present)

    # TODO: Deleting analysis node logs raises am error in the hub.
    # core_client.delete_analysis_node_logs(
    #    analysis_id=analysis_node.analysis_id, node_id=analysis_node.node_id
    # )

    # assert len(core_client.find_analysis_node_logs(
    #    filter={"analysis_id": analysis_node.analysis_id, "node_id": analysis_node.node_id}
    # )) == 0


def test_get_analysis_bucket(core_client, analysis_buckets, analysis_bucket_includables):
    analysis_bucket_get = core_client.get_analysis_bucket(analysis_buckets["CODE"].id)

    assert analysis_bucket_get.id == analysis_buckets["CODE"].id
    assert all(includable in analysis_bucket_get.model_fields_set for includable in analysis_bucket_includables)


def test_get_analysis_buckets(core_client, analysis_buckets, analysis_bucket_includables):
    analysis_buckets_get = core_client.get_analysis_buckets()

    assert len(analysis_buckets_get) > 0
    assert all(
        includable in ab.model_fields_set for ab in analysis_buckets_get for includable in analysis_bucket_includables
    )


def test_get_analysis_bucket_file(core_client, analysis_bucket_file, analysis_bucket_file_includables):
    analysis_bucket_file_get = core_client.get_analysis_bucket_file(analysis_bucket_file.id)

    assert analysis_bucket_file_get.id == analysis_bucket_file.id
    assert all(
        includable in analysis_bucket_file_get.model_fields_set for includable in analysis_bucket_file_includables
    )


def test_get_analysis_bucket_file_not_found(core_client):
    assert core_client.get_analysis_bucket_file(next_uuid()) is None


def test_get_analysis_bucket_files(core_client, analysis_bucket_file, analysis_bucket_file_includables):
    analysis_bucket_files_get = core_client.get_analysis_bucket_files()

    assert len(analysis_bucket_files_get) > 0
    assert all(
        includable in abf.model_fields_set
        for abf in analysis_bucket_files_get
        for includable in analysis_bucket_file_includables
    )


def test_find_analysis_bucket_files(core_client, analysis_bucket_file, analysis_bucket_file_includables):
    # Use "analysis_id" instead of "id" because filtering for ids does not work.
    analysis_bucket_files_find = core_client.find_analysis_bucket_files(
        filter={"analysis_id": analysis_bucket_file.analysis_id}
    )

    assert [analysis_bucket_file.id] == [abf.id for abf in analysis_bucket_files_find]
    assert all(
        includable in abf.model_fields_set
        for abf in analysis_bucket_files_find
        for includable in analysis_bucket_file_includables
    )


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


def test_get_registry_project(core_client, registry_project, registry_project_fields, registry_project_includables):
    registry_project_get = core_client.get_registry_project(registry_project.id, fields=registry_project_fields)

    assert registry_project.id == registry_project_get.id
    assert all(includable in registry_project_get.model_fields_set for includable in registry_project_includables)
    assert all(field in registry_project_get.model_fields_set for field in registry_project_fields)


def test_get_registry_project_not_found(core_client, registry_project):
    assert core_client.get_registry_project(next_uuid()) is None


def test_get_registry_projects(core_client, registry_project, registry_project_fields, registry_project_includables):
    registry_projects_get = core_client.get_registry_projects(fields=registry_project_fields)

    assert len(registry_projects_get) > 0
    assert all(
        includable in rp.model_fields_set for rp in registry_projects_get for includable in registry_project_includables
    )
    assert all(field in rp.model_fields_set for rp in registry_projects_get for field in registry_project_fields)


def test_find_registry_projects(core_client, registry_project, registry_project_fields, registry_project_includables):
    registry_projects_find = core_client.find_registry_projects(
        filter={"id": registry_project.id}, fields=registry_project_fields
    )

    assert [registry_project.id] == [rp.id for rp in registry_projects_find]
    assert all(
        includable in rp.model_fields_set
        for rp in registry_projects_find
        for includable in registry_project_includables
    )
    assert all(field in rp.model_fields_set for rp in registry_projects_find for field in registry_project_fields)


def test_update_registry_project(core_client, registry_project):
    new_name = next_random_string()
    new_registry_project = core_client.update_registry_project(registry_project.id, name=new_name)

    assert registry_project != new_registry_project
    assert new_registry_project.name == new_name


@pytest.mark.xfail(reason="Bug in Hub, see https://github.com/PrivateAIM/hub/issues/1181.")
def test_delete_analysis_logs(core_client, analysis_log):
    core_client.delete_analysis_logs(analysis_id=analysis_log.labels["analysis_id"])

    assert len(core_client.find_analysis_logs(filter={"analysis_id": analysis_log.labels["analysis_id"]})) == 0
