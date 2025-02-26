__all__ = ["AuthClient"]

import typing as t
import uuid
from datetime import datetime

import httpx
from pydantic import BaseModel

from flame_hub.base_client import ResourceList, BaseClient, obtain_uuid_from, PageParams, FilterParams
from flame_hub.defaults import DEFAULT_AUTH_BASE_URL
from flame_hub.flow import RobotAuth, PasswordAuth


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


class AuthClient(BaseClient):
    def __init__(
        self,
        base_url=DEFAULT_AUTH_BASE_URL,
        client: httpx.Client = None,
        auth: t.Union[RobotAuth, PasswordAuth] = None,
    ):
        super().__init__(base_url, client, auth)

    def get_realms(self) -> ResourceList[Realm]:
        return self._get_all_resources(Realm, "realms")

    def find_realms(self, page_params: PageParams = None, filter_params: FilterParams = None) -> ResourceList[Realm]:
        return self._find_all_resources(Realm, page_params, filter_params, "realms")

    def create_realm(self, name: str, display_name: str = None, description: str = None) -> Realm:
        return self._create_resource(
            Realm,
            CreateRealm(
                name=name,
                display_name=display_name,
                description=description,
            ),
            "realms",
        )

    def delete_realm(self, realm_id: t.Union[Realm, uuid.UUID, str]):
        self._delete_resource(realm_id, "realms")

    def get_realm(self, realm_id: t.Union[Realm, uuid.UUID, str]) -> Realm | None:
        return self._get_single_resource(Realm, realm_id, "realms")

    def update_realm(
        self, realm_id: Realm | str | uuid.UUID, name: str = None, display_name: str = None, description: str = None
    ) -> Realm:
        return self._update_resource(
            Realm,
            realm_id,
            UpdateRealm(
                name=name,
                display_name=display_name,
                description=description,
            ),
            "realms",
        )

    def create_robot(
        self, name: str, realm_id: t.Union[Realm, str, uuid.UUID], secret: str, display_name: str = None
    ) -> Robot:
        return self._create_resource(
            Robot,
            CreateRobot(name=name, display_name=display_name, realm_id=str(obtain_uuid_from(realm_id)), secret=secret),
            "robots",
        )

    def delete_robot(self, robot_id: t.Union[Robot, str, uuid.UUID]):
        self._delete_resource(robot_id, "robots")

    def get_robot(self, robot_id: t.Union[Robot, str, uuid.UUID]) -> Robot | None:
        return self._get_single_resource(Robot, robot_id, "robots")

    def update_robot(
        self,
        robot_id: t.Union[Robot, str, uuid.UUID],
        name: str = None,
        display_name: str = None,
        realm_id: t.Union[Realm, str, uuid.UUID] = None,
        secret: str = None,
    ) -> Robot:
        return self._update_resource(
            Robot,
            robot_id,
            UpdateRobot(
                name=name,
                display_name=display_name,
                realm_id=str(obtain_uuid_from(realm_id)) if realm_id else None,
                secret=secret,
            ),
            "robots",
        )
