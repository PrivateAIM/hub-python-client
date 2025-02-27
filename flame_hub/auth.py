__all__ = ["AuthClient"]

import typing as t
import uuid
from datetime import datetime

import httpx
import typing_extensions as te
from pydantic import BaseModel

from flame_hub.base_client import (
    BaseClient,
    obtain_uuid_from,
    UpdateModel,
    _UNSET,
    FindAllKwargs,
)
from flame_hub.defaults import DEFAULT_AUTH_BASE_URL
from flame_hub.flow import RobotAuth, PasswordAuth


class CreateRealm(BaseModel):
    name: str
    display_name: str | None
    description: str | None


class UpdateRealm(UpdateModel):
    name: str | None = None
    display_name: str | None = None
    description: str | None = None


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


class UpdateRobot(UpdateModel):
    display_name: str | None = None
    name: str | None = None
    realm_id: uuid.UUID | None = None
    secret: str | None = None


class AuthClient(BaseClient):
    def __init__(
        self,
        base_url=DEFAULT_AUTH_BASE_URL,
        client: httpx.Client = None,
        auth: t.Union[RobotAuth, PasswordAuth] = None,
    ):
        super().__init__(base_url, client, auth)

    def get_realms(self) -> list[Realm]:
        return self._get_all_resources(Realm, "realms")

    def find_realms(self, **params: te.Unpack[FindAllKwargs]) -> list[Realm]:
        return self._find_all_resources(Realm, "realms", **params)

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
        self._delete_resource("realms", realm_id)

    def get_realm(self, realm_id: t.Union[Realm, uuid.UUID, str]) -> Realm | None:
        return self._get_single_resource(Realm, "realms", realm_id)

    def update_realm(
        self,
        realm_id: Realm | str | uuid.UUID,
        name: str = _UNSET,
        display_name: str = _UNSET,
        description: str = _UNSET,
    ) -> Realm:
        return self._update_resource(
            Realm,
            UpdateRealm(
                name=name,
                display_name=display_name,
                description=description,
            ),
            "realms",
            realm_id,
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
        self._delete_resource("robots", robot_id)

    def get_robot(self, robot_id: t.Union[Robot, str, uuid.UUID]) -> Robot | None:
        return self._get_single_resource(Robot, "robots", robot_id)

    def update_robot(
        self,
        robot_id: t.Union[Robot, str, uuid.UUID],
        name: str = _UNSET,
        display_name: str = _UNSET,
        realm_id: t.Union[Realm, str, uuid.UUID] = _UNSET,
        secret: str = _UNSET,
    ) -> Robot:
        if realm_id not in (None, _UNSET):
            realm_id = obtain_uuid_from(realm_id)

        return self._update_resource(
            Robot,
            UpdateRobot(
                name=name,
                display_name=display_name,
                realm_id=realm_id,
                secret=secret,
            ),
            "robots",
            robot_id,
        )
