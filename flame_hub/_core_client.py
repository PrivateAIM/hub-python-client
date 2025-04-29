import typing as t
import uuid
from datetime import datetime

import httpx
import typing_extensions as te
from pydantic import BaseModel

from flame_hub._auth_client import Realm
from flame_hub._base_client import (
    BaseClient,
    obtain_uuid_from,
    UpdateModel,
    _UNSET,
    FindAllKwargs,
    ClientKwargs,
)
from flame_hub._exceptions import new_hub_api_error_from_response
from flame_hub._defaults import DEFAULT_CORE_BASE_URL
from flame_hub._auth_flows import PasswordAuth, RobotAuth
from flame_hub._storage_client import BucketFile

NodeType = t.Literal["aggregator", "default"]


class CreateNode(BaseModel):
    external_name: str | None
    hidden: bool | None
    name: str
    realm_id: uuid.UUID
    registry_id: uuid.UUID | None
    type: NodeType | None


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
    registry_id: uuid.UUID | None = None


class MasterImageGroup(BaseModel):
    id: uuid.UUID
    name: str
    path: str
    virtual_path: str
    created_at: datetime
    updated_at: datetime


class MasterImageCommandArgument(te.TypedDict):
    value: str
    position: t.Literal["before", "after"] | None


class MasterImage(BaseModel):
    id: uuid.UUID
    path: str | None
    virtual_path: str
    group_virtual_path: str
    name: str
    command: str | None
    command_arguments: list[MasterImageCommandArgument] | None
    created_at: datetime
    updated_at: datetime


class MasterImageEventLog(BaseModel):
    id: uuid.UUID
    name: str
    data: dict | None = None  # Hub resource does not have a "data" key if there is no data.
    expiring: bool
    expires_at: datetime
    master_image_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class CreateProject(BaseModel):
    description: str | None
    master_image_id: uuid.UUID | None
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


ProjectNodeApprovalStatus = t.Literal["rejected", "approved"]


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


class UpdateProjectNode(UpdateModel):
    comment: str | None = None
    approval_status: ProjectNodeApprovalStatus | None = None


AnalysisBuildStatus = t.Literal["starting", "started", "stopping", "stopped", "finished", "failed"]
AnalysisRunStatus = t.Literal["starting", "started", "running", "stopping", "stopped", "finished", "failed"]


class CreateAnalysis(BaseModel):
    description: str | None
    name: str | None
    project_id: uuid.UUID
    master_image_id: uuid.UUID | None
    registry_id: uuid.UUID | None
    image_command_arguments: list[MasterImageCommandArgument] = []


class Analysis(CreateAnalysis):
    id: uuid.UUID
    configuration_locked: bool
    nodes: int
    build_status: AnalysisBuildStatus | None
    run_status: AnalysisRunStatus | None
    created_at: datetime
    updated_at: datetime
    registry_id: uuid.UUID | None
    realm_id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    master_image_id: uuid.UUID | None


class UpdateAnalysis(UpdateModel):
    description: str | None = None
    name: str | None = None
    master_image_id: uuid.UUID | None = None
    image_command_arguments: list[MasterImageCommandArgument] | None = None


AnalysisCommand = t.Literal["spinUp", "tearDown", "buildStart", "buildStop", "configurationLock", "configurationUnlock"]


class CreateAnalysisNode(BaseModel):
    analysis_id: uuid.UUID
    node_id: uuid.UUID


AnalysisNodeApprovalStatus = t.Literal["rejected", "approved"]
AnalysisNodeRunStatus = t.Literal["starting", "started", "stopping", "stopped", "running", "finished", "failed"]


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
    analysis_realm_id: uuid.UUID
    node_realm_id: uuid.UUID


class UpdateAnalysisNode(UpdateModel):
    comment: str | None = None
    approval_status: AnalysisNodeApprovalStatus | None = None
    run_status: AnalysisNodeRunStatus | None = None


AnalysisBucketType = t.Literal["CODE", "RESULT", "TEMP"]


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


class CreateRegistry(BaseModel):
    name: str
    host: str
    account_name: str | None
    account_secret: str | None


class Registry(BaseModel):
    id: uuid.UUID
    name: str
    host: str
    account_name: str | None
    created_at: datetime
    updated_at: datetime


class UpdateRegistry(UpdateModel):
    name: str | None = None
    host: str | None = None
    account_name: str | None = None
    account_secret: str | None = None


RegistryProjectType = t.Literal["default", "aggregator", "incoming", "outgoing", "masterImages", "node"]


class CreateRegistryProject(BaseModel):
    name: str
    type: RegistryProjectType
    registry_id: uuid.UUID
    external_name: str


class RegistryProject(CreateRegistryProject):
    id: uuid.UUID
    public: bool
    external_id: uuid.UUID | None
    webhook_name: str | None
    webhook_exists: bool | None
    realm_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class UpdateRegistryProject(UpdateModel):
    name: str | None = None
    type: RegistryProjectType | None = None
    registry_id: uuid.UUID | None = None
    external_name: str | None = None


class CoreClient(BaseClient):
    def __init__(
        self,
        base_url: str = DEFAULT_CORE_BASE_URL,
        auth: PasswordAuth | RobotAuth = None,
        **kwargs: te.Unpack[ClientKwargs],
    ):
        super().__init__(base_url, auth, **kwargs)

    def get_nodes(self) -> list[Node]:
        return self._get_all_resources(Node, "nodes")

    def find_nodes(self, **params: te.Unpack[FindAllKwargs]) -> list[Node]:
        return self._find_all_resources(Node, "nodes", **params)

    def create_node(
        self,
        name: str,
        realm_id: Realm | str | uuid.UUID,
        registry_id: Registry | uuid.UUID | str = None,
        external_name: str | None = None,
        node_type: NodeType = "default",
        hidden: bool = False,
    ) -> Node:
        if registry_id is not None:
            registry_id = obtain_uuid_from(registry_id)

        return self._create_resource(
            Node,
            CreateNode(
                name=name,
                realm_id=obtain_uuid_from(realm_id),
                external_name=external_name,
                hidden=hidden,
                registry_id=registry_id,
                type=node_type,
            ),
            "nodes",
        )

    def get_node(self, node_id: Node | uuid.UUID | str) -> Node | None:
        return self._get_single_resource(Node, "nodes", node_id)

    def delete_node(self, node_id: Node | uuid.UUID | str):
        self._delete_resource("nodes", node_id)

    def update_node(
        self,
        node_id: Node | uuid.UUID | str,
        external_name: str = _UNSET,
        hidden: bool = _UNSET,
        node_type: NodeType = _UNSET,
        realm_id: Realm | str | uuid.UUID = _UNSET,
        registry_id: Registry | str | uuid.UUID = _UNSET,
        public_key: str = _UNSET,
    ) -> Node:
        if realm_id not in (None, _UNSET):
            realm_id = obtain_uuid_from(realm_id)
        if registry_id not in (None, _UNSET):
            registry_id = obtain_uuid_from(registry_id)

        return self._update_resource(
            Node,
            UpdateNode(
                external_name=external_name,
                hidden=hidden,
                type=node_type,
                public_key=public_key,
                realm_id=realm_id,
                registry_id=registry_id,
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

    def get_master_image_event_log(
        self, master_image_event_log_id: MasterImageEventLog | uuid.UUID | str
    ) -> MasterImageEventLog | None:
        return self._get_single_resource(MasterImageEventLog, "master-image-event-logs", master_image_event_log_id)

    def get_master_image_event_logs(self) -> list[MasterImageEventLog]:
        return self._get_all_resources(MasterImageEventLog, "master-image-event-logs")

    def find_master_image_event_logs(self, **params: te.Unpack[FindAllKwargs]) -> list[MasterImageEventLog]:
        return self._find_all_resources(MasterImageEventLog, "master-image-event-logs", **params)

    def get_projects(self) -> list[Project]:
        return self._get_all_resources(Project, "projects")

    def find_projects(self, **params: te.Unpack[FindAllKwargs]) -> list[Project]:
        return self._find_all_resources(Project, "projects", **params)

    def sync_master_images(self):
        r = self._client.post("master-images/command", json={"command": "sync"})

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_hub_api_error_from_response(r)

    def create_project(
        self, name: str, master_image_id: MasterImage | uuid.UUID | str = None, description: str = None
    ) -> Project:
        return self._create_resource(
            Project,
            CreateProject(
                name=name,
                master_image_id=obtain_uuid_from(master_image_id) if master_image_id is not None else None,
                description=description,
            ),
            "projects",
        )

    def delete_project(self, project_id: Project | uuid.UUID | str):
        self._delete_resource("projects", project_id)

    def get_project(self, project_id: Project | uuid.UUID | str) -> Project | None:
        return self._get_single_resource(Project, "projects", project_id)

    def update_project(
        self,
        project_id: Project | uuid.UUID | str,
        description: str = _UNSET,
        master_image_id: MasterImage | str | uuid.UUID = _UNSET,
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
        self, project_id: Project | uuid.UUID | str, node_id: Node | uuid.UUID | str
    ) -> ProjectNode:
        return self._create_resource(
            ProjectNode,
            CreateProjectNode(
                project_id=obtain_uuid_from(project_id),
                node_id=obtain_uuid_from(node_id),
            ),
            "project-nodes",
        )

    def delete_project_node(self, project_node_id: ProjectNode | uuid.UUID | str):
        self._delete_resource("project-nodes", project_node_id)

    def get_project_nodes(self) -> list[ProjectNode]:
        return self._get_all_resources(ProjectNode, "project-nodes")

    def find_project_nodes(self, **params: te.Unpack[FindAllKwargs]) -> list[ProjectNode]:
        return self._find_all_resources(ProjectNode, "project-nodes", **params)

    def get_project_node(self, project_node_id: ProjectNode | uuid.UUID | str) -> ProjectNode | None:
        return self._get_single_resource(ProjectNode, "project-nodes", project_node_id)

    def update_project_node(
        self,
        project_node_id: ProjectNode | uuid.UUID | str,
        comment: str = _UNSET,
        approval_status: ProjectNodeApprovalStatus = _UNSET,
    ):
        return self._update_resource(
            ProjectNode,
            UpdateProjectNode(comment=comment, approval_status=approval_status),
            "project-nodes",
            project_node_id,
        )

    def create_analysis(
        self,
        project_id: Project | uuid.UUID | str,
        name: str = None,
        description: str = None,
        master_image_id: MasterImage | uuid.UUID | str = None,
        registry_id: Registry | uuid.UUID | str = None,
        image_command_arguments: list[MasterImageCommandArgument] = (),
    ) -> Analysis:
        if master_image_id is not None:
            master_image_id = obtain_uuid_from(master_image_id)
        if registry_id is not None:
            registry_id = obtain_uuid_from(registry_id)

        return self._create_resource(
            Analysis,
            CreateAnalysis(
                project_id=obtain_uuid_from(project_id),
                name=name,
                description=description,
                master_image_id=master_image_id,
                registry_id=registry_id,
                image_command_arguments=image_command_arguments,
            ),
            "analyses",
        )

    def delete_analysis(self, analysis_id: Analysis | uuid.UUID | str):
        self._delete_resource("analyses", analysis_id)

    def get_analyses(self) -> list[Analysis]:
        return self._get_all_resources(Analysis, "analyses")

    def find_analyses(self, **params: te.Unpack[FindAllKwargs]) -> list[Analysis]:
        return self._find_all_resources(Analysis, "analyses", **params)

    def get_analysis(self, analysis_id: Analysis | uuid.UUID | str) -> Analysis | None:
        return self._get_single_resource(Analysis, "analyses", analysis_id)

    def update_analysis(
        self,
        analysis_id: Analysis | uuid.UUID | str,
        name: str = _UNSET,
        description: str = _UNSET,
        master_image_id: MasterImage | uuid.UUID | str = _UNSET,
        image_command_arguments: list[MasterImageCommandArgument] = _UNSET,
    ) -> Analysis:
        if master_image_id not in (None, _UNSET):
            master_image_id = obtain_uuid_from(master_image_id)

        return self._update_resource(
            Analysis,
            UpdateAnalysis(
                name=name,
                description=description,
                master_image_id=master_image_id,
                image_command_arguments=image_command_arguments,
            ),
            "analyses",
            analysis_id,
        )

    def send_analysis_command(self, analysis_id: Analysis | uuid.UUID | str, command: AnalysisCommand):
        r = self._client.post(f"analyses/{obtain_uuid_from(analysis_id)}/command", json={"command": command})

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_hub_api_error_from_response(r)

    def create_analysis_node(
        self, analysis_id: Analysis | uuid.UUID | str, node_id: Node | uuid.UUID | str
    ) -> AnalysisNode:
        return self._create_resource(
            AnalysisNode,
            CreateAnalysisNode(analysis_id=obtain_uuid_from(analysis_id), node_id=obtain_uuid_from(node_id)),
            "analysis-nodes",
        )

    def delete_analysis_node(self, analysis_node_id: AnalysisNode | uuid.UUID | str):
        self._delete_resource("analysis-nodes", analysis_node_id)

    def update_analysis_node(
        self,
        analysis_node_id: AnalysisNode | uuid.UUID | str,
        comment: str = _UNSET,
        approval_status: AnalysisNodeApprovalStatus = _UNSET,
        run_status: AnalysisNodeRunStatus = _UNSET,
    ) -> AnalysisNode:
        return self._update_resource(
            AnalysisNode,
            UpdateAnalysisNode(comment=comment, approval_status=approval_status, run_status=run_status),
            "analysis-nodes",
            analysis_node_id,
        )

    def get_analysis_node(self, analysis_node_id: AnalysisNode | uuid.UUID | str) -> AnalysisNode | None:
        return self._get_single_resource(AnalysisNode, "analysis-nodes", analysis_node_id)

    def get_analysis_nodes(self) -> list[AnalysisNode]:
        return self._get_all_resources(AnalysisNode, "analysis-nodes")

    def find_analysis_nodes(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisNode]:
        return self._find_all_resources(AnalysisNode, "analysis-nodes", **params)

    def get_analysis_buckets(self) -> list[AnalysisBucket]:
        return self._get_all_resources(AnalysisBucket, "analysis-buckets")

    def find_analysis_buckets(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisBucket]:
        return self._find_all_resources(AnalysisBucket, "analysis-buckets", **params)

    def get_analysis_bucket(self, analysis_bucket_id: AnalysisBucket | uuid.UUID | str) -> AnalysisBucket | None:
        return self._get_single_resource(AnalysisBucket, "analysis-buckets", analysis_bucket_id)

    def get_analysis_bucket_files(self) -> list[AnalysisBucketFile]:
        return self._get_all_resources(AnalysisBucketFile, "analysis-bucket-files")

    def find_analysis_bucket_files(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisBucketFile]:
        return self._find_all_resources(AnalysisBucketFile, "analysis-bucket-files", **params)

    def get_analysis_bucket_file(
        self, analysis_bucket_file_id: AnalysisBucketFile | uuid.UUID | str
    ) -> AnalysisBucketFile | None:
        return self._get_single_resource(AnalysisBucketFile, "analysis-bucket-files", analysis_bucket_file_id)

    def delete_analysis_bucket_file(
        self, analysis_bucket_file_id: AnalysisBucketFile | uuid.UUID | str
    ) -> AnalysisBucketFile | None:
        self._delete_resource("analysis-bucket-files", analysis_bucket_file_id)

    def create_analysis_bucket_file(
        self,
        name: str,
        bucket_file_id: BucketFile | uuid.UUID | str,
        analysis_bucket_id: AnalysisBucket | uuid.UUID | str,
        is_entrypoint: bool = False,
    ) -> AnalysisBucketFile:
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
        self, analysis_bucket_file_id: AnalysisBucketFile | uuid.UUID | str, is_entrypoint: bool = _UNSET
    ) -> AnalysisBucketFile:
        return self._update_resource(
            AnalysisBucketFile,
            UpdateAnalysisBucketFile(root=is_entrypoint),
            "analysis-bucket-files",
            analysis_bucket_file_id,
        )

    def create_registry(self, name: str, host: str, account_name: str = None, account_secret: str = None) -> Registry:
        return self._create_resource(
            Registry,
            CreateRegistry(name=name, host=host, account_name=account_name, account_secret=account_secret),
            "registries",
        )

    def get_registry(self, registry_id: Registry | uuid.UUID | str) -> Registry | None:
        return self._get_single_resource(Registry, "registries", registry_id)

    def delete_registry(self, registry_id: Registry | uuid.UUID | str):
        self._delete_resource("registries", registry_id)

    def update_registry(
        self,
        registry_id: Registry | uuid.UUID | str,
        name: str = _UNSET,
        host: str = _UNSET,
        account_name: str = _UNSET,
        account_secret: str = _UNSET,
    ) -> Registry:
        return self._update_resource(
            Registry,
            UpdateRegistry(name=name, host=host, account_name=account_name, account_secret=account_secret),
            "registries",
            registry_id,
        )

    def get_registries(self) -> list[Registry]:
        return self._get_all_resources(Registry, "registries")

    def find_registries(self, **params: te.Unpack[FindAllKwargs]) -> list[Registry]:
        return self._find_all_resources(Registry, "registries", **params)

    def create_registry_project(
        self,
        name: str,
        registry_project_type: RegistryProjectType,
        registry_id: Registry | uuid.UUID | str,
        external_name: str,
    ) -> RegistryProject:
        return self._create_resource(
            RegistryProject,
            CreateRegistryProject(
                name=name,
                type=registry_project_type,
                registry_id=obtain_uuid_from(registry_id),
                external_name=external_name,
            ),
            "registry-projects",
        )

    def get_registry_project(self, registry_project_id: RegistryProject | uuid.UUID | str) -> RegistryProject | None:
        return self._get_single_resource(RegistryProject, "registry-projects", registry_project_id)

    def delete_registry_project(self, registry_project_id: RegistryProject | uuid.UUID | str):
        self._delete_resource("registry-projects", registry_project_id)

    def update_registry_project(
        self,
        registry_project_id: RegistryProject | uuid.UUID | str,
        name: str = _UNSET,
        registry_project_type: RegistryProjectType = _UNSET,
        registry_id: Registry | uuid.UUID | str = _UNSET,
        external_name: str = _UNSET,
    ) -> RegistryProject:
        return self._update_resource(
            RegistryProject,
            UpdateRegistryProject(
                name=name,
                type=registry_project_type,
                registry_id=obtain_uuid_from(registry_id) if registry_id != _UNSET else _UNSET,
                external_name=external_name,
            ),
            "registry-projects",
            registry_project_id,
        )

    def get_registry_projects(self) -> list[RegistryProject]:
        return self._get_all_resources(RegistryProject, "registry-projects")

    def find_registry_projects(self, **params: te.Unpack[FindAllKwargs]) -> list[RegistryProject]:
        return self._find_all_resources(RegistryProject, "registry-projects", **params)
