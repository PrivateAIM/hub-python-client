import uuid
from datetime import datetime
import typing as t

import typing_extensions as te
from pydantic import BaseModel, Field, WrapValidator, EmailStr

from flame_hub._base_client import (
    BaseClient,
    FindAllKwargs,
    GetKwargs,
    ClientKwargs,
    uuid_validator,
    IsOptionalField,
    IsIncludable,
    get_includable_names,
    UNSET,
    UNSET_T,
)
from flame_hub._defaults import DEFAULT_AUTH_BASE_URL
from flame_hub._auth_flows import RobotAuth, PasswordAuth


class CreateRealm(BaseModel):
    name: str
    display_name: str | None
    description: str | None


class UpdateRealm(BaseModel):
    name: str | UNSET_T = UNSET
    display_name: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET


class Realm(CreateRealm):
    id: uuid.UUID
    built_in: bool
    created_at: datetime
    updated_at: datetime


class CreateUser(BaseModel):
    name: str
    display_name: str | None
    email: t.Annotated[EmailStr, IsOptionalField] = None
    active: bool
    name_locked: bool
    first_name: str | None
    last_name: str | None


class User(CreateUser):
    id: uuid.UUID
    avatar: str | None
    cover: str | None
    realm_id: uuid.UUID
    realm: t.Annotated[Realm, IsIncludable] = None
    created_at: datetime
    updated_at: datetime


class UpdateUser(BaseModel):
    name: str | UNSET_T = UNSET
    display_name: str | UNSET_T = UNSET
    email: str | None | UNSET_T = UNSET
    active: bool | UNSET_T = UNSET
    name_locked: bool | UNSET_T = UNSET
    first_name: str | None | UNSET_T = UNSET
    last_name: str | None | UNSET_T = UNSET
    password: str | None | UNSET_T = UNSET


class CreateRobot(BaseModel):
    name: str
    realm_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    secret: t.Annotated[str, IsOptionalField] = None
    display_name: str | None


class Robot(CreateRobot):
    id: uuid.UUID
    description: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
    user_id: uuid.UUID | None
    user: t.Annotated[User | None, IsIncludable] = None
    realm: t.Annotated[Realm, IsIncludable] = None


class UpdateRobot(BaseModel):
    display_name: str | None | UNSET_T = UNSET
    name: str | UNSET_T = UNSET
    realm_id: t.Annotated[uuid.UUID | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET
    secret: str | UNSET_T = UNSET


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
    realm: t.Annotated[Realm | None, IsIncludable] = None


class UpdatePermission(BaseModel):
    name: str | UNSET_T = UNSET
    display_name: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET
    realm_id: t.Annotated[uuid.UUID | None | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET
    policy_id: t.Annotated[uuid.UUID | None | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET


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
    realm: t.Annotated[Realm | None, IsIncludable] = None


class UpdateRole(BaseModel):
    name: str | UNSET_T = UNSET
    display_name: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET


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
    role: t.Annotated[Role, IsIncludable] = None
    role_realm: t.Annotated[Realm | None, IsIncludable] = None
    permission: t.Annotated[Permission, IsIncludable] = None
    permission_realm: t.Annotated[Realm | None, IsIncludable] = None


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
    permission: t.Annotated[Permission, IsIncludable] = None
    user: t.Annotated[User, IsIncludable] = None
    permission_realm: t.Annotated[Realm | None, IsIncludable] = None
    user_realm: t.Annotated[Realm | None, IsIncludable] = None


class CreateUserRole(BaseModel):
    user_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    role_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class UserRole(CreateUserRole):
    id: uuid.UUID
    user_realm_id: uuid.UUID | None
    role_realm_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    user: t.Annotated[User, IsIncludable] = None
    role: t.Annotated[Role, IsIncludable] = None
    user_realm: t.Annotated[Realm | None, IsIncludable] = None
    role_realm: t.Annotated[Realm | None, IsIncludable] = None


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
    robot: t.Annotated[Robot, IsIncludable] = None
    permission: t.Annotated[Permission, IsIncludable] = None
    robot_realm: t.Annotated[Realm | None, IsIncludable] = None
    permission_realm: t.Annotated[Realm | None, IsIncludable] = None


class CreateRobotRole(BaseModel):
    robot_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    role_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class RobotRole(CreateRobotRole):
    id: uuid.UUID
    robot_realm_id: uuid.UUID | None
    role_realm_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    robot: t.Annotated[Robot, IsIncludable] = None
    role: t.Annotated[Role, IsIncludable] = None
    robot_realm: t.Annotated[Realm | None, IsIncludable] = None
    role_realm: t.Annotated[Realm | None, IsIncludable] = None


class CreateClient(BaseModel):
    name: str
    secret: t.Annotated[str | None, IsOptionalField] = None
    display_name: str | None
    description: str | None
    redirect_uri: str | None
    active: bool
    is_confidential: bool
    secret_hashed: bool
    grant_types: str | None
    realm_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class Client(CreateClient):
    id: uuid.UUID
    built_in: bool
    secret_encrypted: bool
    scope: str | None
    base_url: str | None
    root_url: str | None
    created_at: datetime
    updated_at: datetime
    realm: t.Annotated[Realm, IsIncludable] = None


class UpdateClient(BaseModel):
    name: str | UNSET_T = UNSET
    secret: str | None | UNSET_T = UNSET
    display_name: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET
    redirect_uri: str | None | UNSET_T = UNSET
    active: bool | UNSET_T = UNSET
    is_confidential: bool | UNSET_T = UNSET
    secret_hashed: bool | UNSET_T = UNSET
    grant_types: str | None | UNSET_T = UNSET


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
        name: str | UNSET_T = UNSET,
        display_name: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
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
        return self._get_single_resource(Robot, "robots", robot_id, include=get_includable_names(Robot), **params)

    def update_robot(
        self,
        robot_id: Robot | str | uuid.UUID,
        name: str | UNSET_T = UNSET,
        display_name: str | None | UNSET_T = UNSET,
        realm_id: Realm | str | uuid.UUID | UNSET_T = UNSET,
        secret: str | UNSET_T = UNSET,
    ) -> Robot:
        return self._update_resource(
            Robot,
            UpdateRobot(name=name, display_name=display_name, realm_id=realm_id, secret=secret),
            "robots",
            robot_id,
        )

    def get_robots(self, **params: te.Unpack[GetKwargs]) -> list[Robot]:
        return self._get_all_resources(Robot, "robots", include=get_includable_names(Robot), **params)

    def find_robots(self, **params: te.Unpack[FindAllKwargs]) -> list[Robot]:
        return self._find_all_resources(Robot, "robots", include=get_includable_names(Robot), **params)

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
        return self._get_single_resource(
            Permission, "permissions", permission_id, include=get_includable_names(Permission), **params
        )

    def delete_permission(self, permission_id: Permission | uuid.UUID | str):
        self._delete_resource("permissions", permission_id)

    def update_permission(
        self,
        permission_id: Permission | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        display_name: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        realm_id: Realm | uuid.UUID | str | None | UNSET_T = UNSET,
    ) -> Permission:
        return self._update_resource(
            Permission,
            UpdatePermission(name=name, display_name=display_name, description=description, realm_id=realm_id),
            "permissions",
            permission_id,
        )

    def get_permissions(self, **params: te.Unpack[GetKwargs]) -> list[Permission]:
        return self._get_all_resources(Permission, "permissions", include=get_includable_names(Permission), **params)

    def find_permissions(self, **params: te.Unpack[FindAllKwargs]) -> list[Permission]:
        return self._find_all_resources(Permission, "permissions", include=get_includable_names(Permission), **params)

    def create_role(self, name: str, display_name: str = None, description: str = None) -> Role:
        return self._create_resource(
            Role,
            CreateRole(name=name, display_name=display_name, description=description),
            "roles",
        )

    def get_role(self, role_id: Role | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Role | None:
        return self._get_single_resource(Role, "roles", role_id, include=get_includable_names(Role), **params)

    def delete_role(self, role_id: Role | uuid.UUID | str):
        self._delete_resource("roles", role_id)

    def update_role(
        self,
        role_id: Role | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        display_name: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
    ) -> Role:
        return self._update_resource(
            Role,
            UpdateRole(name=name, display_name=display_name, description=description),
            "roles",
            role_id,
        )

    def get_roles(self, **params: te.Unpack[GetKwargs]) -> list[Role]:
        return self._get_all_resources(Role, "roles", include=get_includable_names(Role), **params)

    def find_roles(self, **params: te.Unpack[FindAllKwargs]) -> list[Role]:
        return self._find_all_resources(Role, "roles", include=get_includable_names(Role), **params)

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
            include=get_includable_names(RolePermission),
            **params,
        )

    def delete_role_permission(self, role_permission_id: RolePermission | uuid.UUID | str):
        self._delete_resource("role-permissions", role_permission_id)

    def get_role_permissions(self, **params: te.Unpack[GetKwargs]) -> list[RolePermission]:
        return self._get_all_resources(
            RolePermission,
            "role-permissions",
            include=get_includable_names(RolePermission),
            **params,
        )

    def find_role_permissions(self, **params: te.Unpack[FindAllKwargs]) -> list[RolePermission]:
        return self._find_all_resources(
            RolePermission,
            "role-permissions",
            include=get_includable_names(RolePermission),
            **params,
        )

    def create_user(
        self,
        name: str,
        email: str,
        display_name: str = None,
        active: bool = True,
        name_locked: bool = True,
        first_name: str = None,
        last_name: str = None,
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
            ),
            "users",
        )

    def get_user(self, user_id: User | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> User | None:
        return self._get_single_resource(User, "users", user_id, include=get_includable_names(User), **params)

    def delete_user(self, user_id: User | uuid.UUID | str):
        self._delete_resource("users", user_id)

    def update_user(
        self,
        user_id: User | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        display_name: str | UNSET_T = UNSET,
        email: str | None | UNSET_T = UNSET,
        active: bool | UNSET_T = UNSET,
        name_locked: bool | UNSET_T = UNSET,
        first_name: str | None | UNSET_T = UNSET,
        last_name: str | None | UNSET_T = UNSET,
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
            ),
            "users",
            user_id,
        )

    def get_users(self, **params: te.Unpack[GetKwargs]) -> list[User]:
        return self._get_all_resources(User, "users", include=get_includable_names(User), **params)

    def find_users(self, **params: te.Unpack[FindAllKwargs]) -> list[User]:
        return self._find_all_resources(User, "users", include=get_includable_names(User), **params)

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
            include=get_includable_names(UserPermission),
            **params,
        )

    def delete_user_permission(self, user_permission_id: UserPermission | uuid.UUID | str):
        self._delete_resource("user-permissions", user_permission_id)

    def get_user_permissions(self, **params: te.Unpack[GetKwargs]) -> list[UserPermission]:
        return self._get_all_resources(
            UserPermission,
            "user-permissions",
            include=get_includable_names(UserPermission),
            **params,
        )

    def find_user_permissions(self, **params: te.Unpack[FindAllKwargs]) -> list[UserPermission]:
        return self._find_all_resources(
            UserPermission,
            "user-permissions",
            include=get_includable_names(UserPermission),
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
            UserRole, "user-roles", user_role_id, include=get_includable_names(UserRole), **params
        )

    def delete_user_role(self, user_role_id: UserRole | uuid.UUID | str):
        self._delete_resource("user-roles", user_role_id)

    def get_user_roles(self, **params: te.Unpack[GetKwargs]) -> list[UserRole]:
        return self._get_all_resources(UserRole, "user-roles", include=get_includable_names(UserRole), **params)

    def find_user_roles(self, **params: te.Unpack[FindAllKwargs]) -> list[UserRole]:
        return self._find_all_resources(UserRole, "user-roles", include=get_includable_names(UserRole), **params)

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
            include=get_includable_names(RobotPermission),
            **params,
        )

    def delete_robot_permission(self, robot_permission_id: RobotPermission | uuid.UUID | str):
        self._delete_resource("robot-permissions", robot_permission_id)

    def get_robot_permissions(self, **params: te.Unpack[GetKwargs]) -> list[RobotPermission]:
        return self._get_all_resources(
            RobotPermission,
            "robot-permissions",
            include=get_includable_names(RobotPermission),
            **params,
        )

    def find_robot_permissions(self, **params: te.Unpack[FindAllKwargs]) -> list[RobotPermission]:
        return self._find_all_resources(
            RobotPermission,
            "robot-permissions",
            include=get_includable_names(RobotPermission),
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
            RobotRole, "robot-roles", robot_role_id, include=get_includable_names(RobotRole), **params
        )

    def delete_robot_role(self, robot_role_id: RobotRole | uuid.UUID | str):
        self._delete_resource("robot-roles", robot_role_id)

    def get_robot_roles(self, **params: te.Unpack[GetKwargs]) -> list[RobotRole]:
        return self._get_all_resources(RobotRole, "robot-roles", include=get_includable_names(RobotRole), **params)

    def find_robot_roles(self, **params: te.Unpack[FindAllKwargs]) -> list[RobotRole]:
        return self._find_all_resources(RobotRole, "robot-roles", include=get_includable_names(RobotRole), **params)

    def create_client(
        self,
        name: str,
        realm_id: Realm | str | uuid.UUID,
        secret: str = None,
        display_name: str = None,
        description: str = None,
        redirect_uri: str = None,
        active: bool = True,
        is_confidential: bool = True,
        secret_hashed: bool = False,
        grant_types: str = None,
    ) -> Client:
        return self._create_resource(
            Client,
            CreateClient(
                name=name,
                realm_id=realm_id,
                secret=secret,
                display_name=display_name,
                description=description,
                redirect_uri=redirect_uri,
                active=active,
                is_confidential=is_confidential,
                secret_hashed=secret_hashed,
                grant_types=grant_types,
            ),
            "clients",
        )

    def delete_client(self, client_id: Client | uuid.UUID | str):
        self._delete_resource("clients", client_id)

    def get_client(self, client_id: Client | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Client | None:
        return self._get_single_resource(Client, "clients", client_id, include=get_includable_names(Client), **params)

    def get_clients(self, **params: te.Unpack[GetKwargs]) -> list[Client]:
        return self._get_all_resources(Client, "clients", include=get_includable_names(Client), **params)

    def find_clients(self, **params: te.Unpack[FindAllKwargs]) -> list[Client]:
        return self._find_all_resources(Client, "clients", include=get_includable_names(Client), **params)

    def update_client(
        self,
        client_id: Client | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        secret: str | None | UNSET_T = UNSET,
        display_name: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        redirect_uri: str | None | UNSET_T = UNSET,
        active: bool | UNSET_T = UNSET,
        is_confidential: bool | UNSET_T = UNSET,
        secret_hashed: bool | UNSET_T = UNSET,
        grant_types: str | None | UNSET_T = UNSET,
    ) -> Client:
        return self._update_resource(
            Client,
            UpdateClient(
                name=name,
                secret=secret,
                display_name=display_name,
                description=description,
                redirect_uri=redirect_uri,
                active=active,
                is_confidential=is_confidential,
                secret_hashed=secret_hashed,
                grant_types=grant_types,
            ),
            "clients",
            client_id,
        )
