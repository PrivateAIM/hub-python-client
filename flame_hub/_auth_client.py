import uuid
from datetime import datetime
import typing as t

import typing_extensions as te
from pydantic import Field, WrapValidator, EmailStr

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
    ResourceListResult,
    AuthParam,
    BaseKwargs,
    ConfigBaseModel,
    SingleResourceResult,
)
from flame_hub._defaults import DEFAULT_AUTH_BASE_URL


class AuthBaseModel(ConfigBaseModel):
    pass


class CreateRealm(AuthBaseModel):
    name: str
    display_name: str | None
    description: str | None


class UpdateRealm(AuthBaseModel):
    name: str | UNSET_T = UNSET
    display_name: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET


class Realm(CreateRealm):
    id: uuid.UUID
    built_in: bool
    created_at: datetime
    updated_at: datetime


class CreateUser(AuthBaseModel):
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


class UpdateUser(AuthBaseModel):
    name: str | UNSET_T = UNSET
    display_name: str | UNSET_T = UNSET
    email: str | None | UNSET_T = UNSET
    active: bool | UNSET_T = UNSET
    name_locked: bool | UNSET_T = UNSET
    first_name: str | None | UNSET_T = UNSET
    last_name: str | None | UNSET_T = UNSET
    password: str | None | UNSET_T = UNSET


class CreatePermission(AuthBaseModel):
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


class UpdatePermission(AuthBaseModel):
    name: str | UNSET_T = UNSET
    display_name: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET
    realm_id: t.Annotated[uuid.UUID | None | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET
    policy_id: t.Annotated[uuid.UUID | None | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET


class CreateRole(AuthBaseModel):
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


class UpdateRole(AuthBaseModel):
    name: str | UNSET_T = UNSET
    display_name: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET


class CreateRolePermission(AuthBaseModel):
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


class CreateUserPermission(AuthBaseModel):
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


class CreateUserRole(AuthBaseModel):
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


ClientAuthMethod = t.Literal["none", "secret", "tls"]
ClientTokenBindingMethod = t.Literal["none", "tls"]


class CreateClient(AuthBaseModel):
    name: str
    secret: str | None
    display_name: str | None
    description: str | None
    redirect_uri: str | None
    active: bool
    is_confidential: bool
    secret_hashed: bool
    grant_types: str | None
    auth_method: ClientAuthMethod
    token_binding_method: ClientTokenBindingMethod
    realm_id: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class Client(AuthBaseModel):
    id: uuid.UUID
    name: str
    built_in: bool
    display_name: str | None
    description: str | None
    redirect_uri: str | None
    active: bool
    secret_hashed: bool
    grant_types: str | None
    secret_encrypted: bool
    scope: str | None
    base_url: str | None
    root_url: str | None
    auth_method: ClientAuthMethod
    token_binding_method: ClientTokenBindingMethod
    created_at: datetime
    updated_at: datetime
    realm_id: uuid.UUID
    realm: t.Annotated[Realm, IsIncludable] = None


class UpdateClient(AuthBaseModel):
    name: str | UNSET_T = UNSET
    secret: str | None | UNSET_T = UNSET
    display_name: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET
    redirect_uri: str | None | UNSET_T = UNSET
    active: bool | UNSET_T = UNSET
    is_confidential: bool | UNSET_T = UNSET
    secret_hashed: bool | UNSET_T = UNSET
    grant_types: str | None | UNSET_T = UNSET
    auth_method: ClientAuthMethod | UNSET_T = UNSET
    token_binding_method: ClientTokenBindingMethod | UNSET_T = UNSET


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
        auth: AuthParam = None,
        **kwargs: te.Unpack[ClientKwargs],
    ):
        super().__init__(base_url, auth, **kwargs)

    def get_realms(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Realm]:
        return self._get_all_resources(Realm, "realms", **params)

    def find_realms(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Realm]:
        return self._find_all_resources(Realm, "realms", **params)

    def create_realm(
        self,
        name: str,
        display_name: str | None = None,
        description: str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> Realm:
        return self._create_resource(
            Realm,
            CreateRealm(
                name=name,
                display_name=display_name,
                description=description,
            ),
            "realms",
            **params,
        )

    def delete_realm(self, realm_id: Realm | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("realms", realm_id, **params)

    def get_realm(
        self,
        realm_id: Realm | uuid.UUID | str,
        **params: te.Unpack[GetKwargs],
    ) -> SingleResourceResult[Realm]:
        return self._get_single_resource(Realm, "realms", realm_id, **params)

    def update_realm(
        self,
        realm_id: Realm | str | uuid.UUID,
        name: str | UNSET_T = UNSET,
        display_name: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
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
            **params,
        )

    def create_permission(
        self,
        name: str,
        display_name: str | None = None,
        description: str | None = None,
        realm_id: Realm | uuid.UUID | str | None = None,
        **params: te.Unpack[BaseKwargs],
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
            **params,
        )

    def get_permission(
        self, permission_id: Permission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> SingleResourceResult[Permission]:
        return self._get_single_resource(
            Permission, "permissions", permission_id, include=get_includable_names(Permission), **params
        )

    def delete_permission(self, permission_id: Permission | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("permissions", permission_id, **params)

    def update_permission(
        self,
        permission_id: Permission | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        display_name: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        realm_id: Realm | uuid.UUID | str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Permission:
        return self._update_resource(
            Permission,
            UpdatePermission(name=name, display_name=display_name, description=description, realm_id=realm_id),
            "permissions",
            permission_id,
            **params,
        )

    def get_permissions(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Permission]:
        return self._get_all_resources(Permission, "permissions", include=get_includable_names(Permission), **params)

    def find_permissions(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Permission]:
        return self._find_all_resources(Permission, "permissions", include=get_includable_names(Permission), **params)

    def create_role(
        self,
        name: str,
        display_name: str | None = None,
        description: str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> Role:
        return self._create_resource(
            Role,
            CreateRole(name=name, display_name=display_name, description=description),
            "roles",
            **params,
        )

    def get_role(self, role_id: Role | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> SingleResourceResult[Role]:
        return self._get_single_resource(Role, "roles", role_id, include=get_includable_names(Role), **params)

    def delete_role(self, role_id: Role | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("roles", role_id, **params)

    def update_role(
        self,
        role_id: Role | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        display_name: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Role:
        return self._update_resource(
            Role,
            UpdateRole(name=name, display_name=display_name, description=description),
            "roles",
            role_id,
            **params,
        )

    def get_roles(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Role]:
        return self._get_all_resources(Role, "roles", include=get_includable_names(Role), **params)

    def find_roles(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Role]:
        return self._find_all_resources(Role, "roles", include=get_includable_names(Role), **params)

    def create_role_permission(
        self,
        role_id: Role | uuid.UUID | str,
        permission_id: Permission | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ) -> RolePermission:
        return self._create_resource(
            RolePermission,
            CreateRolePermission(role_id=role_id, permission_id=permission_id),
            "role-permissions",
            **params,
        )

    def get_role_permission(
        self, role_permission_id: RolePermission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> SingleResourceResult[RolePermission]:
        return self._get_single_resource(
            RolePermission,
            "role-permissions",
            role_permission_id,
            include=get_includable_names(RolePermission),
            **params,
        )

    def delete_role_permission(
        self,
        role_permission_id: RolePermission | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._delete_resource("role-permissions", role_permission_id, **params)

    def get_role_permissions(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[RolePermission]:
        return self._get_all_resources(
            RolePermission,
            "role-permissions",
            include=get_includable_names(RolePermission),
            **params,
        )

    def find_role_permissions(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[RolePermission]:
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
        display_name: str | None = None,
        active: bool = True,
        name_locked: bool = False,
        first_name: str | None = None,
        last_name: str | None = None,
        **params: te.Unpack[BaseKwargs],
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
            **params,
        )

    def get_user(self, user_id: User | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> SingleResourceResult[User]:
        return self._get_single_resource(User, "users", user_id, include=get_includable_names(User), **params)

    def delete_user(self, user_id: User | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("users", user_id, **params)

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
        **params: te.Unpack[BaseKwargs],
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
            **params,
        )

    def get_users(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[User]:
        return self._get_all_resources(User, "users", include=get_includable_names(User), **params)

    def find_users(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[User]:
        return self._find_all_resources(User, "users", include=get_includable_names(User), **params)

    def create_user_permission(
        self,
        user_id: User | uuid.UUID | str,
        permission_id: Permission | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ) -> UserPermission:
        return self._create_resource(
            UserPermission,
            CreateUserPermission(user_id=user_id, permission_id=permission_id),
            "user-permissions",
            **params,
        )

    def get_user_permission(
        self, user_permission_id: UserPermission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> SingleResourceResult[UserPermission]:
        return self._get_single_resource(
            UserPermission,
            "user-permissions",
            user_permission_id,
            include=get_includable_names(UserPermission),
            **params,
        )

    def delete_user_permission(
        self,
        user_permission_id: UserPermission | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._delete_resource("user-permissions", user_permission_id, **params)

    def get_user_permissions(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[UserPermission]:
        return self._get_all_resources(
            UserPermission,
            "user-permissions",
            include=get_includable_names(UserPermission),
            **params,
        )

    def find_user_permissions(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[UserPermission]:
        return self._find_all_resources(
            UserPermission,
            "user-permissions",
            include=get_includable_names(UserPermission),
            **params,
        )

    def create_user_role(
        self,
        user_id: User | uuid.UUID | str,
        role_id: Role | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ) -> UserRole:
        return self._create_resource(
            UserRole,
            CreateUserRole(user_id=user_id, role_id=role_id),
            "user-roles",
            **params,
        )

    def get_user_role(
        self, user_role_id: UserRole | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> SingleResourceResult[UserRole]:
        return self._get_single_resource(
            UserRole, "user-roles", user_role_id, include=get_includable_names(UserRole), **params
        )

    def delete_user_role(self, user_role_id: UserRole | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("user-roles", user_role_id, **params)

    def get_user_roles(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[UserRole]:
        return self._get_all_resources(UserRole, "user-roles", include=get_includable_names(UserRole), **params)

    def find_user_roles(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[UserRole]:
        return self._find_all_resources(UserRole, "user-roles", include=get_includable_names(UserRole), **params)

    def create_client(
        self,
        name: str,
        realm_id: Realm | str | uuid.UUID,
        secret: str | None = None,
        display_name: str | None = None,
        description: str | None = None,
        redirect_uri: str | None = None,
        active: bool = True,
        is_confidential: bool = True,
        secret_hashed: bool = False,
        grant_types: str | None = None,
        auth_method: ClientAuthMethod = "secret",
        token_binding_method: ClientTokenBindingMethod = "none",
        **params: te.Unpack[BaseKwargs],
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
                auth_method=auth_method,
                token_binding_method=token_binding_method,
            ),
            "clients",
            **params,
        )

    def delete_client(self, client_id: Client | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("clients", client_id, **params)

    def get_client(
        self,
        client_id: Client | uuid.UUID | str,
        **params: te.Unpack[GetKwargs],
    ) -> SingleResourceResult[Client]:
        return self._get_single_resource(Client, "clients", client_id, include=get_includable_names(Client), **params)

    def get_clients(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Client]:
        return self._get_all_resources(Client, "clients", include=get_includable_names(Client), **params)

    def find_clients(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Client]:
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
        auth_method: ClientAuthMethod | UNSET_T = UNSET,
        token_binding_method: ClientTokenBindingMethod | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
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
                auth_method=auth_method,
                token_binding_method=token_binding_method,
            ),
            "clients",
            client_id,
            **params,
        )
