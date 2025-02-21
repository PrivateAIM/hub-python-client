__all__ = ["CoreClient"]

import typing as t
import uuid
from datetime import datetime
from enum import Enum

import httpx
from pydantic import BaseModel

from flame_hub.auth import Realm
from flame_hub.base_client import BaseClient, ResourceList, obtain_uuid_from
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
