import pytest

from tests.helpers import next_random_string, next_uuid

pytestmark = pytest.mark.integration


@pytest.fixture()
def bucket(storage_client):
    new_bucket = storage_client.create_bucket(next_random_string())
    yield new_bucket
    storage_client.delete_bucket(new_bucket)


def test_get_buckets(storage_client, bucket):
    assert any(bucket.id == b.id for b in storage_client.get_buckets().data)


def test_get_bucket(storage_client, bucket):
    assert bucket == storage_client.get_bucket(bucket.id)


def test_get_bucket_not_found(storage_client):
    assert storage_client.get_bucket(next_uuid()) is None
