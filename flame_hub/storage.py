__all__ = ["StorageClient"]

import uuid
from datetime import datetime

import httpx
from pydantic import BaseModel

from flame_hub import PasswordAuth, RobotAuth
from flame_hub.base_client import BaseClient, ResourceList
from flame_hub.defaults import DEFAULT_STORAGE_BASE_URL

import typing as t


class CreateBucket(BaseModel):
    name: str
    region: str | None


class UpdateBucket(BaseModel):
    name: str | None
    region: str | None


class Bucket(CreateBucket):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    actor_id: uuid.UUID
    actor_type: str
    realm_id: uuid.UUID | None


class StorageClient(BaseClient):
    def __init__(
        self,
        base_url: str = DEFAULT_STORAGE_BASE_URL,
        client: httpx.Client = None,
        auth: t.Union[PasswordAuth, RobotAuth] = None,
    ):
        super().__init__(base_url, client, auth)

    def create_bucket(self, name: str, region: str = None) -> Bucket:
        return self._create_resource(Bucket, CreateBucket(name=name, region=region), "buckets")

    def delete_bucket(self, bucket_id: t.Union[Bucket, str, uuid.UUID]):
        self._delete_resource(bucket_id, "buckets")

    def get_buckets(self) -> ResourceList[Bucket]:
        return self._get_all_resources(Bucket, "buckets")

    def get_bucket(self, bucket_id: t.Union[Bucket, str, uuid.UUID]) -> Bucket | None:
        return self._get_single_resource(Bucket, bucket_id, "buckets")

    def update_bucket(self, bucket_id: t.Union[Bucket, str, uuid.UUID], name: str = None, region: str = None) -> Bucket:
        return self._update_resource(Bucket, bucket_id, UpdateBucket(name=name, region=region), "buckets")
