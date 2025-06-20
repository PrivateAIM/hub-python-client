import tarfile
from io import BytesIO

import pytest

from flame_hub import get_includable_names
from flame_hub.models import BucketFile
from tests.helpers import next_random_string, next_uuid

pytestmark = pytest.mark.integration


@pytest.fixture()
def bucket(storage_client):
    new_bucket = storage_client.create_bucket(next_random_string())
    yield new_bucket
    storage_client.delete_bucket(new_bucket)


@pytest.fixture()
def bucket_file(storage_client, bucket, rng_bytes):
    new_bucket_file_lst = storage_client.upload_to_bucket(
        bucket,
        {
            "file_name": next_random_string(),
            "content": rng_bytes,
        },
    )

    # check that one file was uploaded
    assert len(new_bucket_file_lst) == 1
    new_bucket_file = new_bucket_file_lst.pop()

    yield new_bucket_file

    storage_client.delete_bucket_file(new_bucket_file)


@pytest.fixture(scope="session")
def bucket_file_includables():
    return get_includable_names(BucketFile)


def test_get_buckets(storage_client, bucket):
    assert len(storage_client.get_buckets()) > 0


def test_find_buckets(storage_client, bucket):
    assert storage_client.find_buckets(filter={"id": bucket.id}) == [bucket]


def test_get_bucket(storage_client, bucket):
    assert bucket == storage_client.get_bucket(bucket.id)


def test_stream_bucket_tarball(storage_client, bucket_file, rng_bytes):
    tarball_bytes = next(storage_client.stream_bucket_tarball(bucket_file.bucket_id))

    with tarfile.open(fileobj=BytesIO(tarball_bytes), mode="r") as tar:
        members = tar.getmembers()
        # check that only the single uploaded file is present
        assert len(members) == 1

        with tar.extractfile(members.pop()) as f:
            assert rng_bytes == f.read()


def test_get_bucket_not_found(storage_client):
    assert storage_client.get_bucket(next_uuid()) is None


def test_get_bucket_file(storage_client, bucket_file, bucket_file_includables):
    bucket_file_get = storage_client.get_bucket_file(bucket_file.id)

    assert bucket_file_get.id == bucket_file.id
    assert all(includable in bucket_file_get.model_fields_set for includable in bucket_file_includables)


def test_get_bucket_file_not_found(storage_client):
    assert storage_client.get_bucket_file(next_uuid()) is None


def test_get_bucket_files(storage_client, bucket_file, bucket_file_includables):
    bucket_files_get = storage_client.get_bucket_files()

    assert len(bucket_files_get) > 0
    assert all(includable in bf.model_fields_set for bf in bucket_files_get for includable in bucket_file_includables)


def test_find_bucket_files(storage_client, bucket_file, bucket_file_includables):
    bucket_files_find = storage_client.find_bucket_files(filter={"id": bucket_file.id})

    assert [bucket_file.id] == [bf.id for bf in bucket_files_find]
    assert all(includable in bf.model_fields_set for bf in bucket_files_find for includable in bucket_file_includables)


def test_stream_bucket_file(storage_client, bucket_file, rng_bytes):
    assert rng_bytes == next(storage_client.stream_bucket_file(bucket_file.id))
