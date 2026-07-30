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
    unwrap_enveloped_resource,
)
from flame_hub._defaults import DEFAULT_STORAGE_BASE_URL


class CreateBucket(BaseModel):
    name: str
    region: str | None


class Bucket(CreateBucket):
    id: uuid.UUID
    createdAt: datetime
    updatedAt: datetime
    actorId: uuid.UUID | None
    actorType: str | None
    realmId: uuid.UUID | None


class BucketFile(BaseModel):
    id: uuid.UUID
    name: str
    path: str
    hash: str
    directory: str
    size: int | None
    createdAt: datetime
    updatedAt: datetime
    actorType: str
    actorId: uuid.UUID
    realmId: uuid.UUID
    bucketId: uuid.UUID
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

    def _unwrap_single_resource(self, body: t.Any) -> t.Any:
        """Extract the resource object from the storage service's record envelope.

        Since ``0.13.0`` the FLAME Hub responds to record requests with :python:`{"data": ..., "meta": ...}` instead
        of the resource object itself, mirroring the envelope that list responses have always used. ``meta`` holds
        response-scoped extras such as the queryable schema of the endpoint and is discarded.

        The bucket upload endpoint responds with a collection rather than a record and is parsed as a
        :py:class:`.ResourceList` instead of going through this method.

        Raises
        ------
        :py:exc:`ValueError`
            If ``body`` does not carry a ``data`` property, which is the case for FLAME Hub versions before ``0.13.0``.

        See Also
        --------
        :py:meth:`.BaseClient._unwrap_single_resource`, :py:func:`.unwrap_enveloped_resource`
        """
        return unwrap_enveloped_resource(body, "FLAME Hub 0.13.0")

    def create_bucket(self, name: str, region: str | None = None, **params: te.Unpack[BaseKwargs]) -> Bucket:
        return self._create_resource(Bucket, CreateBucket(name=name, region=region), "buckets", **params)

    def delete_bucket(self, bucketId: Bucket | str | uuid.UUID, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("buckets", bucketId, **params)

    def get_buckets(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[Bucket]:
        return self._get_all_resources(Bucket, "buckets", **params)

    def find_buckets(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[Bucket]:
        return self._find_all_resources(Bucket, "buckets", **params)

    def get_bucket(self, bucketId: Bucket | str | uuid.UUID, **params: te.Unpack[GetKwargs]) -> Bucket | None:
        return self._get_single_resource(Bucket, "buckets", bucketId, **params)

    def stream_bucket_tarball(
        self,
        bucketId: Bucket | str | uuid.UUID,
        chunk_size: int = 1024,
        **params: te.Unpack[BaseKwargs],
    ) -> t.Iterator[bytes]:
        r = self._request(
            "GET",
            "buckets",
            str(obtain_uuid_from(bucketId)),
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
        bucketId: Bucket | str | uuid.UUID,
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
            str(obtain_uuid_from(bucketId)),
            "upload",
            expected_code=httpx.codes.CREATED.value,
            files=upload_file_dict,
            **params,
        )

        return ResourceList[BucketFile](**r.json()).data

    def delete_bucket_file(self, bucketFileId: BucketFile | str | uuid.UUID, **params: te.Unpack[BaseKwargs]):
        self._delete_resource("bucket-files", bucketFileId, **params)

    def get_bucket_file(
        self, bucketFileId: BucketFile | str | uuid.UUID, **params: te.Unpack[GetKwargs]
    ) -> BucketFile | None:
        return self._get_single_resource(
            BucketFile, "bucket-files", bucketFileId, include=get_includable_names(BucketFile), **params
        )

    def get_bucket_files(self, **params: te.Unpack[GetKwargs]) -> ResourceListResult[BucketFile]:
        return self._get_all_resources(BucketFile, "bucket-files", include=get_includable_names(BucketFile), **params)

    def find_bucket_files(self, **params: te.Unpack[FindAllKwargs]) -> ResourceListResult[BucketFile]:
        return self._find_all_resources(BucketFile, "bucket-files", include=get_includable_names(BucketFile), **params)

    def stream_bucket_file(
        self,
        bucketFileId: BucketFile | str | uuid.UUID,
        chunk_size: int = 1024,
        **params: te.Unpack[BaseKwargs],
    ) -> t.Iterator[bytes]:
        r = self._request(
            "GET",
            "bucket-files",
            str(obtain_uuid_from(bucketFileId)),
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
