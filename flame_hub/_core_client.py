from enum import Enum
import typing as t
import uuid
from datetime import datetime

import httpx2 as httpx
import typing_extensions as te
from pydantic import BaseModel, WrapValidator, Field, BeforeValidator

from flame_hub._auth_client import Realm
from flame_hub._base_client import (
    BaseClient,
    obtain_uuid_from,
    UNSET,
    UNSET_T,
    FindAllKwargs,
    GetKwargs,
    ClientKwargs,
    uuid_validator,
    IsOptionalField,
    IsIncludable,
    get_includable_names,
    build_filter_params,
    ResourceListResult,
    AuthParam,
    BaseKwargs,
    unwrap_enveloped_resource,
)
from flame_hub._defaults import DEFAULT_CORE_BASE_URL
from flame_hub._storage_client import Bucket, BucketFile

RegistryCommand = t.Literal["setup", "cleanup"]


class CreateRegistry(BaseModel):
    name: str
    host: str
    accountName: str | None
    accountSecret: t.Annotated[str | None, IsOptionalField] = None


class Registry(CreateRegistry):
    id: uuid.UUID
    createdAt: datetime
    updatedAt: datetime


class UpdateRegistry(BaseModel):
    name: str | UNSET_T = UNSET
    host: str | UNSET_T = UNSET
    accountName: str | None | UNSET_T = UNSET
    accountSecret: str | None | UNSET_T = UNSET


RegistryProjectType = t.Literal["default", "aggregator", "incoming", "outgoing", "masterImages", "node"]


class CreateRegistryProject(BaseModel):
    name: str
    type: RegistryProjectType
    registryId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    externalName: str
    accountName: str | None
    accountSecret: t.Annotated[str | None, IsOptionalField] = None


class RegistryProject(CreateRegistryProject):
    id: uuid.UUID
    public: bool
    externalId: str | None
    accountId: str | None
    webhookName: str | None
    webhookExists: bool | None
    realmId: uuid.UUID | None
    registry: t.Annotated[Registry, IsIncludable] = None
    createdAt: datetime
    updatedAt: datetime


class UpdateRegistryProject(BaseModel):
    name: str | UNSET_T = UNSET
    type: RegistryProjectType | UNSET_T = UNSET
    registryId: t.Annotated[uuid.UUID | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET
    externalName: str | UNSET_T = UNSET
    accountName: str | None | UNSET_T = UNSET
    accountSecret: str | None | UNSET_T = UNSET


NodeType = t.Literal["aggregator", "default"]


class CreateNode(BaseModel):
    externalName: str | None
    hidden: bool | None
    name: str
    realmId: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    registryId: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    type: NodeType | None


class Node(CreateNode):
    id: uuid.UUID
    publicKey: str | None
    online: bool
    registry: t.Annotated[Registry | None, IsIncludable] = None
    registryProjectId: uuid.UUID | None
    registryProject: t.Annotated[RegistryProject | None, IsIncludable] = None
    clientId: uuid.UUID | None
    createdAt: datetime
    updatedAt: datetime


class UpdateNode(BaseModel):
    hidden: bool | UNSET_T = UNSET
    externalName: str | None | UNSET_T = UNSET
    type: NodeType | UNSET_T = UNSET
    publicKey: str | None | UNSET_T = UNSET
    realmId: t.Annotated[uuid.UUID | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET
    registryId: t.Annotated[uuid.UUID | None | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET


class NodeRegistryCredentials(BaseModel):
    host: str
    externalName: str
    accountName: str | None
    accountSecret: str | None


class ClientCredentials(BaseModel):
    id: uuid.UUID
    secret: str | None
    name: str
    displayName: str


class UpdateClientCredentials(BaseModel):
    secret: str | None | UNSET_T = UNSET
    name: str | UNSET_T = UNSET
    displayName: str | UNSET_T = UNSET


class MasterImageGroup(BaseModel):
    id: uuid.UUID
    name: str
    path: str
    virtualPath: str
    createdAt: datetime
    updatedAt: datetime


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


ProcessStatus = t.Literal["starting", "started", "stopping", "stopped", "executing", "executed", "failed"]


class MasterImage(BaseModel):
    id: uuid.UUID
    path: str | None
    virtualPath: str
    groupVirtualPath: str
    buildStatus: ProcessStatus | None
    buildProgress: int | None
    name: str
    command: str | None
    commandArguments: t.Annotated[list[MasterImageCommandArgument] | None, BeforeValidator(ensure_position_none)]
    createdAt: datetime
    updatedAt: datetime


class CreateProject(BaseModel):
    description: str | None
    masterImageId: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    name: str
    displayName: str | None


class Project(CreateProject):
    id: uuid.UUID
    analyses: int
    nodes: int
    masterImage: t.Annotated[MasterImage | None, IsIncludable] = None
    createdAt: datetime
    updatedAt: datetime
    realmId: uuid.UUID
    userId: uuid.UUID | None


class UpdateProject(BaseModel):
    description: str | None | UNSET_T = UNSET
    masterImageId: t.Annotated[uuid.UUID | None | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET
    name: str | UNSET_T = UNSET
    displayName: str | None | UNSET_T = UNSET


ProjectNodeApprovalStatus = t.Literal["rejected", "approved"]


class CreateProjectNode(BaseModel):
    nodeId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    projectId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class ProjectNode(CreateProjectNode):
    id: uuid.UUID
    approvalStatus: ProjectNodeApprovalStatus | None
    comment: str | None
    createdAt: datetime
    updatedAt: datetime
    node: t.Annotated[Node, IsIncludable] = None
    project: t.Annotated[Project, IsIncludable] = None
    projectRealmId: uuid.UUID
    nodeRealmId: uuid.UUID


class UpdateProjectNode(BaseModel):
    comment: str | None | UNSET_T = UNSET
    approvalStatus: ProjectNodeApprovalStatus | None | UNSET_T = UNSET


LogLevel = t.Literal["emerg", "alert", "crit", "error", "warn", "notice", "info", "debug"]
LogChannel = t.Literal["http", "websocket", "background", "system"]


class Log(BaseModel):
    time: str
    message: str
    service: str
    channel: LogChannel
    level: LogLevel
    labels: dict[str, str | None]


class CreateAnalysis(BaseModel):
    description: str | None
    name: str | None
    displayName: str | None
    projectId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    masterImageId: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    registryId: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    imageCommandArguments: t.Annotated[
        list[MasterImageCommandArgument],
        Field(default_factory=list),
        BeforeValidator(lambda args: [] if args is None else ensure_position_none(args)),
    ]


class Analysis(CreateAnalysis):
    id: uuid.UUID
    nodes: int
    nodesApproved: int
    configurationLocked: bool
    configurationEntrypointValid: bool
    configurationImageValid: bool
    configurationNodeAggregatorValid: bool
    configurationNodeDefaultValid: bool
    configurationNodesValid: bool
    buildStatus: ProcessStatus | None
    buildNodesValid: bool
    buildProgress: int | None
    buildHash: str | None
    buildOs: str | None
    buildSize: int | None
    distributionStatus: ProcessStatus | None
    distributionProgress: int | None
    executionStatus: ProcessStatus | None
    executionProgress: int | None
    createdAt: datetime
    updatedAt: datetime
    registry: t.Annotated[Registry | None, IsIncludable] = None
    realmId: uuid.UUID
    userId: uuid.UUID
    clientId: uuid.UUID | None
    projectId: uuid.UUID
    project: t.Annotated[Project, IsIncludable] = None
    masterImage: t.Annotated[MasterImage | None, IsIncludable] = None


class UpdateAnalysis(BaseModel):
    description: str | None | UNSET_T = UNSET
    name: str | UNSET_T = UNSET
    displayName: str | None | UNSET_T = UNSET
    masterImageId: t.Annotated[uuid.UUID | None | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET
    imageCommandArguments: (
        t.Annotated[
            list[MasterImageCommandArgument],
            BeforeValidator(lambda args: ensure_position_none(args)),
        ]
        | UNSET_T
    ) = UNSET


AnalysisCommand = t.Literal[
    "buildStart",
    "buildCheck",
    "configurationLock",
    "configurationUnlock",
    "distributionStart",
    "distributionCheck",
    "storageCheck",
]


class CreateAnalysisNode(BaseModel):
    analysisId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    nodeId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


AnalysisNodeApprovalStatus = t.Literal["rejected", "approved"]


class AnalysisNode(CreateAnalysisNode):
    id: uuid.UUID
    approvalStatus: AnalysisNodeApprovalStatus | None
    executionStatus: ProcessStatus | None
    executionProgress: int | None
    comment: str | None
    artifactTag: str | None
    artifactDigest: str | None
    createdAt: datetime
    updatedAt: datetime
    analysis: t.Annotated[Analysis, IsIncludable] = None
    node: t.Annotated[Node, IsIncludable] = None
    analysisRealmId: uuid.UUID
    nodeRealmId: uuid.UUID


class UpdateAnalysisNode(BaseModel):
    comment: str | None | UNSET_T = UNSET
    approvalStatus: AnalysisNodeApprovalStatus | None | UNSET_T = UNSET
    executionStatus: ProcessStatus | None | UNSET_T = UNSET
    executionProgress: int | None | UNSET_T = UNSET


class CreateAnalysisNodeLog(BaseModel):
    analysisId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    nodeId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    code: str | None
    status: str | None
    message: str
    level: LogLevel


class AnalysisBucketType(str, Enum):
    CODE = "CODE"
    RESULT = "RESULT"
    TEMP = "TEMP"


class CreateAnalysisBucket(BaseModel):
    type: AnalysisBucketType
    bucketId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    analysisId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class AnalysisBucket(CreateAnalysisBucket):
    id: uuid.UUID
    createdAt: datetime
    updatedAt: datetime
    analysis: t.Annotated[Analysis, IsIncludable] = None
    realmId: uuid.UUID


class CreateAnalysisBucketFile(BaseModel):
    path: str
    bucketFileId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    bucketId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    analysisBucketId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    root: bool


class AnalysisBucketFile(CreateAnalysisBucketFile):
    id: uuid.UUID
    createdAt: datetime
    updatedAt: datetime
    analysisBucket: t.Annotated[AnalysisBucket, IsIncludable] = None
    realmId: uuid.UUID
    userId: uuid.UUID | None
    clientId: uuid.UUID | None
    analysisId: uuid.UUID
    analysis: t.Annotated[Analysis, IsIncludable] = None


class UpdateAnalysisBucketFile(BaseModel):
    root: bool | UNSET_T = UNSET


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
        auth: AuthParam = None,
        **kwargs: te.Unpack[ClientKwargs],
    ):
        super().__init__(base_url, auth, **kwargs)

    def _unwrap_single_resource(self, body: t.Any) -> t.Any:
        """Extract the resource object from the core service's record envelope.

        Since ``0.13.0`` the FLAME Hub responds to record requests with :python:`{"data": ..., "meta": ...}` instead
        of the resource object itself, mirroring the envelope that list responses have always used. ``meta`` holds
        response-scoped extras such as the queryable schema of the endpoint and is discarded.

        The credential endpoints keep responding with a bare object and pass :python:`envelope=False` instead of
        going through this method.

        Raises
        ------
        :py:exc:`ValueError`
            If ``body`` does not carry a ``data`` property, which is the case for FLAME Hub versions before ``0.13.0``.

        See Also
        --------
        :py:meth:`.BaseClient._unwrap_single_resource`, :py:func:`.unwrap_enveloped_resource`
        """
        return unwrap_enveloped_resource(body, "FLAME Hub 0.13.0")

    def get_nodes(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Node]:
        return self._get_all_resources(Node, "nodes", include=get_includable_names(Node), **params)

    def find_nodes(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Node]:
        return self._find_all_resources(Node, "nodes", include=get_includable_names(Node), **params)

    def create_node(
        self,
        name: str,
        realmId: Realm | str | uuid.UUID | None = None,
        registryId: Registry | uuid.UUID | str | None = None,
        externalName: str | None = None,
        node_type: NodeType = "default",
        hidden: bool = False,
        **params: te.Unpack[BaseKwargs],
    ) -> Node:
        return self._create_resource(
            Node,
            CreateNode(
                name=name,
                realmId=realmId,
                externalName=externalName,
                hidden=hidden,
                registryId=registryId,
                type=node_type,
            ),
            "nodes",
            **params,
        )

    def get_node(self, nodeId: Node | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Node | None:
        return self._get_single_resource(Node, "nodes", nodeId, include=get_includable_names(Node), **params)

    def delete_node(
        self,
        nodeId: Node | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._delete_resource("nodes", nodeId, **params)

    def update_node(
        self,
        nodeId: Node | uuid.UUID | str,
        externalName: str | None | UNSET_T = UNSET,
        hidden: bool | UNSET_T = UNSET,
        node_type: NodeType | UNSET_T = UNSET,
        realmId: Realm | str | uuid.UUID | UNSET_T = UNSET,
        registryId: Registry | str | uuid.UUID | None | UNSET_T = UNSET,
        publicKey: str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Node:
        return self._update_resource(
            Node,
            UpdateNode(
                externalName=externalName,
                hidden=hidden,
                type=node_type,
                publicKey=publicKey,
                realmId=realmId,
                registryId=registryId,
            ),
            "nodes",
            nodeId,
            **params,
        )

    def get_node_registry_credentials(
        self,
        nodeId: Node | uuid.UUID | str,
        **params: te.Unpack[GetKwargs],
    ) -> NodeRegistryCredentials | None:
        """Returns the node's registry project credentials."""

        return self._get_single_resource(
            NodeRegistryCredentials,
            "nodes",
            nodeId,
            "registry",
            "credentials",
            envelope=False,
            **params,
        )

    def get_node_client_credentials(
        self,
        nodeId: Node | uuid.UUID | str,
        **params: te.Unpack[GetKwargs],
    ) -> ClientCredentials | None:
        """Returns the node's client credentials."""

        return self._get_single_resource(
            ClientCredentials,
            "nodes",
            nodeId,
            "client",
            "credentials",
            envelope=False,
            **params,
        )

    def update_node_client_credentials(
        self,
        nodeId: Node | uuid.UUID | str,
        secret: str | None | UNSET_T = UNSET,
        name: str | UNSET_T = UNSET,
        displayName: str | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> ClientCredentials:
        """Update the node's client credentials. If ``secret`` is set to :any:`None`, then the Hub will create and set
        a random secret."""

        return self._update_resource(
            ClientCredentials,
            UpdateClientCredentials(
                secret=secret,
                name=name,
                displayName=displayName,
            ),
            "nodes",
            nodeId,
            "client",
            "credentials",
            expected_code=httpx.codes.OK.value,
            envelope=False,
            **params,
        )

    def get_master_image_groups(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[MasterImageGroup]:
        return self._get_all_resources(MasterImageGroup, "master-image-groups", **params)

    def get_master_image_group(
        self, masterImageGroupId: MasterImageGroup | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> MasterImageGroup | None:
        return self._get_single_resource(MasterImageGroup, "master-image-groups", masterImageGroupId, **params)

    def find_master_image_groups(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[MasterImageGroup]:
        return self._find_all_resources(MasterImageGroup, "master-image-groups", **params)

    def get_master_images(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[MasterImage]:
        return self._get_all_resources(MasterImage, "master-images", **params)

    def get_master_image(
        self, masterImageId: MasterImage | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> MasterImage | None:
        return self._get_single_resource(MasterImage, "master-images", masterImageId, **params)

    def find_master_images(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[MasterImage]:
        return self._find_all_resources(MasterImage, "master-images", **params)

    def get_projects(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Project]:
        return self._get_all_resources(Project, "projects", include=get_includable_names(Project), **params)

    def find_projects(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Project]:
        return self._find_all_resources(Project, "projects", include=get_includable_names(Project), **params)

    def sync_master_images(self, **params: te.Unpack[BaseKwargs]):
        """This method will start to synchronize the master images. Note that an error is raised if you request a
        synchronization while the Hub instance is still synchronizing master images.
        """

        self._request(
            "POST",
            "master-images",
            "command",
            expected_code=httpx.codes.ACCEPTED.value,
            json={"command": "sync"},
            **params,
        )

    def build_master_image(self, masterImageId: MasterImage | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        """This method will command the Hub to start building a master image. Note that building a master image could
        take some time.
        """

        self._request(
            "POST",
            "master-images",
            "command",
            expected_code=httpx.codes.ACCEPTED.value,
            json={"command": "build", "id": str(obtain_uuid_from(masterImageId))},
            **params,
        )

    def create_project(
        self,
        name: str,
        displayName: str | None = None,
        masterImageId: MasterImage | uuid.UUID | str | None = None,
        description: str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> Project:
        return self._create_resource(
            Project,
            CreateProject(
                name=name,
                masterImageId=masterImageId,
                description=description,
                displayName=displayName,
            ),
            "projects",
            **params,
        )

    def delete_project(self, projectId: Project | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("projects", projectId, **params)

    def get_project(self, projectId: Project | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Project | None:
        return self._get_single_resource(
            Project, "projects", projectId, include=get_includable_names(Project), **params
        )

    def update_project(
        self,
        projectId: Project | uuid.UUID | str,
        description: str | None | UNSET_T = UNSET,
        masterImageId: MasterImage | str | uuid.UUID | None | UNSET_T = UNSET,
        name: str | UNSET_T = UNSET,
        displayName: str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Project:
        return self._update_resource(
            Project,
            UpdateProject(description=description, masterImageId=masterImageId, name=name, displayName=displayName),
            "projects",
            projectId,
            **params,
        )

    def create_project_node(
        self, projectId: Project | uuid.UUID | str, nodeId: Node | uuid.UUID | str, **params: te.Unpack[BaseKwargs]
    ) -> ProjectNode:
        return self._create_resource(
            ProjectNode,
            CreateProjectNode(projectId=projectId, nodeId=nodeId),
            "project-nodes",
            **params,
        )

    def delete_project_node(self, projectNodeId: ProjectNode | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("project-nodes", projectNodeId, **params)

    def get_project_nodes(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[ProjectNode]:
        return self._get_all_resources(
            ProjectNode, "project-nodes", include=get_includable_names(ProjectNode), **params
        )

    def find_project_nodes(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[ProjectNode]:
        return self._find_all_resources(
            ProjectNode, "project-nodes", include=get_includable_names(ProjectNode), **params
        )

    def get_project_node(
        self, projectNodeId: ProjectNode | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> ProjectNode | None:
        return self._get_single_resource(
            ProjectNode, "project-nodes", projectNodeId, include=get_includable_names(ProjectNode), **params
        )

    def update_project_node(
        self,
        projectNodeId: ProjectNode | uuid.UUID | str,
        comment: str | None | UNSET_T = UNSET,
        approvalStatus: ProjectNodeApprovalStatus | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ):
        return self._update_resource(
            ProjectNode,
            UpdateProjectNode(comment=comment, approvalStatus=approvalStatus),
            "project-nodes",
            projectNodeId,
            **params,
        )

    def create_analysis(
        self,
        projectId: Project | uuid.UUID | str,
        name: str | None = None,
        displayName: str | None = None,
        description: str | None = None,
        masterImageId: MasterImage | uuid.UUID | str | None = None,
        registryId: Registry | uuid.UUID | str | None = None,
        imageCommandArguments: list[MasterImageCommandArgument] | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> Analysis:
        return self._create_resource(
            Analysis,
            CreateAnalysis(
                projectId=projectId,
                name=name,
                displayName=displayName,
                description=description,
                masterImageId=masterImageId,
                registryId=registryId,
                imageCommandArguments=imageCommandArguments,
            ),
            "analyses",
            **params,
        )

    def delete_analysis(self, analysisId: Analysis | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("analyses", analysisId, **params)

    def get_analyses(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Analysis]:
        return self._get_all_resources(Analysis, "analyses", include=get_includable_names(Analysis), **params)

    def find_analyses(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Analysis]:
        return self._find_all_resources(Analysis, "analyses", include=get_includable_names(Analysis), **params)

    def get_analysis(self, analysisId: Analysis | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Analysis | None:
        return self._get_single_resource(
            Analysis, "analyses", analysisId, include=get_includable_names(Analysis), **params
        )

    def update_analysis(
        self,
        analysisId: Analysis | uuid.UUID | str,
        name: str | None | UNSET_T = UNSET,
        displayName: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        masterImageId: MasterImage | uuid.UUID | str | None | UNSET_T = UNSET,
        imageCommandArguments: list[MasterImageCommandArgument] | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Analysis:
        return self._update_resource(
            Analysis,
            UpdateAnalysis(
                name=name,
                displayName=displayName,
                description=description,
                masterImageId=masterImageId,
                imageCommandArguments=imageCommandArguments,
            ),
            "analyses",
            analysisId,
            **params,
        )

    def send_analysis_command(
        self,
        analysisId: Analysis | uuid.UUID | str,
        command: AnalysisCommand,
        **params: te.Unpack[BaseKwargs],
    ) -> Analysis:
        r = self._request(
            "POST",
            "analyses",
            obtain_uuid_from(analysisId),
            "command",
            expected_code=httpx.codes.ACCEPTED.value,
            json={"command": command},
            **params,
        )

        return Analysis(**self._unwrap_single_resource(r.json()))

    def get_analysis_client_credentials(
        self,
        analysisId: Analysis | uuid.UUID | str,
        **params: te.Unpack[GetKwargs],
    ) -> ClientCredentials | None:
        """Returns the client credentials of the analysis."""

        return self._get_single_resource(
            ClientCredentials,
            "analyses",
            analysisId,
            "client",
            "credentials",
            envelope=False,
            **params,
        )

    def update_analysis_client_credentials(
        self,
        analysisId: Analysis | uuid.UUID | str,
        secret: str | None | UNSET_T = UNSET,
        name: str | UNSET_T = UNSET,
        displayName: str | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> ClientCredentials:
        """Update the client credentials of the analysis. If ``secret`` is set to :any:`None`, then the Hub will create
        and set a random secret."""

        return self._update_resource(
            ClientCredentials,
            UpdateClientCredentials(
                secret=secret,
                name=name,
                displayName=displayName,
            ),
            "analyses",
            analysisId,
            "client",
            "credentials",
            expected_code=httpx.codes.OK.value,
            envelope=False,
            **params,
        )

    def create_analysis_node(
        self, analysisId: Analysis | uuid.UUID | str, nodeId: Node | uuid.UUID | str, **params: te.Unpack[BaseKwargs]
    ) -> AnalysisNode:
        return self._create_resource(
            AnalysisNode,
            CreateAnalysisNode(analysisId=analysisId, nodeId=nodeId),
            "analysis-nodes",
            **params,
        )

    def delete_analysis_node(self, analysisNodeId: AnalysisNode | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("analysis-nodes", analysisNodeId, **params)

    def update_analysis_node(
        self,
        analysisNodeId: AnalysisNode | uuid.UUID | str,
        comment: str | None | UNSET_T = UNSET,
        approvalStatus: AnalysisNodeApprovalStatus | None | UNSET_T = UNSET,
        executionStatus: ProcessStatus | None | UNSET_T = UNSET,
        executionProgress: int | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> AnalysisNode:
        return self._update_resource(
            AnalysisNode,
            UpdateAnalysisNode(
                comment=comment,
                approvalStatus=approvalStatus,
                executionStatus=executionStatus,
                executionProgress=executionProgress,
            ),
            "analysis-nodes",
            analysisNodeId,
            **params,
        )

    def get_analysis_node(
        self, analysisNodeId: AnalysisNode | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> AnalysisNode | None:
        return self._get_single_resource(
            AnalysisNode, "analysis-nodes", analysisNodeId, include=get_includable_names(AnalysisNode), **params
        )

    def get_analysis_nodes(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[AnalysisNode]:
        return self._get_all_resources(
            AnalysisNode, "analysis-nodes", include=get_includable_names(AnalysisNode), **params
        )

    def find_analysis_nodes(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[AnalysisNode]:
        return self._find_all_resources(
            AnalysisNode, "analysis-nodes", include=get_includable_names(AnalysisNode), **params
        )

    def create_analysis_node_log(
        self,
        analysisId: Analysis | uuid.UUID | str,
        nodeId: Node | uuid.UUID | str,
        level: LogLevel,
        message: str,
        status: str | None = None,
        code: str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> Log:
        return self._create_resource(
            Log,
            CreateAnalysisNodeLog(
                analysisId=analysisId,
                nodeId=nodeId,
                level=level,
                message=message,
                status=status,
                code=code,
            ),
            "analysis-node-logs",
            expected_code=httpx.codes.ACCEPTED.value,
            **params,
        )

    def delete_analysis_node_logs(
        self,
        analysisId: Analysis | uuid.UUID | str,
        nodeId: Node | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._request(
            "DELETE",
            "analysis-node-logs",
            expected_code=httpx.codes.ACCEPTED.value,
            params=build_filter_params(
                {
                    "analysisId": str(obtain_uuid_from(analysisId)),
                    "nodeId": str(obtain_uuid_from(nodeId)),
                }
            ),
            **params,
        )

    def find_analysis_node_logs(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Log]:
        return self._find_all_resources(Log, "analysis-node-logs", **params)

    def create_analysis_bucket(
        self,
        bucket_type: AnalysisBucketType,
        bucketId: Bucket | uuid.UUID | str,
        analysisId: Analysis | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ) -> AnalysisBucket:
        return self._create_resource(
            AnalysisBucket,
            CreateAnalysisBucket(
                type=bucket_type,
                bucketId=bucketId,
                analysisId=analysisId,
            ),
            "analysis-buckets",
            **params,
        )

    def delete_analysis_bucket(
        self,
        analysisBucketId: AnalysisBucket | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._delete_resource("analysis-buckets", analysisBucketId, **params)

    def get_analysis_buckets(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[AnalysisBucket]:
        return self._get_all_resources(
            AnalysisBucket, "analysis-buckets", include=get_includable_names(AnalysisBucket), **params
        )

    def find_analysis_buckets(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[AnalysisBucket]:
        return self._find_all_resources(
            AnalysisBucket, "analysis-buckets", include=get_includable_names(AnalysisBucket), **params
        )

    def get_analysis_bucket(
        self, analysisBucketId: AnalysisBucket | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> AnalysisBucket | None:
        return self._get_single_resource(
            AnalysisBucket,
            "analysis-buckets",
            analysisBucketId,
            include=get_includable_names(AnalysisBucket),
            **params,
        )

    def get_analysis_bucket_files(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[AnalysisBucketFile]:
        return self._get_all_resources(
            AnalysisBucketFile, "analysis-bucket-files", include=get_includable_names(AnalysisBucketFile), **params
        )

    def find_analysis_bucket_files(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[AnalysisBucketFile]:
        return self._find_all_resources(
            AnalysisBucketFile, "analysis-bucket-files", include=get_includable_names(AnalysisBucketFile), **params
        )

    def get_analysis_bucket_file(
        self, analysisBucketFileId: AnalysisBucketFile | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> AnalysisBucketFile | None:
        return self._get_single_resource(
            AnalysisBucketFile,
            "analysis-bucket-files",
            analysisBucketFileId,
            include=get_includable_names(AnalysisBucketFile),
            **params,
        )

    def delete_analysis_bucket_file(
        self,
        analysisBucketFileId: AnalysisBucketFile | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._delete_resource("analysis-bucket-files", analysisBucketFileId, **params)

    def create_analysis_bucket_file(
        self,
        path: str,
        bucketFileId: BucketFile | uuid.UUID | str,
        bucketId: Bucket | uuid.UUID | str,
        analysisBucketId: AnalysisBucket | uuid.UUID | str,
        is_entrypoint: bool = False,
        **params: te.Unpack[BaseKwargs],
    ) -> AnalysisBucketFile:
        return self._create_resource(
            AnalysisBucketFile,
            CreateAnalysisBucketFile(
                bucketFileId=bucketFileId,
                bucketId=bucketId,
                analysisBucketId=analysisBucketId,
                path=path,
                root=is_entrypoint,
            ),
            "analysis-bucket-files",
            **params,
        )

    def update_analysis_bucket_file(
        self,
        analysisBucketFileId: AnalysisBucketFile | uuid.UUID | str,
        is_entrypoint: bool | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> AnalysisBucketFile:
        return self._update_resource(
            AnalysisBucketFile,
            UpdateAnalysisBucketFile(root=is_entrypoint),
            "analysis-bucket-files",
            analysisBucketFileId,
            **params,
        )

    def create_registry(
        self,
        name: str,
        host: str,
        accountName: str | None = None,
        accountSecret: str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> Registry:
        return self._create_resource(
            Registry,
            CreateRegistry(name=name, host=host, accountName=accountName, accountSecret=accountSecret),
            "registries",
            **params,
        )

    def get_registry(self, registryId: Registry | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Registry | None:
        return self._get_single_resource(Registry, "registries", registryId, **params)

    def delete_registry(
        self,
        registryId: Registry | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._delete_resource("registries", registryId, **params)

    def update_registry(
        self,
        registryId: Registry | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        host: str | UNSET_T = UNSET,
        accountName: str | None | UNSET_T = UNSET,
        accountSecret: str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Registry:
        return self._update_resource(
            Registry,
            UpdateRegistry(name=name, host=host, accountName=accountName, accountSecret=accountSecret),
            "registries",
            registryId,
            **params,
        )

    def get_registries(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Registry]:
        return self._get_all_resources(Registry, "registries", **params)

    def find_registries(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Registry]:
        return self._find_all_resources(Registry, "registries", **params)

    def send_registry_command(
        self,
        registryId: Registry | uuid.UUID | str,
        command: RegistryCommand,
        **params: te.Unpack[BaseKwargs],
    ):
        self._request(
            "POST",
            "services",
            "registry",
            "command",
            expected_code=httpx.codes.ACCEPTED.value,
            json={"command": command, "id": str(obtain_uuid_from(registryId))},
            **params,
        )

    def create_registry_project(
        self,
        name: str,
        registry_project_type: RegistryProjectType,
        registryId: Registry | uuid.UUID | str,
        externalName: str,
        accountName: str | None = None,
        accountSecret: str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> RegistryProject:
        return self._create_resource(
            RegistryProject,
            CreateRegistryProject(
                name=name,
                type=registry_project_type,
                registryId=registryId,
                externalName=externalName,
                accountName=accountName,
                accountSecret=accountSecret,
            ),
            "registry-projects",
            **params,
        )

    def get_registry_project(
        self, registryProjectId: RegistryProject | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> RegistryProject | None:
        return self._get_single_resource(
            RegistryProject,
            "registry-projects",
            registryProjectId,
            include=get_includable_names(RegistryProject),
            **params,
        )

    def delete_registry_project(
        self,
        registryProjectId: RegistryProject | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._delete_resource("registry-projects", registryProjectId, **params)

    def update_registry_project(
        self,
        registryProjectId: RegistryProject | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        registry_project_type: RegistryProjectType | UNSET_T = UNSET,
        registryId: Registry | uuid.UUID | str | UNSET_T = UNSET,
        externalName: str | UNSET_T = UNSET,
        accountName: str | None | UNSET_T = UNSET,
        accountSecret: str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> RegistryProject:
        return self._update_resource(
            RegistryProject,
            UpdateRegistryProject(
                name=name,
                type=registry_project_type,
                registryId=registryId,
                externalName=externalName,
                accountName=accountName,
                accountSecret=accountSecret,
            ),
            "registry-projects",
            registryProjectId,
            **params,
        )

    def get_registry_projects(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[RegistryProject]:
        return self._get_all_resources(
            RegistryProject,
            "registry-projects",
            include=get_includable_names(RegistryProject),
            **params,
        )

    def find_registry_projects(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[RegistryProject]:
        return self._find_all_resources(
            RegistryProject,
            "registry-projects",
            include=get_includable_names(RegistryProject),
            **params,
        )

    def delete_analysis_logs(self, analysisId: Analysis | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._request(
            "DELETE",
            "analysis-logs",
            expected_code=httpx.codes.ACCEPTED.value,
            params=build_filter_params({"analysisId": str(obtain_uuid_from(analysisId))}),
            **params,
        )

    def find_analysis_logs(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Log]:
        return self._find_all_resources(Log, "analysis-logs", **params)
