__all__ = ["CoreClient"]

import typing as t
import uuid
from datetime import datetime
from enum import Enum

import httpx
import typing_extensions as te
from pydantic import BaseModel

from flame_hub.auth import Realm
from flame_hub.base_client import (
    BaseClient,
    obtain_uuid_from,
    UpdateModel,
    _UNSET,
    FindAllKwargs,
    new_error_from_response,
)
from flame_hub.defaults import DEFAULT_CORE_BASE_URL
from flame_hub.flow import PasswordAuth, RobotAuth
from flame_hub.storage import BucketFile


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


class UpdateNode(UpdateModel):
    hidden: bool | None = None
    external_name: str | None = None
    type: NodeType | None = None
    public_key: str | None = None
    realm_id: uuid.UUID | None = None


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


class UpdateProject(UpdateModel):
    description: str | None = None
    master_image_id: uuid.UUID | None = None
    name: str | None = None


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


class UpdateAnalysis(UpdateModel):
    name: str | None


AnalysisCommand = t.Literal["spinUp", "tearDown", "buildStart", "buildStop", "configurationLock", "configurationUnlock"]


class CreateAnalysisNode(BaseModel):
    analysis_id: uuid.UUID
    node_id: uuid.UUID


class AnalysisNodeApprovalStatus(str, Enum):
    rejected = "rejected"
    approved = "approved"


class AnalysisNodeRunStatus(str, Enum):
    starting = "starting"
    started = "started"
    stopping = "stopping"
    stopped = "stopped"
    running = "running"
    finished = "finished"
    failed = "failed"


class AnalysisNode(CreateAnalysisNode):
    id: uuid.UUID
    approval_status: AnalysisNodeApprovalStatus | None
    run_status: AnalysisNodeRunStatus | None
    comment: str | None
    index: int
    artifact_tag: str | None
    artifact_digest: str | None
    created_at: datetime
    updated_at: datetime
    analysis_id: uuid.UUID
    analysis_realm_id: uuid.UUID
    node_id: uuid.UUID
    node_realm_id: uuid.UUID


class UpdateAnalysisNode(UpdateModel):
    comment: str | None = None
    approval_status: AnalysisNodeApprovalStatus | None = None
    run_status: AnalysisNodeRunStatus | None = None


class AnalysisBucketType(str, Enum):
    code = "CODE"
    result = "RESULT"
    temp = "TEMP"


class AnalysisBucket(BaseModel):
    id: uuid.UUID
    type: AnalysisBucketType
    external_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    analysis_id: uuid.UUID
    realm_id: uuid.UUID


class CreateAnalysisBucketFile(BaseModel):
    name: str
    external_id: uuid.UUID
    bucket_id: uuid.UUID
    root: bool


class AnalysisBucketFile(CreateAnalysisBucketFile):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    realm_id: uuid.UUID
    user_id: uuid.UUID | None
    robot_id: uuid.UUID | None
    analysis_id: uuid.UUID


class UpdateAnalysisBucketFile(UpdateModel):
    root: bool | None = None


class CoreClient(BaseClient):
    def __init__(
        self,
        base_url: str = DEFAULT_CORE_BASE_URL,
        client: httpx.Client = None,
        auth: t.Union[PasswordAuth, RobotAuth] = None,
    ):
        super().__init__(base_url, client, auth)

    def get_nodes(self) -> list[Node]:
        return self._get_all_resources(Node, "nodes")

    def find_nodes(self, **params: te.Unpack[FindAllKwargs]) -> list[Node]:
        return self._find_all_resources(Node, "nodes", **params)

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
        return self._get_single_resource(Node, "nodes", node_id)

    def delete_node(self, node_id: t.Union[Node, uuid.UUID, str]):
        self._delete_resource("nodes", node_id)

    def update_node(
        self,
        node_id: t.Union[Node, uuid.UUID, str],
        external_name: str = _UNSET,
        hidden: bool = _UNSET,
        node_type: NodeType = _UNSET,
        realm_id: t.Union[Realm, str, uuid.UUID] = _UNSET,
        public_key: str = _UNSET,
    ) -> Node:
        if realm_id not in (None, _UNSET):
            realm_id = obtain_uuid_from(realm_id)

        return self._update_resource(
            Node,
            UpdateNode(
                external_name=external_name,
                hidden=hidden,
                type=node_type,
                public_key=public_key,
                realm_id=realm_id,
            ),
            "nodes",
            node_id,
        )

    def get_master_image_groups(self) -> list[MasterImageGroup]:
        return self._get_all_resources(MasterImageGroup, "master-image-groups")

    def find_master_image_groups(self, **params: te.Unpack[FindAllKwargs]) -> list[MasterImageGroup]:
        return self._find_all_resources(MasterImageGroup, "master-image-groups", **params)

    def get_master_images(self) -> list[MasterImage]:
        return self._get_all_resources(MasterImage, "master-images")

    def find_master_images(self, **params: te.Unpack[FindAllKwargs]) -> list[MasterImage]:
        return self._find_all_resources(MasterImage, "master-images", **params)

    def get_projects(self) -> list[Project]:
        return self._get_all_resources(Project, "projects")

    def find_projects(self, **params: te.Unpack[FindAllKwargs]) -> list[Project]:
        return self._find_all_resources(Project, "projects", **params)

    def sync_master_images(self):
        r = self._client.post("master-images/command", json={"command": "sync"})

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_error_from_response(r)

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
        self._delete_resource("projects", project_id)

    def get_project(self, project_id: t.Union[Project, uuid.UUID, str]) -> Project | None:
        return self._get_single_resource(Project, "projects", project_id)

    def update_project(
        self,
        project_id: t.Union[Project, uuid.UUID, str],
        description: str = _UNSET,
        master_image_id: t.Union[MasterImage, str, uuid.UUID] = _UNSET,
        name: str = _UNSET,
    ) -> Project:
        if master_image_id not in (None, _UNSET):
            master_image_id = obtain_uuid_from(master_image_id)

        return self._update_resource(
            Project,
            UpdateProject(
                description=description,
                master_image_id=master_image_id,
                name=name,
            ),
            "projects",
            project_id,
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
        self._delete_resource("project-nodes", project_node_id)

    def get_project_nodes(self) -> list[ProjectNode]:
        return self._get_all_resources(ProjectNode, "project-nodes")

    def find_project_nodes(self, **params: te.Unpack[FindAllKwargs]) -> list[ProjectNode]:
        return self._find_all_resources(ProjectNode, "project-nodes", **params)

    def get_project_node(self, project_node_id: t.Union[ProjectNode, uuid.UUID, str]) -> ProjectNode | None:
        return self._get_single_resource(ProjectNode, "project-nodes", project_node_id)

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
        self._delete_resource("analyses", analysis_id)

    def get_analyses(self) -> list[Analysis]:
        return self._get_all_resources(Analysis, "analyses")

    def find_analyses(self, **params: te.Unpack[FindAllKwargs]) -> list[Analysis]:
        return self._find_all_resources(Analysis, "analyses", **params)

    def get_analysis(self, analysis_id: t.Union[Analysis, uuid.UUID, str]) -> Analysis | None:
        return self._get_single_resource(Analysis, "analyses", analysis_id)

    def update_analysis(self, analysis_id: t.Union[Analysis, uuid.UUID, str], name: str = _UNSET):
        if analysis_id not in (None, _UNSET):
            analysis_id = obtain_uuid_from(analysis_id)

        return self._update_resource(Analysis, UpdateAnalysis(name=name), "analyses", analysis_id)

    def send_analysis_command(self, analysis_id: t.Union[Analysis, uuid.UUID, str], command: AnalysisCommand):
        r = self._client.post(f"analyses/{obtain_uuid_from(analysis_id)}/command", json={"command": command})

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_error_from_response(r)

    def create_analysis_node(
        self, analysis_id: t.Union[Analysis, uuid.UUID, str], node_id: t.Union[Node, uuid.UUID, str]
    ):
        return self._create_resource(
            AnalysisNode, CreateAnalysisNode(analysis_id=analysis_id, node_id=node_id), "analysis-nodes"
        )

    def delete_analysis_node(self, analysis_node_id: t.Union[AnalysisNode, uuid.UUID, str]):
        self._delete_resource("analysis-nodes", analysis_node_id)

    def update_analysis_node(
        self,
        analysis_node_id: t.Union[AnalysisNode, uuid.UUID, str],
        comment: str = _UNSET,
        approval_status: AnalysisNodeApprovalStatus = _UNSET,
        run_status: AnalysisNodeRunStatus = _UNSET,
    ):
        return self._update_resource(
            AnalysisNode,
            UpdateAnalysisNode(comment=comment, approval_status=approval_status, run_status=run_status),
            "analysis-nodes",
            analysis_node_id,
        )

    def get_analysis_buckets(self) -> list[AnalysisBucket]:
        return self._get_all_resources(AnalysisBucket, "analysis-buckets")

    def find_analysis_buckets(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisBucket]:
        return self._find_all_resources(AnalysisBucket, "analysis-buckets", **params)

    def get_analysis_bucket(self, analysis_bucket_id: t.Union[AnalysisBucket, uuid.UUID, str]) -> AnalysisBucket | None:
        return self._get_single_resource(AnalysisBucket, "analysis-buckets", analysis_bucket_id)

    def get_analysis_bucket_files(self) -> list[AnalysisBucketFile]:
        return self._get_all_resources(AnalysisBucketFile, "analysis-bucket-files")

    def find_analysis_bucket_files(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisBucketFile]:
        return self._find_all_resources(AnalysisBucketFile, "analysis-bucket-files", **params)

    def get_analysis_bucket_file(
        self, analysis_bucket_file_id: t.Union[AnalysisBucketFile, uuid.UUID, str]
    ) -> AnalysisBucketFile | None:
        return self._get_single_resource(AnalysisBucketFile, "analysis-bucket-files", analysis_bucket_file_id)

    def create_analysis_bucket_file(
        self,
        name: str,
        bucket_file_id: t.Union[BucketFile, uuid.UUID, str],
        analysis_bucket_id: t.Union[AnalysisBucket, uuid.UUID, str],
        is_entrypoint: bool = False,
    ):
        return self._create_resource(
            AnalysisBucketFile,
            CreateAnalysisBucketFile(
                external_id=obtain_uuid_from(bucket_file_id),
                bucket_id=obtain_uuid_from(analysis_bucket_id),
                name=name,
                root=is_entrypoint,
            ),
            "analysis-bucket-files",
        )

    def update_analysis_bucket_file(
        self, analysis_bucket_file_id: t.Union[AnalysisBucketFile, uuid.UUID, str], is_entrypoint: bool = _UNSET
    ) -> AnalysisBucketFile:
        if analysis_bucket_file_id not in (None, _UNSET):
            analysis_bucket_file_id = obtain_uuid_from(analysis_bucket_file_id)

        return self._update_resource(
            AnalysisBucketFile,
            UpdateAnalysisBucketFile(root=is_entrypoint),
            "analysis-bucket-files",
            analysis_bucket_file_id,
        )
