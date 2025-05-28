import uuid
from datetime import datetime
import typing as t

import typing_extensions as te
from pydantic import BaseModel, Field, WrapValidator

from flame_hub._base_client import (
    BaseClient,
    UpdateModel,
    _UNSET,
    FindAllKwargs,
    GetKwargs,
    ClientKwargs,
    uuid_validator,
    IsField,
)
from flame_hub._defaults import DEFAULT_AUTH_BASE_URL
from flame_hub._auth_flows import RobotAuth, PasswordAuth


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


class CreateUser(BaseModel):
    name: str
    display_name: str | None
    email: t.Annotated[str | None, IsField]
    active: bool
    name_locked: bool
    first_name: str | None
    last_name: str | None
    password: str | None


class User(BaseModel):
    id: uuid.UUID
    name: str
    active: bool
    name_locked: bool
    email: t.Annotated[str | None, IsField] = None
    display_name: str | None
    first_name: str | None
    last_name: str | None
    avatar: str | None
    cover: str | None
    realm_id: uuid.UUID
    realm: Realm = None
    created_at: datetime
    updated_at: datetime


class UpdateUser(UpdateModel):
    name: str | None = None
    display_name: str | None = None
    email: str | None = None
    active: bool | None = None
    name_locked: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None


class CreateRobot(BaseModel):
    name: str
    realm_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    secret: t.Annotated[str, IsField] = None
    display_name: str | None


class Robot(CreateRobot):
    id: uuid.UUID
    description: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
    user_id: uuid.UUID | None
    user: User | None = None
    realm: Realm = None


class UpdateRobot(UpdateModel):
    display_name: str | None = None
    name: str | None = None
    realm_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)] = None
    secret: str | None = None


class CreatePermission(BaseModel):
    name: str
    display_name: str | None
    description: str | None
    realm_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    policy_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]


class Permission(CreatePermission):
    id: uuid.UUID
    built_in: bool
    client_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    realm: Realm | None = None


class UpdatePermission(UpdateModel):
    name: str | None = None
    display_name: str | None = None
    description: str | None = None
    realm_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)] = None
    policy_id: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)] = None


class CreateRole(BaseModel):
    name: str
    display_name: str | None
    description: str | None


class Role(CreateRole):
    id: uuid.UUID
    target: str | None
    realm_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    realm: Realm | None = None


class UpdateRole(UpdateModel):
    name: str | None = None
    display_name: str | None = None
    description: str | None = None


class CreateRolePermission(BaseModel):
    role_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    permission_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class RolePermission(CreateRolePermission):
    id: uuid.UUID
    role_realm_id: uuid.UUID | None
    permission_realm_id: uuid.UUID | None
    policy_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    role: Role = None
    role_realm: Realm | None = None
    permission: Permission = None
    permission_realm: Realm | None = None


class CreateUserPermission(BaseModel):
    user_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    permission_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class UserPermission(CreateUserPermission):
    id: uuid.UUID
    user_realm_id: uuid.UUID | None
    permission_realm_id: uuid.UUID | None
    policy_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    permission: Permission = None
    user: User = None
    permission_realm: Realm | None = None
    user_realm: Realm | None = None


class CreateUserRole(BaseModel):
    user_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    role_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class UserRole(CreateUserRole):
    id: uuid.UUID
    user_realm_id: uuid.UUID | None
    role_realm_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    user: User = None
    role: Role = None
    user_realm: Realm | None = None
    role_realm: Realm | None = None


class CreateRobotPermission(BaseModel):
    robot_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    permission_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class RobotPermission(CreateRobotPermission):
    id: uuid.UUID
    robot_realm_id: uuid.UUID | None
    permission_realm_id: uuid.UUID | None
    policy_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    robot: Robot = None
    permission: Permission = None
    robot_realm: Realm | None = None
    permission_realm: Realm | None = None


class CreateRobotRole(BaseModel):
    robot_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    role_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class RobotRole(CreateRobotRole):
    id: uuid.UUID
    robot_realm_id: uuid.UUID | None
    role_realm_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    robot: Robot = None
    role: Role = None
    robot_realm: Realm | None = None
    role_realm: Realm | None = None


class AuthClient(BaseClient):
    """The client which implements all auth endpoints.

    This class passes its arguments through to :py:class:`.BaseClient`. Check the documentation of that class for
    further information. Note that ``base_url`` defaults :py:const:`~flame_hub._defaults.DEFAULT_AUTH_BASE_URL`.

    See Also
    --------
    :py:class:`.BaseClient`
    """

    def __init__(
        self,
        base_url=DEFAULT_AUTH_BASE_URL,
        auth: RobotAuth | PasswordAuth = None,
        **kwargs: te.Unpack[ClientKwargs],
    ):
        super().__init__(base_url, auth, **kwargs)

    def get_realms(self, **params: te.Unpack[GetKwargs]) -> list[Realm]:
        return self._get_all_resources(Realm, "realms", **params)

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

    def delete_realm(self, realm_id: Realm | uuid.UUID | str):
        self._delete_resource("realms", realm_id)

    def get_realm(self, realm_id: Realm | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Realm | None:
        return self._get_single_resource(Realm, "realms", realm_id, **params)

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
        self, name: str, realm_id: Realm | str | uuid.UUID, secret: str, display_name: str = None
    ) -> Robot:
        return self._create_resource(
            Robot,
            CreateRobot(name=name, display_name=display_name, realm_id=realm_id, secret=secret),
            "robots",
        )

    def delete_robot(self, robot_id: Robot | str | uuid.UUID):
        self._delete_resource("robots", robot_id)

    def get_robot(self, robot_id: Robot | str | uuid.UUID, **params: te.Unpack[GetKwargs]) -> Robot | None:
        return self._get_single_resource(Robot, "robots", robot_id, include=("realm", "user"), **params)

    def update_robot(
        self,
        robot_id: Robot | str | uuid.UUID,
        name: str = _UNSET,
        display_name: str = _UNSET,
        realm_id: Realm | str | uuid.UUID = _UNSET,
        secret: str = _UNSET,
    ) -> Robot:
        return self._update_resource(
            Robot,
            UpdateRobot(name=name, display_name=display_name, realm_id=realm_id, secret=secret),
            "robots",
            robot_id,
        )

    def get_robots(self, **params: te.Unpack[GetKwargs]) -> list[Robot]:
        return self._get_all_resources(Robot, "robots", include=("user", "realm"), **params)

    def find_robots(self, **params: te.Unpack[FindAllKwargs]) -> list[Robot]:
        return self._find_all_resources(Robot, "robots", include=("user", "realm"), **params)

    def create_permission(
        self,
        name: str,
        display_name: str = None,
        description: str = None,
        realm_id: Realm | uuid.UUID | str = None,
    ) -> Permission:
        return self._create_resource(
            Permission,
            CreatePermission(
                name=name,
                display_name=display_name,
                description=description,
                realm_id=realm_id,
                policy_id=None,  # TODO: add policies when hub implements them
            ),
            "permissions",
        )

    def get_permission(
        self, permission_id: Permission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> Permission | None:
        return self._get_single_resource(Permission, "permissions", permission_id, include="realm", **params)

    def delete_permission(self, permission_id: Permission | uuid.UUID | str):
        self._delete_resource("permissions", permission_id)

    def update_permission(
        self,
        permission_id: Permission | uuid.UUID | str,
        name: str = _UNSET,
        display_name: str = _UNSET,
        description: str = _UNSET,
        realm_id: Realm | uuid.UUID | str = _UNSET,
    ) -> Permission:
        return self._update_resource(
            Permission,
            UpdatePermission(name=name, display_name=display_name, description=description, realm_id=realm_id),
            "permissions",
            permission_id,
        )

    def get_permissions(self, **params: te.Unpack[GetKwargs]) -> list[Permission]:
        return self._get_all_resources(Permission, "permissions", include="realm", **params)

    def find_permissions(self, **params: te.Unpack[FindAllKwargs]) -> list[Permission]:
        return self._find_all_resources(Permission, "permissions", include="realm", **params)

    def create_role(self, name: str, display_name: str = None, description: str = None) -> Role:
        return self._create_resource(
            Role,
            CreateRole(name=name, display_name=display_name, description=description),
            "roles",
        )

    def get_role(self, role_id: Role | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Role | None:
        return self._get_single_resource(Role, "roles", role_id, include="realm", **params)

    def delete_role(self, role_id: Role | uuid.UUID | str):
        self._delete_resource("roles", role_id)

    def update_role(
        self,
        role_id: Role | uuid.UUID | str,
        name: str = _UNSET,
        display_name: str = _UNSET,
        description: str = _UNSET,
    ) -> Role:
        return self._update_resource(
            Role,
            UpdateRole(name=name, display_name=display_name, description=description),
            "roles",
            role_id,
        )

    def get_roles(self, **params: te.Unpack[GetKwargs]) -> list[Role]:
        return self._get_all_resources(Role, "roles", include="realm", **params)

    def find_roles(self, **params: te.Unpack[FindAllKwargs]) -> list[Role]:
        return self._find_all_resources(Role, "roles", include="realm", **params)

    def create_role_permission(
        self, role_id: Role | uuid.UUID | str, permission_id: Permission | uuid.UUID | str
    ) -> RolePermission:
        return self._create_resource(
            RolePermission,
            CreateRolePermission(role_id=role_id, permission_id=permission_id),
            "role-permissions",
        )

    def get_role_permission(
        self, role_permission_id: RolePermission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> RolePermission | None:
        return self._get_single_resource(
            RolePermission,
            "role-permissions",
            role_permission_id,
            include=("role", "role_realm", "permission", "permission_realm"),
            **params,
        )

    def delete_role_permission(self, role_permission_id: RolePermission | uuid.UUID | str):
        self._delete_resource("role-permissions", role_permission_id)

    def get_role_permissions(self, **params: te.Unpack[GetKwargs]) -> list[RolePermission]:
        return self._get_all_resources(
            RolePermission,
            "role-permissions",
            include=("role", "role_realm", "permission", "permission_realm"),
            **params,
        )

    def find_role_permissions(self, **params: te.Unpack[FindAllKwargs]) -> list[RolePermission]:
        return self._find_all_resources(
            RolePermission,
            "role-permissions",
            include=("role", "role_realm", "permission", "permission_realm"),
            **params,
        )

    def create_user(
        self,
        name: str,
        display_name: str = None,
        email: str = None,
        active: bool = True,
        name_locked: bool = True,
        first_name: str = None,
        last_name: str = None,
        password: str = None,
    ) -> User:
        return self._create_resource(
            User,
            CreateUser(
                name=name,
                display_name=display_name,
                email=email,
                active=active,
                name_locked=name_locked,
                first_name=first_name,
                last_name=last_name,
                password=password,
            ),
            "users",
        )

    def get_user(self, user_id: User | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> User | None:
        return self._get_single_resource(User, "users", user_id, include="realm", **params)

    def delete_user(self, user_id: User | uuid.UUID | str):
        self._delete_resource("users", user_id)

    def update_user(
        self,
        user_id: User | uuid.UUID | str,
        name: str = _UNSET,
        display_name: str = _UNSET,
        email: str = _UNSET,
        active: bool = _UNSET,
        name_locked: bool = _UNSET,
        first_name: str = _UNSET,
        last_name: str = _UNSET,
        password: str = _UNSET,
    ) -> User:
        return self._update_resource(
            User,
            UpdateUser(
                name=name,
                display_name=display_name,
                email=email,
                active=active,
                name_locked=name_locked,
                first_name=first_name,
                last_name=last_name,
                password=password,
            ),
            "users",
            user_id,
        )

    def get_users(self, **params: te.Unpack[GetKwargs]) -> list[User]:
        return self._get_all_resources(User, "users", include="realm", **params)

    def find_users(self, **params: te.Unpack[FindAllKwargs]) -> list[User]:
        return self._find_all_resources(User, "users", include="realm", **params)

    def create_user_permission(
        self,
        user_id: User | uuid.UUID | str,
        permission_id: Permission | uuid.UUID | str,
    ) -> UserPermission:
        return self._create_resource(
            UserPermission,
            CreateUserPermission(user_id=user_id, permission_id=permission_id),
            "user-permissions",
        )

    def get_user_permission(
        self, user_permission_id: UserPermission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> UserPermission | None:
        return self._get_single_resource(
            UserPermission,
            "user-permissions",
            user_permission_id,
            include=("user", "permission", "user_realm", "permission_realm"),
            **params,
        )

    def delete_user_permission(self, user_permission_id: UserPermission | uuid.UUID | str):
        self._delete_resource("user-permissions", user_permission_id)

    def get_user_permissions(self, **params: te.Unpack[GetKwargs]) -> list[UserPermission]:
        return self._get_all_resources(
            UserPermission,
            "user-permissions",
            include=("user", "permission", "user_realm", "permission_realm"),
            **params,
        )

    def find_user_permissions(self, **params: te.Unpack[FindAllKwargs]) -> list[UserPermission]:
        return self._find_all_resources(
            UserPermission,
            "user-permissions",
            include=("user", "permission", "user_realm", "permission_realm"),
            **params,
        )

    def create_user_role(self, user_id: User | uuid.UUID | str, role_id: Role | uuid.UUID | str) -> UserRole:
        return self._create_resource(
            UserRole,
            CreateUserRole(user_id=user_id, role_id=role_id),
            "user-roles",
        )

    def get_user_role(
        self, user_role_id: UserRole | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> UserRole | None:
        return self._get_single_resource(
            UserRole, "user-roles", user_role_id, include=("user", "role", "user_realm", "role_realm"), **params
        )

    def delete_user_role(self, user_role_id: UserRole | uuid.UUID | str):
        self._delete_resource("user-roles", user_role_id)

    def get_user_roles(self, **params: te.Unpack[GetKwargs]) -> list[UserRole]:
        return self._get_all_resources(
            UserRole, "user-roles", include=("user", "role", "user_realm", "role_realm"), **params
        )

    def find_user_roles(self, **params: te.Unpack[FindAllKwargs]) -> list[UserRole]:
        return self._find_all_resources(
            UserRole, "user-roles", include=("user", "role", "user_realm", "role_realm"), **params
        )

    def create_robot_permission(
        self, robot_id: Robot | uuid.UUID | str, permission_id: Permission | uuid.UUID | str
    ) -> RobotPermission:
        return self._create_resource(
            RobotPermission,
            CreateRobotPermission(robot_id=robot_id, permission_id=permission_id),
            "robot-permissions",
        )

    def get_robot_permission(
        self, robot_permission_id: RobotPermission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> RobotPermission | None:
        return self._get_single_resource(
            RobotPermission,
            "robot-permissions",
            robot_permission_id,
            include=("robot", "permission", "robot_realm", "permission_realm"),
            **params,
        )

    def delete_robot_permission(self, robot_permission_id: RobotPermission | uuid.UUID | str):
        self._delete_resource("robot-permissions", robot_permission_id)

    def get_robot_permissions(self, **params: te.Unpack[GetKwargs]) -> list[RobotPermission]:
        return self._get_all_resources(
            RobotPermission,
            "robot-permissions",
            include=("robot", "permission", "robot_realm", "permission_realm"),
            **params,
        )

    def find_robot_permissions(self, **params: te.Unpack[FindAllKwargs]) -> list[RobotPermission]:
        return self._find_all_resources(
            RobotPermission,
            "robot-permissions",
            include=("robot", "permission", "robot_realm", "permission_realm"),
            **params,
        )

    def create_robot_role(self, robot_id: Robot | uuid.UUID | str, role_id: Role | uuid.UUID | str) -> RobotRole:
        return self._create_resource(
            RobotRole,
            CreateRobotRole(robot_id=robot_id, role_id=role_id),
            "robot-roles",
        )

    def get_robot_role(
        self, robot_role_id: RobotRole | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> RobotRole | None:
        return self._get_single_resource(
            RobotRole, "robot-roles", robot_role_id, include=("robot", "role", "robot_realm", "role_realm"), **params
        )

    def delete_robot_role(self, robot_role_id: RobotRole | uuid.UUID | str):
        self._delete_resource("robot-roles", robot_role_id)

    def get_robot_roles(self, **params: te.Unpack[GetKwargs]) -> list[RobotRole]:
        return self._get_all_resources(
            RobotRole, "robot-roles", include=("robot", "role", "robot_realm", "role_realm"), **params
        )

    def find_robot_roles(self, **params: te.Unpack[FindAllKwargs]) -> list[RobotRole]:
        return self._find_all_resources(
            RobotRole, "robot-roles", include=("robot", "role", "robot_realm", "role_realm"), **params
        )
