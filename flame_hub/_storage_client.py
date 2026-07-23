import typing as t
import uuid
from datetime import datetime

import httpx2 as httpx
import typing_extensions as te
from pydantic import BaseModel

from flame_hub._base_client import (
    BaseClient,
    ResourceList,
    obtain_uuid_from,
    FindAllKwargs,
    GetKwargs,
    ClientKwargs,
    IsIncludable,
    get_includable_names,
    ResourceListResult,
    AuthParam,
    BaseKwargs,
)
from flame_hub._defaults import DEFAULT_STORAGE_BASE_URL


class CreateBucket(BaseModel):
    name: str
    region: str | None


class Bucket(CreateBucket):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    actor_id: uuid.UUID | None
    actor_type: str | None
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
    realm_id: uuid.UUID
    bucket_id: uuid.UUID
    bucket: t.Annotated[Bucket, IsIncludable] = None


class ReadableBinary(t.Protocol):
    def read(self, size: int = -1) -> bytes: ...


class UploadFile(te.TypedDict):
    file_name: str
    content: bytes | t.IO[bytes] | ReadableBinary | str
    content_type: te.NotRequired[str]


def apply_upload_file_defaults(uf: UploadFile) -> UploadFile:
    if not hasattr(uf, "content_type") or uf["content_type"] is None:
        uf["content_type"] = "application/octet-stream"

    return uf


class StorageClient(BaseClient):
    """The client which implements all storage endpoints.

    This class passes its arguments through to :py:class:`.BaseClient`. Check the documentation of that class for
    further information. Note that ``base_url`` defaults :py:const:`~flame_hub._defaults.DEFAULT_STORAGE_BASE_URL`.

    See Also
    --------
    :py:class:`.BaseClient`
    """

    def __init__(
        self,
        base_url: str = DEFAULT_STORAGE_BASE_URL,
        auth: AuthParam = None,
        **kwargs: te.Unpack[ClientKwargs],
    ):
        super().__init__(base_url, auth, **kwargs)

    def create_bucket(self, name: str, region: str | None = None, **params: te.Unpack[BaseKwargs]) -> Bucket:
        return self._create_resource(Bucket, CreateBucket(name=name, region=region), "buckets", **params)

    def delete_bucket(self, bucket_id: Bucket | str | uuid.UUID, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("buckets", bucket_id, **params)

    def get_buckets(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Bucket]:
        return self._get_all_resources(Bucket, "buckets", **params)

    def find_buckets(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Bucket]:
        return self._find_all_resources(Bucket, "buckets", **params)

    def get_bucket(self, bucket_id: Bucket | str | uuid.UUID, **params: te.Unpack[GetKwargs]) -> Bucket | None:
        return self._get_single_resource(Bucket, "buckets", bucket_id, **params)

    def stream_bucket_tarball(
        self,
        bucket_id: Bucket | str | uuid.UUID,
        chunk_size: int = 1024,
        **params: te.Unpack[BaseKwargs],
    ) -> t.Iterator[bytes]:
        r = self._request(
            "GET",
            "buckets",
            str(obtain_uuid_from(bucket_id)),
            "stream",
            expected_code=httpx.codes.OK.value,
            stream=True,
            **params,
        )

        try:
            for b in r.iter_bytes(chunk_size=chunk_size):
                yield b
        finally:
            r.close()

    def upload_to_bucket(
        self,
        bucket_id: Bucket | str | uuid.UUID,
        *upload_file: UploadFile,
        **params: te.Unpack[BaseKwargs],
    ) -> list[BucketFile]:
        upload_file_tpl = tuple(apply_upload_file_defaults(uf) for uf in upload_file)
        upload_file_dict = {
            str(uuid.uuid4()): (uf["file_name"], uf["content"], uf["content_type"]) for uf in upload_file_tpl
        }

        r = self._request(
            "POST",
            "buckets",
            str(obtain_uuid_from(bucket_id)),
            "upload",
            expected_code=httpx.codes.CREATED.value,
            files=upload_file_dict,
            **params,
        )

        return ResourceList[BucketFile](**r.json()).data

    def delete_bucket_file(self, bucket_file_id: BucketFile | str | uuid.UUID, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("bucket-files", bucket_file_id, **params)

    def get_bucket_file(
        self, bucket_file_id: BucketFile | str | uuid.UUID, **params: te.Unpack[GetKwargs]
    ) -> BucketFile | None:
        return self._get_single_resource(
            BucketFile, "bucket-files", bucket_file_id, include=get_includable_names(BucketFile), **params
        )

    def get_bucket_files(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[BucketFile]:
        return self._get_all_resources(BucketFile, "bucket-files", include=get_includable_names(BucketFile), **params)

    def find_bucket_files(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[BucketFile]:
        return self._find_all_resources(BucketFile, "bucket-files", include=get_includable_names(BucketFile), **params)

    def stream_bucket_file(
        self,
        bucket_file_id: BucketFile | str | uuid.UUID,
        chunk_size: int = 1024,
        **params: te.Unpack[BaseKwargs],
    ) -> t.Iterator[bytes]:
        r = self._request(
            "GET",
            "bucket-files",
            str(obtain_uuid_from(bucket_file_id)),
            "stream",
            expected_code=httpx.codes.OK.value,
            stream=True,
            **params,
        )

        try:
            for b in r.iter_bytes(chunk_size=chunk_size):
                yield b
        finally:
            r.close()
