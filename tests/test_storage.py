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


@pytest.mark.skip(reason="service does not return updated object")
def test_update_bucket(storage_client, bucket):
    new_name = next_random_string()
    new_bucket = storage_client.update_bucket(bucket.id, name=new_name, region="us-west-1")

    assert bucket != new_bucket
    assert new_bucket.name == new_name
