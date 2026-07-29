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
    ResourceListResult,
    AuthParam,
    BaseKwargs,
)
from flame_hub._defaults import DEFAULT_AUTH_BASE_URL


class CreateRealm(BaseModel):
    name: str
    displayName: str | None
    description: str | None


class UpdateRealm(BaseModel):
    name: str | UNSET_T = UNSET
    displayName: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET


class Realm(CreateRealm):
    id: uuid.UUID
    builtIn: bool
    createdAt: datetime
    updatedAt: datetime


class CreateUser(BaseModel):
    name: str
    displayName: str | None
    email: t.Annotated[EmailStr, IsOptionalField] = None
    active: bool
    nameLocked: bool
    firstName: str | None
    lastName: str | None


class User(CreateUser):
    id: uuid.UUID
    avatar: str | None
    cover: str | None
    realmId: uuid.UUID
    realm: t.Annotated[Realm, IsIncludable] = None
    createdAt: datetime
    updatedAt: datetime


class UpdateUser(BaseModel):
    name: str | UNSET_T = UNSET
    displayName: str | UNSET_T = UNSET
    email: str | None | UNSET_T = UNSET
    active: bool | UNSET_T = UNSET
    nameLocked: bool | UNSET_T = UNSET
    firstName: str | None | UNSET_T = UNSET
    lastName: str | None | UNSET_T = UNSET
    password: str | None | UNSET_T = UNSET


class CreatePermission(BaseModel):
    name: str
    displayName: str | None
    description: str | None
    realmId: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]
    policyId: t.Annotated[uuid.UUID | None, Field(), WrapValidator(uuid_validator)]


class Permission(CreatePermission):
    id: uuid.UUID
    builtIn: bool
    clientId: uuid.UUID | None
    createdAt: datetime
    updatedAt: datetime
    realm: t.Annotated[Realm | None, IsIncludable] = None


class UpdatePermission(BaseModel):
    name: str | UNSET_T = UNSET
    displayName: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET
    realmId: t.Annotated[uuid.UUID | None | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET
    policyId: t.Annotated[uuid.UUID | None | UNSET_T, Field(), WrapValidator(uuid_validator)] = UNSET


class CreateRole(BaseModel):
    name: str
    displayName: str | None
    description: str | None


class Role(CreateRole):
    id: uuid.UUID
    target: str | None
    realmId: uuid.UUID | None
    createdAt: datetime
    updatedAt: datetime
    realm: t.Annotated[Realm | None, IsIncludable] = None


class UpdateRole(BaseModel):
    name: str | UNSET_T = UNSET
    displayName: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET


class CreateRolePermission(BaseModel):
    roleId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    permissionId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class RolePermission(CreateRolePermission):
    id: uuid.UUID
    roleRealmId: uuid.UUID | None
    permissionRealmId: uuid.UUID | None
    policyId: uuid.UUID | None
    createdAt: datetime
    updatedAt: datetime
    role: t.Annotated[Role, IsIncludable] = None
    roleRealm: t.Annotated[Realm | None, IsIncludable] = None
    permission: t.Annotated[Permission, IsIncludable] = None
    permissionRealm: t.Annotated[Realm | None, IsIncludable] = None


class CreateUserPermission(BaseModel):
    userId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    permissionId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class UserPermission(CreateUserPermission):
    id: uuid.UUID
    userRealmId: uuid.UUID | None
    permissionRealmId: uuid.UUID | None
    policyId: uuid.UUID | None
    createdAt: datetime
    updatedAt: datetime
    permission: t.Annotated[Permission, IsIncludable] = None
    user: t.Annotated[User, IsIncludable] = None
    permissionRealm: t.Annotated[Realm | None, IsIncludable] = None
    userRealm: t.Annotated[Realm | None, IsIncludable] = None


class CreateUserRole(BaseModel):
    userId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]
    roleId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class UserRole(CreateUserRole):
    id: uuid.UUID
    userRealmId: uuid.UUID | None
    roleRealmId: uuid.UUID | None
    createdAt: datetime
    updatedAt: datetime
    user: t.Annotated[User, IsIncludable] = None
    role: t.Annotated[Role, IsIncludable] = None
    userRealm: t.Annotated[Realm | None, IsIncludable] = None
    roleRealm: t.Annotated[Realm | None, IsIncludable] = None


ClientAuthMethod = t.Literal["none", "secret", "tls"]
ClientTokenBindingMethod = t.Literal["none", "tls"]


class CreateClient(BaseModel):
    name: str
    secret: str | None
    displayName: str | None
    description: str | None
    redirectUri: str | None
    active: bool
    isConfidential: bool
    secretHashed: bool
    grantTypes: str | None
    authMethod: ClientAuthMethod
    tokenBindingMethod: ClientTokenBindingMethod
    realmId: t.Annotated[uuid.UUID, Field(), WrapValidator(uuid_validator)]


class Client(BaseModel):
    id: uuid.UUID
    name: str
    builtIn: bool
    displayName: str | None
    description: str | None
    redirectUri: str | None
    active: bool
    secretHashed: bool
    grantTypes: str | None
    secretEncrypted: bool
    scope: str | None
    baseUrl: str | None
    rootUrl: str | None
    authMethod: ClientAuthMethod
    tokenBindingMethod: ClientTokenBindingMethod
    createdAt: datetime
    updatedAt: datetime
    realmId: uuid.UUID
    realm: t.Annotated[Realm, IsIncludable] = None


class UpdateClient(BaseModel):
    name: str | UNSET_T = UNSET
    secret: str | None | UNSET_T = UNSET
    displayName: str | None | UNSET_T = UNSET
    description: str | None | UNSET_T = UNSET
    redirectUri: str | None | UNSET_T = UNSET
    active: bool | UNSET_T = UNSET
    isConfidential: bool | UNSET_T = UNSET
    secretHashed: bool | UNSET_T = UNSET
    grantTypes: str | None | UNSET_T = UNSET
    authMethod: ClientAuthMethod | UNSET_T = UNSET
    tokenBindingMethod: ClientTokenBindingMethod | UNSET_T = UNSET


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

    def _unwrap_single_resource(self, body: t.Any) -> t.Any:
        """Extract the resource object from authup's single-resource envelope.

        Since ``1.0.0-beta.57`` authup responds to single-resource requests with :python:`{"data": ..., "meta": ...}`
        instead of the resource object itself, mirroring the envelope that list responses have always used. ``meta``
        holds response-scoped extras such as the queryable schema of the endpoint and is discarded.

        Raises
        ------
        :py:exc:`ValueError`
            If ``body`` does not carry a ``data`` property, which is the case for authup versions before
            ``1.0.0-beta.57``.

        See Also
        --------
        :py:meth:`.BaseClient._unwrap_single_resource`
        """
        if not isinstance(body, dict) or "data" not in body:
            raise ValueError("response body is not wrapped in a data property, authup 1.0.0-beta.57 or newer required")

        return body["data"]

    def get_realms(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Realm]:
        return self._get_all_resources(Realm, "realms", **params)

    def find_realms(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Realm]:
        return self._find_all_resources(Realm, "realms", **params)

    def create_realm(
        self,
        name: str,
        displayName: str | None = None,
        description: str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> Realm:
        return self._create_resource(
            Realm,
            CreateRealm(
                name=name,
                displayName=displayName,
                description=description,
            ),
            "realms",
            **params,
        )

    def delete_realm(self, realmId: Realm | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("realms", realmId, **params)

    def get_realm(self, realmId: Realm | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Realm | None:
        return self._get_single_resource(Realm, "realms", realmId, **params)

    def update_realm(
        self,
        realmId: Realm | str | uuid.UUID,
        name: str | UNSET_T = UNSET,
        displayName: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Realm:
        return self._update_resource(
            Realm,
            UpdateRealm(
                name=name,
                displayName=displayName,
                description=description,
            ),
            "realms",
            realmId,
            **params,
        )

    def create_permission(
        self,
        name: str,
        displayName: str | None = None,
        description: str | None = None,
        realmId: Realm | uuid.UUID | str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> Permission:
        return self._create_resource(
            Permission,
            CreatePermission(
                name=name,
                displayName=displayName,
                description=description,
                realmId=realmId,
                policyId=None,  # TODO: add policies when hub implements them
            ),
            "permissions",
            **params,
        )

    def get_permission(
        self, permissionId: Permission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> Permission | None:
        return self._get_single_resource(
            Permission, "permissions", permissionId, include=get_includable_names(Permission), **params
        )

    def delete_permission(self, permissionId: Permission | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("permissions", permissionId, **params)

    def update_permission(
        self,
        permissionId: Permission | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        displayName: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        realmId: Realm | uuid.UUID | str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Permission:
        return self._update_resource(
            Permission,
            UpdatePermission(name=name, displayName=displayName, description=description, realmId=realmId),
            "permissions",
            permissionId,
            **params,
        )

    def get_permissions(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Permission]:
        return self._get_all_resources(Permission, "permissions", include=get_includable_names(Permission), **params)

    def find_permissions(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Permission]:
        return self._find_all_resources(Permission, "permissions", include=get_includable_names(Permission), **params)

    def create_role(
        self,
        name: str,
        displayName: str | None = None,
        description: str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> Role:
        return self._create_resource(
            Role,
            CreateRole(name=name, displayName=displayName, description=description),
            "roles",
            **params,
        )

    def get_role(self, roleId: Role | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Role | None:
        return self._get_single_resource(Role, "roles", roleId, include=get_includable_names(Role), **params)

    def delete_role(self, roleId: Role | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("roles", roleId, **params)

    def update_role(
        self,
        roleId: Role | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        displayName: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Role:
        return self._update_resource(
            Role,
            UpdateRole(name=name, displayName=displayName, description=description),
            "roles",
            roleId,
            **params,
        )

    def get_roles(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Role]:
        return self._get_all_resources(Role, "roles", include=get_includable_names(Role), **params)

    def find_roles(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Role]:
        return self._find_all_resources(Role, "roles", include=get_includable_names(Role), **params)

    def create_role_permission(
        self,
        roleId: Role | uuid.UUID | str,
        permissionId: Permission | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ) -> RolePermission:
        return self._create_resource(
            RolePermission,
            CreateRolePermission(roleId=roleId, permissionId=permissionId),
            "role-permissions",
            **params,
        )

    def get_role_permission(
        self, rolePermissionId: RolePermission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> RolePermission | None:
        return self._get_single_resource(
            RolePermission,
            "role-permissions",
            rolePermissionId,
            include=get_includable_names(RolePermission),
            **params,
        )

    def delete_role_permission(
        self,
        rolePermissionId: RolePermission | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._delete_resource("role-permissions", rolePermissionId, **params)

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
        displayName: str | None = None,
        active: bool = True,
        nameLocked: bool = False,
        firstName: str | None = None,
        lastName: str | None = None,
        **params: te.Unpack[BaseKwargs],
    ) -> User:
        return self._create_resource(
            User,
            CreateUser(
                name=name,
                displayName=displayName,
                email=email,
                active=active,
                nameLocked=nameLocked,
                firstName=firstName,
                lastName=lastName,
            ),
            "users",
            **params,
        )

    def get_user(self, userId: User | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> User | None:
        return self._get_single_resource(User, "users", userId, include=get_includable_names(User), **params)

    def delete_user(self, userId: User | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("users", userId, **params)

    def update_user(
        self,
        userId: User | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        displayName: str | UNSET_T = UNSET,
        email: str | None | UNSET_T = UNSET,
        active: bool | UNSET_T = UNSET,
        nameLocked: bool | UNSET_T = UNSET,
        firstName: str | None | UNSET_T = UNSET,
        lastName: str | None | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> User:
        return self._update_resource(
            User,
            UpdateUser(
                name=name,
                displayName=displayName,
                email=email,
                active=active,
                nameLocked=nameLocked,
                firstName=firstName,
                lastName=lastName,
            ),
            "users",
            userId,
            **params,
        )

    def get_users(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[User]:
        return self._get_all_resources(User, "users", include=get_includable_names(User), **params)

    def find_users(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[User]:
        return self._find_all_resources(User, "users", include=get_includable_names(User), **params)

    def create_user_permission(
        self,
        userId: User | uuid.UUID | str,
        permissionId: Permission | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ) -> UserPermission:
        return self._create_resource(
            UserPermission,
            CreateUserPermission(userId=userId, permissionId=permissionId),
            "user-permissions",
            **params,
        )

    def get_user_permission(
        self, userPermissionId: UserPermission | uuid.UUID | str, **params: te.Unpack[GetKwargs]
    ) -> UserPermission | None:
        return self._get_single_resource(
            UserPermission,
            "user-permissions",
            userPermissionId,
            include=get_includable_names(UserPermission),
            **params,
        )

    def delete_user_permission(
        self,
        userPermissionId: UserPermission | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ):
        self._delete_resource("user-permissions", userPermissionId, **params)

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
        userId: User | uuid.UUID | str,
        roleId: Role | uuid.UUID | str,
        **params: te.Unpack[BaseKwargs],
    ) -> UserRole:
        return self._create_resource(
            UserRole,
            CreateUserRole(userId=userId, roleId=roleId),
            "user-roles",
            **params,
        )

    def get_user_role(self, userRoleId: UserRole | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> UserRole | None:
        return self._get_single_resource(
            UserRole, "user-roles", userRoleId, include=get_includable_names(UserRole), **params
        )

    def delete_user_role(self, userRoleId: UserRole | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("user-roles", userRoleId, **params)

    def get_user_roles(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[UserRole]:
        return self._get_all_resources(UserRole, "user-roles", include=get_includable_names(UserRole), **params)

    def find_user_roles(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[UserRole]:
        return self._find_all_resources(UserRole, "user-roles", include=get_includable_names(UserRole), **params)

    def create_client(
        self,
        name: str,
        realmId: Realm | str | uuid.UUID,
        secret: str | None = None,
        displayName: str | None = None,
        description: str | None = None,
        redirectUri: str | None = None,
        active: bool = True,
        isConfidential: bool = True,
        secretHashed: bool = False,
        grantTypes: str | None = None,
        authMethod: ClientAuthMethod = "secret",
        tokenBindingMethod: ClientTokenBindingMethod = "none",
        **params: te.Unpack[BaseKwargs],
    ) -> Client:
        return self._create_resource(
            Client,
            CreateClient(
                name=name,
                realmId=realmId,
                secret=secret,
                displayName=displayName,
                description=description,
                redirectUri=redirectUri,
                active=active,
                isConfidential=isConfidential,
                secretHashed=secretHashed,
                grantTypes=grantTypes,
                authMethod=authMethod,
                tokenBindingMethod=tokenBindingMethod,
            ),
            "clients",
            **params,
        )

    def delete_client(self, clientId: Client | uuid.UUID | str, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("clients", clientId, **params)

    def get_client(self, clientId: Client | uuid.UUID | str, **params: te.Unpack[GetKwargs]) -> Client | None:
        return self._get_single_resource(Client, "clients", clientId, include=get_includable_names(Client), **params)

    def get_clients(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Client]:
        return self._get_all_resources(Client, "clients", include=get_includable_names(Client), **params)

    def find_clients(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Client]:
        return self._find_all_resources(Client, "clients", include=get_includable_names(Client), **params)

    def update_client(
        self,
        clientId: Client | uuid.UUID | str,
        name: str | UNSET_T = UNSET,
        secret: str | None | UNSET_T = UNSET,
        displayName: str | None | UNSET_T = UNSET,
        description: str | None | UNSET_T = UNSET,
        redirectUri: str | None | UNSET_T = UNSET,
        active: bool | UNSET_T = UNSET,
        isConfidential: bool | UNSET_T = UNSET,
        secretHashed: bool | UNSET_T = UNSET,
        grantTypes: str | None | UNSET_T = UNSET,
        authMethod: ClientAuthMethod | UNSET_T = UNSET,
        tokenBindingMethod: ClientTokenBindingMethod | UNSET_T = UNSET,
        **params: te.Unpack[BaseKwargs],
    ) -> Client:
        return self._update_resource(
            Client,
            UpdateClient(
                name=name,
                secret=secret,
                displayName=displayName,
                description=description,
                redirectUri=redirectUri,
                active=active,
                isConfidential=isConfidential,
                secretHashed=secretHashed,
                grantTypes=grantTypes,
                authMethod=authMethod,
                tokenBindingMethod=tokenBindingMethod,
            ),
            "clients",
            clientId,
            **params,
        )
