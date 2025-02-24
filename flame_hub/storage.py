__all__ = ["StorageClient"]

import httpx

from flame_hub import PasswordAuth, RobotAuth
from flame_hub.base_client import BaseClient
from flame_hub.defaults import DEFAULT_STORAGE_BASE_URL

import typing as t


class StorageClient(BaseClient):
    def __init__(
        self,
        base_url: str = DEFAULT_STORAGE_BASE_URL,
        client: httpx.Client = None,
        auth: t.Union[PasswordAuth, RobotAuth] = None,
    ):
        super().__init__(base_url, client, auth)
