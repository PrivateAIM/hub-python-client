__all__ = ["CoreClient"]

import uuid
from datetime import datetime
from enum import Enum

import typing as t

import httpx
from pydantic import BaseModel

from flame_hub import common, flow

import urllib.parse

from flame_hub.auth import Realm


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


class CoreClient(object):
    def __init__(
        self,
        base_url=common.DEFAULT_CORE_BASE_URL,
        client: httpx.Client = None,
        auth: t.Union[flow.RobotAuth, flow.PasswordAuth] = None,
    ):
        self._base_url = urllib.parse.urlsplit(base_url)
        self._client = client or httpx.Client(auth=auth)

    def get_nodes(self) -> common.ResourceList[Node]:
        r = self._client.get(
            common.merge_parse_result(self._base_url, path=common.join_url_path(self._base_url.path, "nodes"))
        )

        assert r.status_code == httpx.codes.OK.value
        return common.ResourceList[Node](**r.json())

    def create_node(
        self,
        name: str,
        realm_id: t.Union[Realm, str, uuid.UUID],
        external_name: str | None = None,
        node_type: NodeType = NodeType.default,
        hidden: bool = False,
    ) -> Node:
        if isinstance(realm_id, Realm):
            realm_id = str(realm_id.id)

        # noinspection PyTypeChecker
        r = self._client.post(
            common.merge_parse_result(self._base_url, path=common.join_url_path(self._base_url.path, "nodes")),
            json=CreateNode(
                name=name,
                realm_id=str(realm_id),
                external_name=external_name,
                hidden=hidden,
                registry_id=None,  # TODO add registries
                type=node_type,
            ).model_dump(mode="json"),
        )

        assert r.status_code == httpx.codes.CREATED.value
        return Node(**r.json())

    def get_node(self, node_id: t.Union[Node, uuid.UUID, str]) -> Node | None:
        if isinstance(node_id, Node):
            node_id = node_id.id

        r = self._client.get(
            common.merge_parse_result(
                self._base_url, path=common.join_url_path(self._base_url.path, f"nodes/{node_id}")
            ),
        )

        if r.status_code == httpx.codes.NOT_FOUND.value:
            return None

        assert r.status_code == httpx.codes.OK.value
        return Node(**r.json())

    def delete_node(self, node_id: t.Union[Node, uuid.UUID, str]):
        if isinstance(node_id, Node):
            node_id = node_id.id

        r = self._client.delete(
            common.merge_parse_result(
                self._base_url, path=common.join_url_path(self._base_url.path, f"nodes/{node_id}")
            ),
        )

        assert r.status_code == httpx.codes.ACCEPTED.value

    def update_node(
        self,
        node_id: t.Union[Node, uuid.UUID, str],
        external_name: str = None,
        hidden: bool = None,
        node_type: NodeType = None,
        realm_id: t.Union[Realm, str, uuid.UUID] = None,
        public_key: str = None,
    ) -> Node:
        if isinstance(node_id, Node):
            node_id = node_id.id

        if isinstance(realm_id, Realm):
            realm_id = realm_id.id

        r = self._client.post(
            common.merge_parse_result(
                self._base_url, path=common.join_url_path(self._base_url.path, f"nodes/{node_id}")
            ),
            json=UpdateNode(
                external_name=external_name,
                hidden=hidden,
                type=node_type,
                public_key=public_key,
                realm_id=str(realm_id) if realm_id else None,
            ).model_dump(mode="json", exclude_none=True),
        )

        assert r.status_code == httpx.codes.ACCEPTED.value
        return Node(**r.json())
