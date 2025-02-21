import typing as t
import uuid

import httpx
from pydantic import BaseModel

import urllib.parse

from flame_hub.flow import PasswordAuth, RobotAuth
from flame_hub.common import merge_parse_result, join_url_path

# base resource type which assumes BaseModel as the base class
ResourceT = t.TypeVar("ResourceT", bound=BaseModel)


# structural subtype which expects a BaseModel to have an id property
class UuidModel(t.Protocol[ResourceT]):
    id: uuid.UUID


# union which encompasses all types where a UUID can be extracted from
UuidIdentifiable = t.Union[UuidModel, uuid.UUID, str]


def obtain_uuid_from(uuid_identifiable: UuidIdentifiable) -> uuid.UUID:
    """Extract a UUID from a model containing an ID property, a string or a UUID object."""
    if isinstance(uuid_identifiable, BaseModel):
        uuid_identifiable = getattr(uuid_identifiable, "id")

    if isinstance(uuid_identifiable, str):
        return uuid.UUID(uuid_identifiable)

    if isinstance(uuid_identifiable, uuid.UUID):
        return uuid_identifiable

    raise ValueError(f"{uuid_identifiable} cannot be converted into a UUID")


# resource for meta information on list responses
class ResourceListMeta(BaseModel):
    total: int


# resource for list responses
class ResourceList(BaseModel, t.Generic[ResourceT]):
    data: list[ResourceT]
    meta: ResourceListMeta


class BaseClient(object):
    def __init__(self, base_url: str, client: httpx.Client = None, auth: t.Union[PasswordAuth, RobotAuth] = None):
        self._base_url = urllib.parse.urlsplit(base_url)
        self._client = client or httpx.Client(auth=auth)

    def _get_all_resources(self, resource_type: type[ResourceT], *path: str):
        r = self._client.get(
            merge_parse_result(self._base_url, path=join_url_path(self._base_url.path, "/".join(path))),
        )

        assert r.status_code == httpx.codes.OK.value
        return ResourceList[resource_type](**r.json())

    def _create_resource(self, resource_type: type[ResourceT], resource: BaseModel, *path: str) -> ResourceT:
        r = self._client.post(
            merge_parse_result(self._base_url, path=join_url_path(self._base_url.path, "/".join(path))),
            json=resource.model_dump(mode="json"),
        )

        assert r.status_code == httpx.codes.CREATED.value
        return resource_type(**r.json())

    def _get_single_resource(
        self, resource_type: type[ResourceT], resource_id: UuidIdentifiable, *path: str
    ) -> ResourceT | None:
        path = (*path, str(obtain_uuid_from(resource_id)))

        r = self._client.get(
            merge_parse_result(self._base_url, path=join_url_path(self._base_url.path, "/".join(path))),
        )

        if r.status_code == httpx.codes.NOT_FOUND.value:
            return None

        assert r.status_code == httpx.codes.OK.value
        return resource_type(**r.json())

    def _update_resource(
        self,
        resource_type: type[ResourceT],
        resource_id: UuidIdentifiable,
        resource: BaseModel,
        *path: str,
    ) -> ResourceT:
        path = (*path, str(obtain_uuid_from(resource_id)))

        r = self._client.post(
            merge_parse_result(self._base_url, path=join_url_path(self._base_url.path, "/".join(path))),
            json=resource.model_dump(mode="json", exclude_none=True),
        )

        assert r.status_code == httpx.codes.ACCEPTED.value
        return resource_type(**r.json())

    def _delete_resource(self, resource_id: t.Union[UuidModel, str, uuid.UUID], *path: str):
        path = (*path, str(obtain_uuid_from(resource_id)))

        r = self._client.delete(
            merge_parse_result(self._base_url, path=join_url_path(self._base_url.path, "/".join(path))),
        )

        assert r.status_code == httpx.codes.ACCEPTED.value
