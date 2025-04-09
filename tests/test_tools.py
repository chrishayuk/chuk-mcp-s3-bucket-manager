# tests/test_tools.py
import pytest
from datetime import datetime
from botocore.exceptions import ClientError
from chuk_mcp_s3_bucket_manager import tools

class FakeS3Client:
    def list_buckets(self):
        return {
            "Buckets": [
                {"Name": "bucket1", "CreationDate": datetime(2025, 1, 1, 12, 0, 0)},
                {"Name": "bucket2", "CreationDate": datetime(2025, 1, 2, 12, 0, 0)},
            ]
        }

    def get_bucket_location(self, Bucket):
        if Bucket == "bucket1":
            return {"LocationConstraint": "us-east-1"}
        elif Bucket == "bucket2":
            return {"LocationConstraint": "eu-west-1"}
        raise Exception("Bucket not found")

    def head_bucket(self, Bucket):
        # Simulate that the bucket "exists-bucket" exists; any other bucket will be simulated as not found.
        if Bucket == "exists-bucket":
            return {}
        # Simulate not found by raising a ClientError with code "404"
        raise ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket")

    def create_bucket(self, Bucket, CreateBucketConfiguration=None):
        # Simulate successful bucket creation.
        return {}

    def delete_bucket(self, Bucket):
        return {}

    def get_paginator(self, operation_name):
        # Only support list_objects_v2 for our current tests.
        if operation_name == "list_objects_v2":
            class FakePaginator:
                def paginate(self, Bucket, Prefix=None):
                    # Return an empty list of objects.
                    return [{"Contents": []}]
            return FakePaginator()
        raise ValueError("Unsupported paginator operation")

    def delete_objects(self, Bucket, Delete):
        return {"Deleted": Delete["Objects"]}

# Pytest fixture that returns our fake S3 client.
@pytest.fixture
def fake_s3_client():
    return FakeS3Client()

# Patch the get_s3_client function in the tools module to return our fake client.
@pytest.fixture(autouse=True)
def patch_get_s3_client(monkeypatch, fake_s3_client):
    monkeypatch.setattr(tools, "get_s3_client", lambda: fake_s3_client)

def test_list_buckets():
    result = tools.list_buckets()
    # Check that the expected keys are in our result.
    assert "buckets" in result
    buckets = result["buckets"]
    # We expect two buckets according to our fake response.
    assert len(buckets) == 2
    names = {bucket["name"] for bucket in buckets}
    assert "bucket1" in names
    assert "bucket2" in names

def test_create_bucket_already_exists():
    # For bucket "exists-bucket", the fake head_bucket returns success,
    # so the function should report that the bucket already exists.
    result = tools.create_bucket(bucket_name="exists-bucket")
    assert "already exists" in result["message"]

def test_create_bucket_success():
    # For a bucket that does not exist (e.g., "new-bucket"), head_bucket will raise ClientError.
    result = tools.create_bucket(bucket_name="new-bucket")
    assert "created successfully" in result["message"]

def test_delete_bucket_not_exists():
    # For a non-existent bucket ("nonexistent-bucket"), head_bucket will raise a ClientError.
    result = tools.delete_bucket(bucket_name="nonexistent-bucket", force=False)
    assert "does not exist" in result["message"]

def test_delete_bucket_success():
    # For an existing bucket ("exists-bucket") without forcing deletion, deletion should succeed.
    result = tools.delete_bucket(bucket_name="exists-bucket", force=False)
    assert "deleted successfully" in result["message"]

def test_delete_bucket_with_force(monkeypatch):
    # For forced deletion, our internal _clear_bucket helper should be called.
    # We'll monkeypatch _clear_bucket to record that it was called.
    called = False

    def fake_clear_bucket(s3, bucket_name):
        nonlocal called
        called = True

    monkeypatch.setattr(tools, "_clear_bucket", fake_clear_bucket)
    result = tools.delete_bucket(bucket_name="exists-bucket", force=True)
    assert called is True
    assert "deleted successfully" in result["message"]
