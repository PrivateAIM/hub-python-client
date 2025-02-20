__all__ = ["AuthClient"]

import typing as t
import urllib.parse
import uuid
from datetime import datetime

import httpx
from pydantic import BaseModel

from flame_hub import common, flow


class CreateRealm(BaseModel):
    name: str
    display_name: str | None
    description: str | None


class UpdateRealm(BaseModel):
    name: str | None
    display_name: str | None
    description: str | None


class Realm(CreateRealm):
    id: uuid.UUID
    built_in: bool
    created_at: datetime
    updated_at: datetime


class AuthClient(object):
    def __init__(
        self,
        base_url=common.DEFAULT_AUTH_BASE_URL,
        client: httpx.Client = None,
        auth: t.Union[flow.RobotAuth, flow.PasswordAuth] = None,
    ):
        self._base_url = urllib.parse.urlsplit(base_url)
        self._client = client or httpx.Client(auth=auth)

    def get_realms(self) -> common.ResourceList[Realm]:
        r = self._client.get(
            common.merge_parse_result(self._base_url, path=common.join_url_path(self._base_url.path, "realms")),
        )

        assert r.status_code == httpx.codes.OK.value
        return common.ResourceList[Realm](**r.json())

    def create_realm(self, name: str, display_name: str = None, description: str = None) -> Realm:
        r = self._client.post(
            common.merge_parse_result(self._base_url, path=common.join_url_path(self._base_url.path, "realms")),
            json=CreateRealm(
                name=name,
                display_name=display_name,
                description=description,
            ).model_dump(mode="json"),
        )

        assert r.status_code == httpx.codes.CREATED.value
        return Realm(**r.json())

    def delete_realm(self, realm_id: Realm | str | uuid.UUID):
        if isinstance(realm_id, Realm):
            realm_id = realm_id.id

        r = self._client.delete(
            common.merge_parse_result(
                self._base_url, path=common.join_url_path(self._base_url.path, f"realms/{realm_id}")
            ),
        )

        assert r.status_code == httpx.codes.ACCEPTED.value

    def get_realm(self, realm_id: Realm | str | uuid.UUID) -> Realm | None:
        if isinstance(realm_id, Realm):
            realm_id = realm_id.id

        r = self._client.get(
            common.merge_parse_result(
                self._base_url, path=common.join_url_path(self._base_url.path, f"realms/{realm_id}")
            ),
        )

        if r.status_code == httpx.codes.NOT_FOUND.value:
            return None

        assert r.status_code == httpx.codes.OK.value
        return Realm(**r.json())

    def update_realm(
        self, realm_id: Realm | str | uuid.UUID, name: str = None, display_name: str = None, description: str = None
    ) -> Realm:
        if isinstance(realm_id, Realm):
            realm_id = realm_id.id

        r = self._client.post(
            common.merge_parse_result(
                self._base_url, path=common.join_url_path(self._base_url.path, f"realms/{realm_id}")
            ),
            json=UpdateRealm(
                name=name,
                display_name=display_name,
                description=description,
            ).model_dump(mode="json", exclude_none=True),
        )

        assert r.status_code == httpx.codes.ACCEPTED.value
        return Realm(**r.json())
