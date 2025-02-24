__all__ = ["CoreClient"]

import typing as t
import uuid
from datetime import datetime
from enum import Enum

import httpx
from pydantic import BaseModel

from flame_hub.auth import Realm
from flame_hub.base_client import BaseClient, ResourceList, obtain_uuid_from
from flame_hub.common import merge_parse_result, join_url_path
from flame_hub.defaults import DEFAULT_CORE_BASE_URL
from flame_hub.flow import PasswordAuth, RobotAuth


class NodeType(str, Enum):
    aggregator = "aggregator"
    default = "default"


class CreateNode(BaseModel):
    external_name: str | None
    hidden: bool
    name: str
    realm_id: uuid.UUID
    registry_id: uuid.UUID | None
    type: NodeType


class Node(CreateNode):
    id: uuid.UUID
    public_key: str | None
    online: bool
    registry_project_id: uuid.UUID | None
    robot_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UpdateNode(BaseModel):
    hidden: bool | None
    external_name: str | None
    type: NodeType | None
    public_key: str | None
    realm_id: uuid.UUID | None


class MasterImageGroup(BaseModel):
    id: uuid.UUID
    name: str
    path: str
    virtual_path: str
    command: str | None
    command_arguments: t.Any
    created_at: datetime
    updated_at: datetime


class MasterImage(BaseModel):
    id: uuid.UUID
    path: str | None
    virtual_path: str
    group_virtual_path: str
    name: str
    command: str | None
    created_at: datetime
    updated_at: datetime


class CreateProject(BaseModel):
    description: str | None
    master_image_id: uuid.UUID
    name: str


class Project(CreateProject):
    id: uuid.UUID
    analyses: int
    nodes: int
    created_at: datetime
    updated_at: datetime
    realm_id: uuid.UUID
    user_id: uuid.UUID | None
    robot_id: uuid.UUID | None


class UpdateProject(BaseModel):
    description: str | None
    master_image_id: uuid.UUID | None
    name: str | None


class ProjectNodeApprovalStatus(str, Enum):
    rejected = "rejected"
    approved = "approved"


class CreateProjectNode(BaseModel):
    node_id: uuid.UUID
    project_id: uuid.UUID


class ProjectNode(CreateProjectNode):
    id: uuid.UUID
    approval_status: ProjectNodeApprovalStatus
    comment: str | None
    created_at: datetime
    updated_at: datetime
    project_realm_id: uuid.UUID
    node_realm_id: uuid.UUID


class AnalysisBuildStatus(str, Enum):
    starting = "starting"
    started = "started"
    stopping = "stopping"
    stopped = "stopped"
    finished = "finished"
    failed = "failed"


class AnalysisRunStatus(str, Enum):
    starting = "starting"
    started = "started"
    running = "running"
    stopping = "stopping"
    stopped = "stopped"
    finished = "finished"
    failed = "failed"


class CreateAnalysis(BaseModel):
    description: str | None
    name: str
    project_id: uuid.UUID


class Analysis(CreateAnalysis):
    id: uuid.UUID
    configuration_locked: bool
    build_status: AnalysisBuildStatus | None
    run_status: AnalysisRunStatus | None
    created_at: datetime
    updated_at: datetime
    registry_id: uuid.UUID | None
    realm_id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    master_image_id: uuid.UUID


class CoreClient(BaseClient):
    def __init__(
        self,
        base_url: str = DEFAULT_CORE_BASE_URL,
        client: httpx.Client = None,
        auth: t.Union[PasswordAuth, RobotAuth] = None,
    ):
        super().__init__(base_url, client, auth)

    def get_nodes(self) -> ResourceList[Node]:
        return self._get_all_resources(Node, "nodes")

    def create_node(
        self,
        name: str,
        realm_id: t.Union[Realm, str, uuid.UUID],
        external_name: str | None = None,
        node_type: NodeType = NodeType.default,
        hidden: bool = False,
    ) -> Node:
        return self._create_resource(
            Node,
            CreateNode(
                name=name,
                realm_id=str(obtain_uuid_from(realm_id)),
                external_name=external_name,
                hidden=hidden,
                registry_id=None,  # TODO add registries
                type=node_type,
            ),
            "nodes",
        )

    def get_node(self, node_id: t.Union[Node, uuid.UUID, str]) -> Node | None:
        return self._get_single_resource(Node, node_id, "nodes")

    def delete_node(self, node_id: t.Union[Node, uuid.UUID, str]):
        self._delete_resource(node_id, "nodes")

    def update_node(
        self,
        node_id: t.Union[Node, uuid.UUID, str],
        external_name: str = None,
        hidden: bool = None,
        node_type: NodeType = None,
        realm_id: t.Union[Realm, str, uuid.UUID] = None,
        public_key: str = None,
    ) -> Node:
        return self._update_resource(
            Node,
            node_id,
            UpdateNode(
                external_name=external_name,
                hidden=hidden,
                type=node_type,
                public_key=public_key,
                realm_id=str(obtain_uuid_from(realm_id)) if realm_id else None,
            ),
            "nodes",
        )

    def get_master_image_groups(self) -> ResourceList[MasterImageGroup]:
        return self._get_all_resources(MasterImageGroup, "master-image-groups")

    def get_master_images(self) -> ResourceList[MasterImage]:
        return self._get_all_resources(MasterImage, "master-images")

    def get_projects(self) -> ResourceList[Project]:
        return self._get_all_resources(Project, "projects")

    def sync_master_images(self):
        r = self._client.post(
            merge_parse_result(self._base_url, path=join_url_path(self._base_url.path, "master-images/command"))
        )

        assert r.status_code == httpx.codes.ACCEPTED.value

    def create_project(
        self, name: str, master_image_id: t.Union[MasterImage, uuid.UUID, str], description: str = None
    ) -> Project:
        return self._create_resource(
            Project,
            CreateProject(
                name=name,
                master_image_id=str(obtain_uuid_from(master_image_id)),
                description=description,
            ),
            "projects",
        )

    def delete_project(self, project_id: t.Union[Project, uuid.UUID, str]):
        self._delete_resource(project_id, "projects")

    def get_project(self, project_id: t.Union[Project, uuid.UUID, str]) -> Project | None:
        return self._get_single_resource(Project, project_id, "projects")

    def update_project(
        self,
        project_id: t.Union[Project, uuid.UUID, str],
        description: str = None,
        master_image_id: t.Union[MasterImage, str, uuid.UUID] = None,
        name: str = None,
    ) -> Project:
        return self._update_resource(
            Project,
            project_id,
            UpdateProject(
                description=description,
                master_image_id=str(obtain_uuid_from(master_image_id)) if master_image_id else None,
                name=name,
            ),
            "projects",
        )

    def create_project_node(
        self, project_id: t.Union[Project, uuid.UUID, str], node_id: t.Union[Node, uuid.UUID, str]
    ) -> ProjectNode:
        return self._create_resource(
            ProjectNode,
            CreateProjectNode(
                project_id=str(obtain_uuid_from(project_id)),
                node_id=str(obtain_uuid_from(node_id)),
            ),
            "project-nodes",
        )

    def delete_project_node(self, project_node_id: t.Union[ProjectNode, uuid.UUID, str]):
        self._delete_resource(project_node_id, "project-nodes")

    def get_project_nodes(self) -> ResourceList[ProjectNode]:
        return self._get_all_resources(ProjectNode, "project-nodes")

    def get_project_node(self, project_node_id: t.Union[ProjectNode, uuid.UUID, str]) -> ProjectNode | None:
        return self._get_single_resource(ProjectNode, project_node_id, "project-nodes")

    def create_analysis(
        self, name: str, project_id: t.Union[Project, uuid.UUID, str], description: str = None
    ) -> Analysis:
        return self._create_resource(
            Analysis,
            CreateAnalysis(
                name=name,
                project_id=str(obtain_uuid_from(project_id)),
                description=description,
            ),
            "analyses",
        )

    def delete_analysis(self, analysis_id: t.Union[Analysis, uuid.UUID, str]):
        self._delete_resource(analysis_id, "analyses")

    def get_analyses(self) -> ResourceList[Analysis]:
        return self._get_all_resources(Analysis, "analyses")

    def get_analysis(self, analysis_id: t.Union[Analysis, uuid.UUID, str]) -> Analysis | None:
        return self._get_single_resource(Analysis, analysis_id, "analyses")
