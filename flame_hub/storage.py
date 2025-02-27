__all__ = ["StorageClient"]

import typing as t
import uuid
from datetime import datetime

import httpx
import typing_extensions as te
from pydantic import BaseModel

from flame_hub import PasswordAuth, RobotAuth
from flame_hub.base_client import BaseClient, ResourceList, obtain_uuid_from, FindAllKwargs, new_error_from_response
from flame_hub.defaults import DEFAULT_STORAGE_BASE_URL


class CreateBucket(BaseModel):
    name: str
    region: str | None


class Bucket(CreateBucket):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    actor_id: uuid.UUID
    actor_type: str
    realm_id: uuid.UUID | None


class BucketFile(BaseModel):
    id: uuid.UUID
    name: str
    path: str
    hash: str
    directory: str
    size: int | None
    created_at: datetime
    updated_at: datetime
    actor_type: str
    actor_id: uuid.UUID
    bucket_id: uuid.UUID


class UploadFile(te.TypedDict):
    file_name: str
    content: t.Union[bytes, t.IO[bytes], str]
    content_type: te.NotRequired[str]


def apply_upload_file_defaults(uf: UploadFile) -> UploadFile:
    if not hasattr(uf, "content_type") or uf["content_type"] is None:
        uf["content_type"] = "application/octet-stream"

    return uf


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
        self._delete_resource("buckets", bucket_id)

    def get_buckets(self) -> list[Bucket]:
        return self._get_all_resources(Bucket, "buckets")

    def find_buckets(self, **params: te.Unpack[FindAllKwargs]) -> list[Bucket]:
        return self._find_all_resources(Bucket, "buckets", **params)

    def get_bucket(self, bucket_id: t.Union[Bucket, str, uuid.UUID]) -> Bucket | None:
        return self._get_single_resource(Bucket, "buckets", bucket_id)

    def stream_bucket_tarball(self, bucket_id: t.Union[Bucket, str, uuid.UUID], chunk_size=1024):
        with self._client.stream("GET", f"buckets/{obtain_uuid_from(bucket_id)}/stream") as r:
            for b in r.iter_bytes(chunk_size=chunk_size):
                yield b

    def upload_to_bucket(
        self, bucket_id: t.Union[Bucket, str, uuid.UUID], *upload_file: UploadFile
    ) -> list[BucketFile]:
        upload_file_tpl = (apply_upload_file_defaults(uf) for uf in upload_file)
        upload_file_dict = {
            str(uuid.uuid4()): (uf["file_name"], uf["content"], uf["content_type"]) for uf in upload_file_tpl
        }

        r = self._client.post(
            f"buckets/{obtain_uuid_from(bucket_id)}/upload",
            files=upload_file_dict,
        )

        if r.status_code != httpx.codes.CREATED.value:
            raise new_error_from_response(r)

        return ResourceList[BucketFile](**r.json()).data

    def delete_bucket_file(self, bucket_file_id: t.Union[BucketFile, str, uuid.UUID]):
        self._delete_resource("bucket-files", bucket_file_id)

    def get_bucket_file(self, bucket_file_id: t.Union[BucketFile, str, uuid.UUID]) -> BucketFile | None:
        return self._get_single_resource(BucketFile, "bucket-files", bucket_file_id)

    def get_bucket_files(self) -> list[BucketFile]:
        return self._get_all_resources(BucketFile, "bucket-files")

    def find_bucket_files(self, **params: te.Unpack[FindAllKwargs]) -> list[BucketFile]:
        return self._find_all_resources(BucketFile, "bucket-files", **params)

    def stream_bucket_file(self, bucket_file_id: t.Union[BucketFile, str, uuid.UUID], chunk_size=1024):
        with self._client.stream("GET", f"bucket-files/{obtain_uuid_from(bucket_file_id)}/stream") as r:
            for b in r.iter_bytes(chunk_size=chunk_size):
                yield b
