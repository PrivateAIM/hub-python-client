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


class CreateRobot(BaseModel):
    name: str
    realm_id: uuid.UUID
    secret: str
    display_name: str | None


class Robot(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str | None
    description: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
    user_id: uuid.UUID | None
    realm_id: uuid.UUID


class UpdateRobot(BaseModel):
    display_name: str | None
    name: str | None
    realm_id: uuid.UUID | None
    secret: str | None


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

    def create_robot(
        self, name: str, realm_id: t.Union[Realm, str, uuid.UUID], secret: str, display_name: str = None
    ) -> Robot:
        if isinstance(realm_id, Realm):
            realm_id = realm_id.id

        # noinspection PyTypeChecker
        r = self._client.post(
            common.merge_parse_result(self._base_url, path=common.join_url_path(self._base_url.path, "robots")),
            json=CreateRobot(name=name, display_name=display_name, realm_id=str(realm_id), secret=secret).model_dump(
                mode="json"
            ),
        )

        assert r.status_code == httpx.codes.CREATED.value
        return Robot(**r.json())

    def delete_robot(self, robot_id: t.Union[Robot, str, uuid.UUID]):
        if isinstance(robot_id, Robot):
            robot_id = robot_id.id

        r = self._client.delete(
            common.merge_parse_result(
                self._base_url, path=common.join_url_path(self._base_url.path, f"robots/{robot_id}")
            ),
        )

        assert r.status_code == httpx.codes.ACCEPTED.value

    def get_robot(self, robot_id: t.Union[Robot, str, uuid.UUID]) -> Robot | None:
        if isinstance(robot_id, Robot):
            robot_id = robot_id.id

        r = self._client.get(
            common.merge_parse_result(
                self._base_url, path=common.join_url_path(self._base_url.path, f"robots/{robot_id}")
            ),
        )

        if r.status_code == httpx.codes.NOT_FOUND.value:
            return None

        assert r.status_code == httpx.codes.OK.value
        return Robot(**r.json())

    def update_robot(
        self,
        robot_id: t.Union[Robot, str, uuid.UUID],
        name: str = None,
        display_name: str = None,
        realm_id: t.Union[Realm, str, uuid.UUID] = None,
        secret: str = None,
    ) -> Robot:
        if isinstance(robot_id, Robot):
            robot_id = robot_id.id

        if isinstance(realm_id, Realm):
            realm_id = realm_id.id

        # noinspection PyTypeChecker
        r = self._client.post(
            common.merge_parse_result(
                self._base_url, path=common.join_url_path(self._base_url.path, f"robots/{robot_id}")
            ),
            json=UpdateRobot(
                name=name,
                display_name=display_name,
                realm_id=str(realm_id) if realm_id is not None else None,
                secret=secret,
            ).model_dump(mode="json", exclude_none=True),
        )

        assert r.status_code == httpx.codes.ACCEPTED.value
        return Robot(**r.json())
