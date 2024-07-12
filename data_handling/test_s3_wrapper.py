from threading import Thread
from unittest.mock import patch

import boto3
import pytest
from aiohttp import ClientError
from moto import mock_s3
# Local packages
from s3_wrapper import S3Wrapper
from util_s3 import S3Lock


# Mocked S3 setup
@pytest.fixture
def s3_client():
    with mock_s3():
        yield boto3.client("s3")

# Test functions (using pytest)
def test_concurrent_uploads(s3_client):
    bucket_name = "test-bucket"
    s3_client.create_bucket(Bucket=bucket_name)
    s3_wrapper = S3Wrapper()

    def upload_thread(file_name, object_name):
        with S3Lock(s3_wrapper, bucket_name, object_name):
            s3_wrapper.upload_file(file_name, bucket_name, object_name)

    threads = []
    for i in range(5):
        file_name = f"file_{i}.txt"
        object_name = f"object_{i}.txt"
        t = Thread(target=upload_thread, args=(file_name, object_name))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    objects = s3_wrapper.list_objects(bucket_name)
    assert len(objects) == 5
    for i in range(5):
        assert f"object_{i}.txt" in objects


def test_create_and_delete_bucket(s3_client):
    bucket_name = "new-bucket"
    s3_wrapper = S3Wrapper()

    with S3Lock(s3_wrapper, bucket_name):
        s3_wrapper.create_bucket(bucket_name)
        s3_client.put_object(Bucket=bucket_name, Key="test_key", Body="test_value")

    with S3Lock(s3_wrapper, bucket_name):
        s3_wrapper.delete_bucket(bucket_name)

    with pytest.raises(ClientError):
        s3_client.head_bucket(Bucket=bucket_name)  # Should raise exception since bucket is deleted


# Mocking S3 lock
@patch("util_s3.S3Lock")
def test_concurrent_deletes(mock_s3_lock, s3_client):
    bucket_name = "test-bucket-2"
    s3_client.create_bucket(Bucket=bucket_name)
    for i in range(5):
        s3_client.put_object(Bucket=bucket_name, Key=f"object_{i}.txt", Body="test_value")
    s3_wrapper = S3Wrapper()

    def delete_thread(object_name):
        with S3Lock(s3_wrapper, bucket_name, object_name):
            s3_wrapper.delete_file(bucket_name, object_name)
            
    threads = []
    for i in range(5):
        object_name = f"object_{i}.txt"
        t = Thread(target=delete_thread, args=(object_name,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    objects = s3_wrapper.list_objects(bucket_name)
    assert len(objects) == 0


