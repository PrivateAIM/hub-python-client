from __future__ import annotations
import typing as t
import uuid
from datetime import datetime

import httpx
import typing_extensions as te
from pydantic import BaseModel, WrapValidator, Field, BeforeValidator

from flame_hub._auth_client import Realm
from flame_hub._base_client import (
    BaseClient,
    obtain_uuid_from,
    UpdateModel,
    _UNSET,
    FindAllKwargs,
    GetKwargs,
    ClientKwargs,
    uuid_validator,
    IsField,
)
from flame_hub._exceptions import new_hub_api_error_from_response
from flame_hub._defaults import DEFAULT_CORE_BASE_URL
from flame_hub._auth_flows import PasswordAuth, RobotAuth
from flame_hub._storage_client import BucketFile


RegistryCommand = t.Literal["setup", "cleanup"]


class CreateRegistry(BaseModel):
    name: str
    host: str
    account_name: str | None
    account_secret: t.Annotated[str | None, IsField] = None


class Registry(CreateRegistry):
    id: uuid.UUID
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
    registry_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    external_name: str


class RegistryProject(CreateRegistryProject):
    id: uuid.UUID
    public: bool
    external_id: str | None
    webhook_name: str | None
    webhook_exists: bool | None
    realm_id: uuid.UUID | None
    registry: Registry = None
    account_id: t.Annotated[str | None, IsField] = None
    account_name: t.Annotated[str | None, IsField] = None
    account_secret: t.Annotated[str | None, IsField] = None
    created_at: datetime
    updated_at: datetime


class UpdateRegistryProject(UpdateModel):
    name: str | None = None
    type: RegistryProjectType | None = None
    registry_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)] = None
    external_name: str | None = None


NodeType = t.Literal["aggregator", "default"]


class CreateNode(BaseModel):
    external_name: str | None
    hidden: bool | None
    name: str
    realm_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    registry_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    type: NodeType | None


class Node(CreateNode):
    id: uuid.UUID
    public_key: str | None
    online: bool
    registry: Registry | None = None
    registry_project_id: uuid.UUID | None
    registry_project: RegistryProject | None = None
    robot_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UpdateNode(UpdateModel):
    hidden: bool | None = None
    external_name: str | None = None
    type: NodeType | None = None
    public_key: str | None = None
    realm_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)] = None
    registry_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)] = None


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


def ensure_position_none(value: t.Any) -> t.Any:
    # see https://github.com/PrivateAIM/hub-python-client/issues/42
    # `position` can be absent. if that's the case, validation fails because
    # MasterImageCommandArgument is a TypedDict and cannot supply default values.
    # therefore this validator checks if `position` is absent and, if so, sets it to None.
    if not isinstance(value, list) or not all(isinstance(v_dict, dict) for v_dict in value):
        raise ValueError("value must be a list of dicts")

    for v_idx, v_dict in enumerate(value):
        if "position" not in v_dict:
            value[v_idx]["position"] = None

    return value


class MasterImage(BaseModel):
    id: uuid.UUID
    path: str | None
    virtual_path: str
    group_virtual_path: str
    name: str
    command: str | None
    command_arguments: t.Annotated[list[MasterImageCommandArgument] | None, BeforeValidator(ensure_position_none)]
    created_at: datetime
    updated_at: datetime


class MasterImageEventLog(BaseModel):
    id: uuid.UUID
    name: str
    data: dict | None = None  # Hub resource does not have a "data" key if there is no data.
    expiring: bool
    expires_at: datetime
    master_image_id: uuid.UUID | None
    master_image: MasterImage | None = None
    created_at: datetime
    updated_at: datetime


class CreateProject(BaseModel):
    description: str | None
    master_image_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    name: str


class Project(CreateProject):
    id: uuid.UUID
    analyses: int
    nodes: int
    master_image: MasterImage | None = None
    created_at: datetime
    updated_at: datetime
    realm_id: uuid.UUID
    user_id: uuid.UUID | None
    robot_id: uuid.UUID | None


class UpdateProject(UpdateModel):
    description: str | None = None
    master_image_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)] = None
    name: str | None = None


ProjectNodeApprovalStatus = t.Literal["rejected", "approved"]


class CreateProjectNode(BaseModel):
    node_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    project_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class ProjectNode(CreateProjectNode):
    id: uuid.UUID
    approval_status: ProjectNodeApprovalStatus
    comment: str | None
    created_at: datetime
    updated_at: datetime
    node: Node = None
    project: Project = None
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
    project_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    master_image_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    registry_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    image_command_arguments: t.Annotated[
        list[MasterImageCommandArgument],
        Field(default_factory=list),
        BeforeValidator(lambda value: [] if value is None else value),
    ]


class Analysis(CreateAnalysis):
    id: uuid.UUID
    configuration_locked: bool
    nodes: int
    build_status: AnalysisBuildStatus | None
    run_status: AnalysisRunStatus | None
    created_at: datetime
    updated_at: datetime
    registry: Registry | None = None
    realm_id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID
    project: Project = None
    master_image: MasterImage | None = None


class UpdateAnalysis(UpdateModel):
    description: str | None = None
    name: str | None = None
    master_image_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)] = None
    image_command_arguments: t.Annotated[list[MasterImageCommandArgument], Field(default_factory=list)]


AnalysisCommand = t.Literal[
    "spinUp",
    "tearDown",
    "buildStart",
    "buildStop",
    "configurationLock",
    "configurationUnlock",
    "buildStatus",
]


class AnalysisLog(BaseModel):
    id: uuid.UUID
    component: str | None
    command: str | None
    event: str | None
    error: bool
    error_code: str | None
    status: str | None
    status_message: str | None
    meta: str | None
    created_at: datetime
    updated_at: datetime
    analysis_id: uuid.UUID
    analysis: Analysis = None
    realm_id: uuid.UUID


class CreateAnalysisNode(BaseModel):
    analysis_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    node_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


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
    analysis: Analysis = None
    node: Node = None
    analysis_realm_id: uuid.UUID
    node_realm_id: uuid.UUID


class UpdateAnalysisNode(UpdateModel):
    comment: str | None = None
    approval_status: AnalysisNodeApprovalStatus | None = None
    run_status: AnalysisNodeRunStatus | None = None


class CreateAnalysisNodeLog(BaseModel):
    analysis_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    node_id: uuid.UUID
    error: bool
    error_code: str | None
    status: str
    status_message: str | None


class AnalysisNodeLog(CreateAnalysisNodeLog):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    analysis: Analysis = None
    node: Node = None
    analysis_realm_id: uuid.UUID
    node_realm_id: uuid.UUID


class UpdateAnalysisNodeLog(UpdateModel):
    error: bool | None = None
    error_code: str | None = None
    status: str | None = None
    status_message: str | None = None


AnalysisBucketType = t.Literal["CODE", "RESULT", "TEMP"]


class AnalysisBucket(BaseModel):
    id: uuid.UUID
    type: AnalysisBucketType
    external_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    analysis_id: uuid.UUID
    analysis: Analysis = None
    realm_id: uuid.UUID


class CreateAnalysisBucketFile(BaseModel):
    name: str
    external_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    bucket_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    root: bool


class AnalysisBucketFile(CreateAnalysisBucketFile):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    realm_id: uuid.UUID
    user_id: uuid.UUID | None
    robot_id: uuid.UUID | None
    analysis_id: uuid.UUID
    analysis: Analysis = None
    bucket: AnalysisBucket = None


class UpdateAnalysisBucketFile(UpdateModel):
    root: bool | None = None


class CoreClient(BaseClient):
    """The client which implements all core endpoints.

    This class passes its arguments through to :py:class:`.BaseClient`. Check the documentation of that class for
    further information. Note that ``base_url`` defaults :py:const:`~flame_hub._defaults.DEFAULT_CORE_BASE_URL`.

    See Also
    --------
    :py:class:`.BaseClient`
    """

    def __init__(
        self,
        base_url: str = DEFAULT_CORE_BASE_URL,
        auth: PasswordAuth | RobotAuth = None,
        **kwargs: te.Unpack[ClientKwargs],
    ):
        super().__init__(base_url, auth, **kwargs)

    def get_nodes(self, **params: te.Unpack[GetKwargs]) -> list[Node]:
        return self._get_all_resources(Node, "nodes", include=("registry", "registry_project"), **params)

    def find_nodes(self, **params: te.Unpack[FindAllKwargs]) -> list[Node]:
        return self._find_all_resources(Node, "nodes", include=("registry", "registry_project"), **params)

    def create_node(
        self,
        name: str,
        realm_id: Realm | str | uuid.UUID = None,
        registry_id: Registry | uuid.UUID | str = None,
        external_name: str | None = None,
        node_type: NodeType = "default",
        hidden: bool = False,
    ) -> Node:
        return self._create_resource(
            Node,
            CreateNode(
                name=name,
                realm_id=realm_id,
                external_name=external_name,
                hidden=hidden,
                registry_id=registry_id,
                type=node_type,
            ),
            "nodes",
        )

    def get_node(self, node_id: Node | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Node | None:
        return self._get_single_resource(Node, "nodes", node_id, include=("registry", "registry_project"), **params)

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

    def get_master_image_groups(self, **params: te.Unpack[GetKwargs]) -> list[MasterImageGroup]:
        return self._get_all_resources(MasterImageGroup, "master-image-groups", **params)

    def get_master_image_group(
        self, master_image_group_id: MasterImageGroup | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> MasterImageGroup | None:
        return self._get_single_resource(MasterImageGroup, "master-image-groups", master_image_group_id, **params)

    def find_master_image_groups(self, **params: te.Unpack[FindAllKwargs]) -> list[MasterImageGroup]:
        return self._find_all_resources(MasterImageGroup, "master-image-groups", **params)

    def get_master_images(self, **params: te.Unpack[GetKwargs]) -> list[MasterImage]:
        return self._get_all_resources(MasterImage, "master-images", **params)

    def get_master_image(
        self, master_image_id: MasterImage | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> MasterImage | None:
        return self._get_single_resource(MasterImage, "master-images", master_image_id, **params)

    def find_master_images(self, **params: te.Unpack[FindAllKwargs]) -> list[MasterImage]:
        return self._find_all_resources(MasterImage, "master-images", **params)

    def get_master_image_event_log(
        self, master_image_event_log_id: MasterImageEventLog | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> MasterImageEventLog | None:
        return self._get_single_resource(
            MasterImageEventLog, "master-image-event-logs", master_image_event_log_id, include="master_image", **params
        )

    def get_master_image_event_logs(self, **params: te.Unpack[GetKwargs]) -> list[MasterImageEventLog]:
        return self._get_all_resources(MasterImageEventLog, "master-image-event-logs", include="master_image", **params)

    def find_master_image_event_logs(self, **params: te.Unpack[FindAllKwargs]) -> list[MasterImageEventLog]:
        return self._find_all_resources(
            MasterImageEventLog, "master-image-event-logs", include="master_image", **params
        )

    def get_projects(self, **params: te.Unpack[GetKwargs]) -> list[Project]:
        return self._get_all_resources(Project, "projects", include="master_image", **params)

    def find_projects(self, **params: te.Unpack[FindAllKwargs]) -> list[Project]:
        return self._find_all_resources(Project, "projects", include="master_image", **params)

    def sync_master_images(self):
        """This method will start to synchronize the master images. Note that an error is raised if you request a
        synchronization while the Hub instance is still synchronizing master images.
        """
        r = self._client.post("master-images/command", json={"command": "sync"})

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_hub_api_error_from_response(r)

    def create_project(
        self, name: str, master_image_id: MasterImage | uuid.UUID | str = None, description: str = None
    ) -> Project:
        return self._create_resource(
            Project,
            CreateProject(name=name, master_image_id=master_image_id, description=description),
            "projects",
        )

    def delete_project(self, project_id: Project | uuid.UUID | str):
        self._delete_resource("projects", project_id)

    def get_project(self, project_id: Project | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Project | None:
        return self._get_single_resource(Project, "projects", project_id, include="master_image", **params)

    def update_project(
        self,
        project_id: Project | uuid.UUID | str,
        description: str = _UNSET,
        master_image_id: MasterImage | str | uuid.UUID = _UNSET,
        name: str = _UNSET,
    ) -> Project:
        return self._update_resource(
            Project,
            UpdateProject(description=description, master_image_id=master_image_id, name=name),
            "projects",
            project_id,
        )

    def create_project_node(
        self, project_id: Project | uuid.UUID | str, node_id: Node | uuid.UUID | str
    ) -> ProjectNode:
        return self._create_resource(
            ProjectNode,
            CreateProjectNode(project_id=project_id, node_id=node_id),
            "project-nodes",
        )

    def delete_project_node(self, project_node_id: ProjectNode | uuid.UUID | str):
        self._delete_resource("project-nodes", project_node_id)

    def get_project_nodes(self, **params: te.Unpack[GetKwargs]) -> list[ProjectNode]:
        return self._get_all_resources(ProjectNode, "project-nodes", include=("node", "project"), **params)

    def find_project_nodes(self, **params: te.Unpack[FindAllKwargs]) -> list[ProjectNode]:
        return self._find_all_resources(ProjectNode, "project-nodes", include=("node", "project"), **params)

    def get_project_node(
        self, project_node_id: ProjectNode | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> ProjectNode | None:
        return self._get_single_resource(
            ProjectNode, "project-nodes", project_node_id, include=("node", "project"), **params
        )

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
        return self._create_resource(
            Analysis,
            CreateAnalysis(
                project_id=project_id,
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

    def get_analyses(self, **params: te.Unpack[GetKwargs]) -> list[Analysis]:
        return self._get_all_resources(Analysis, "analyses", include=("registry", "project", "master_image"), **params)

    def find_analyses(self, **params: te.Unpack[FindAllKwargs]) -> list[Analysis]:
        return self._find_all_resources(Analysis, "analyses", include=("registry", "project", "master_image"), **params)

    def get_analysis(self, analysis_id: Analysis | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Analysis | None:
        return self._get_single_resource(
            Analysis, "analyses", analysis_id, include=("registry", "project", "master_image"), **params
        )

    def update_analysis(
        self,
        analysis_id: Analysis | uuid.UUID | str,
        name: str = _UNSET,
        description: str = _UNSET,
        master_image_id: MasterImage | uuid.UUID | str = _UNSET,
        image_command_arguments: list[MasterImageCommandArgument] = _UNSET,
    ) -> Analysis:
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

    def send_analysis_command(self, analysis_id: Analysis | uuid.UUID | str, command: AnalysisCommand) -> Analysis:
        r = self._client.post(f"analyses/{obtain_uuid_from(analysis_id)}/command", json={"command": command})

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_hub_api_error_from_response(r)

        return Analysis(**r.json())

    def create_analysis_node(
        self, analysis_id: Analysis | uuid.UUID | str, node_id: Node | uuid.UUID | str
    ) -> AnalysisNode:
        return self._create_resource(
            AnalysisNode,
            CreateAnalysisNode(analysis_id=analysis_id, node_id=node_id),
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

    def get_analysis_node(
        self, analysis_node_id: AnalysisNode | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> AnalysisNode | None:
        return self._get_single_resource(
            AnalysisNode, "analysis-nodes", analysis_node_id, include=("analysis", "node"), **params
        )

    def get_analysis_nodes(self, **params: te.Unpack[GetKwargs]) -> list[AnalysisNode]:
        return self._get_all_resources(AnalysisNode, "analysis-nodes", include=("analysis", "node"), **params)

    def find_analysis_nodes(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisNode]:
        return self._find_all_resources(AnalysisNode, "analysis-nodes", include=("analysis", "node"), **params)

    def create_analysis_node_log(
        self,
        analysis_id: Analysis | uuid.UUID | str,
        node_id: Node | uuid.UUID | str,
        error: bool,
        error_code: str = None,
        status: str = "",
        status_message: str = None,
    ) -> AnalysisNodeLog:
        return self._create_resource(
            AnalysisNodeLog,
            CreateAnalysisNodeLog(
                analysis_id=obtain_uuid_from(analysis_id),
                node_id=obtain_uuid_from(node_id),
                error=error,
                error_code=error_code,
                status=status,
                status_message=status_message,
            ),
            "analysis-node-logs",
        )

    def get_analysis_node_log(
        self, analysis_node_log_id: AnalysisNodeLog | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> AnalysisNodeLog | None:
        return self._get_single_resource(
            AnalysisNodeLog, "analysis-node-logs", analysis_node_log_id, include=("analysis", "node"), **params
        )

    def delete_analysis_node_log(self, analysis_node_log_id: AnalysisNodeLog | uuid.UUID | str):
        self._delete_resource("analysis-node-logs", analysis_node_log_id)

    def get_analysis_node_logs(self, **params: te.Unpack[GetKwargs]) -> list[AnalysisNodeLog]:
        return self._get_all_resources(AnalysisNodeLog, "analysis-node-logs", include=("analysis", "node"), **params)

    def find_analysis_node_logs(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisNodeLog]:
        return self._find_all_resources(AnalysisNodeLog, "analysis-node-logs", include=("analysis", "node"), **params)

    def update_analysis_node_log(
        self,
        analysis_node_log_id: AnalysisNodeLog | uuid.UUID | str,
        error: bool = _UNSET,
        error_code: str = _UNSET,
        status: str = _UNSET,
        status_message: str = _UNSET,
    ) -> AnalysisNodeLog:
        return self._update_resource(
            AnalysisNodeLog,
            UpdateAnalysisNodeLog(error=error, error_code=error_code, status=status, status_message=status_message),
            "analysis-node-logs",
            analysis_node_log_id,
        )

    def get_analysis_buckets(self, **params: te.Unpack[GetKwargs]) -> list[AnalysisBucket]:
        return self._get_all_resources(AnalysisBucket, "analysis-buckets", include="analysis", **params)

    def find_analysis_buckets(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisBucket]:
        return self._find_all_resources(AnalysisBucket, "analysis-buckets", include="analysis", **params)

    def get_analysis_bucket(
        self, analysis_bucket_id: AnalysisBucket | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> AnalysisBucket | None:
        return self._get_single_resource(
            AnalysisBucket, "analysis-buckets", analysis_bucket_id, include="analysis", **params
        )

    def get_analysis_bucket_files(self, **params: te.Unpack[GetKwargs]) -> list[AnalysisBucketFile]:
        return self._get_all_resources(
            AnalysisBucketFile, "analysis-bucket-files", include=("analysis", "bucket"), **params
        )

    def find_analysis_bucket_files(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisBucketFile]:
        return self._find_all_resources(
            AnalysisBucketFile, "analysis-bucket-files", include=("analysis", "bucket"), **params
        )

    def get_analysis_bucket_file(
        self, analysis_bucket_file_id: AnalysisBucketFile | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> AnalysisBucketFile | None:
        return self._get_single_resource(
            AnalysisBucketFile,
            "analysis-bucket-files",
            analysis_bucket_file_id,
            include=("analysis", "bucket"),
            **params,
        )

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
                external_id=bucket_file_id,
                bucket_id=analysis_bucket_id,
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

    def get_registry(self, registry_id: Registry | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Registry | None:
        return self._get_single_resource(Registry, "registries", registry_id, **params)

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

    def get_registries(self, **params: te.Unpack[GetKwargs]) -> list[Registry]:
        return self._get_all_resources(Registry, "registries", **params)

    def find_registries(self, **params: te.Unpack[FindAllKwargs]) -> list[Registry]:
        return self._find_all_resources(Registry, "registries", **params)

    def send_registry_command(self, registry_id: Registry | uuid.UUID | str, command: RegistryCommand):
        r = self._client.post(
            "services/registry/command", json={"command": command, "id": str(obtain_uuid_from(registry_id))}
        )

        if r.status_code != httpx.codes.ACCEPTED.value:
            raise new_hub_api_error_from_response(r)

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
                registry_id=registry_id,
                external_name=external_name,
            ),
            "registry-projects",
        )

    def get_registry_project(
        self, registry_project_id: RegistryProject | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> RegistryProject | None:
        return self._get_single_resource(
            RegistryProject,
            "registry-projects",
            registry_project_id,
            include="registry",
            **params,
        )

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
                registry_id=registry_id,
                external_name=external_name,
            ),
            "registry-projects",
            registry_project_id,
        )

    def get_registry_projects(self, **params: te.Unpack[GetKwargs]) -> list[RegistryProject]:
        return self._get_all_resources(
            RegistryProject,
            "registry-projects",
            include="registry",
            **params,
        )

    def find_registry_projects(self, **params: te.Unpack[FindAllKwargs]) -> list[RegistryProject]:
        return self._find_all_resources(
            RegistryProject,
            "registry-projects",
            include="registry",
            **params,
        )

    def get_analysis_log(
        self, analysis_log_id: AnalysisLog | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> AnalysisLog | None:
        return self._get_single_resource(AnalysisLog, "analysis-logs", analysis_log_id, include="analysis", **params)

    def delete_analysis_log(self, analysis_log_id: AnalysisLog | uuid.UUID | str):
        self._delete_resource("analysis-logs", analysis_log_id)

    def get_analysis_logs(self, **params: te.Unpack[GetKwargs]) -> list[AnalysisLog]:
        return self._get_all_resources(AnalysisLog, "analysis-logs", include="analysis", **params)

    def find_analysis_logs(self, **params: te.Unpack[FindAllKwargs]) -> list[AnalysisLog]:
        return self._find_all_resources(AnalysisLog, "analysis-logs", include="analysis", **params)
