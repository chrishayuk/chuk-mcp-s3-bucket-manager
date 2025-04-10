# src/chuk_mcp_s3_bucket_manager/tools.py
import os
import logging
import sys
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from dotenv import load_dotenv
from pydantic import ValidationError

# Import MCP tool decorator from your runtime
from chuk_mcp_runtime.common.mcp_tool_decorator import mcp_tool

# Import the defined models
from chuk_mcp_s3_bucket_manager.models import (
    BucketInfo,
    ListBucketsResult,
    CreateBucketInput,
    CreateBucketResult,
    DeleteBucketInput,
    DeleteBucketResult
)

logger = logging.getLogger("chuk-mcp-s3-bucket-manager")

# Configure logger to output to stderr
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.CRITICAL)

# Load environment variables from .env file if it exists
load_dotenv()

def get_s3_client():
    """Create and return an S3 client using environment variables."""
    endpoint_url = os.environ.get("AWS_ENDPOINT_URL_S3")
    region_name = os.environ.get("AWS_REGION", "us-east-1")

    client_kwargs = {}
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url
    if region_name:
        client_kwargs["region_name"] = region_name

    return boto3.client("s3", **client_kwargs)

@mcp_tool(name="list_buckets", description="List all S3 buckets")
def list_buckets() -> dict:
    """List all available S3 buckets and return their details."""
    s3 = get_s3_client()
    try:
        response = s3.list_buckets()
        bucket_list = []
        for bucket in response.get("Buckets", []):
            # Determine bucket region (default to us-east-1 if not specified)
            try:
                loc_response = s3.get_bucket_location(Bucket=bucket["Name"])
                region = loc_response.get("LocationConstraint") or "us-east-1"
            except Exception:
                region = "unknown"
            bucket_list.append(
                BucketInfo(
                    name=bucket["Name"],
                    creation_date=bucket["CreationDate"],
                    region=region
                )
            )
        result = ListBucketsResult(buckets=bucket_list)
        result_dict = result.model_dump()

        # Convert any datetime values to ISO format strings before returning
        for bucket in result_dict.get("buckets", []):
            if "creation_date" in bucket and isinstance(bucket["creation_date"], datetime):
                bucket["creation_date"] = bucket["creation_date"].isoformat()
        return result_dict
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        raise ValueError(f"Error listing buckets: {e}")

@mcp_tool(name="create_bucket", description="Create a new S3 bucket")
def create_bucket(bucket_name: str) -> dict:
    """Create a new S3 bucket with the specified name."""
    s3 = get_s3_client()
    # Validate input using the CreateBucketInput model
    try:
        input_data = CreateBucketInput(bucket_name=bucket_name)
    except ValidationError as e:
        raise ValueError(f"Invalid input for bucket creation: {e}")

    try:
        # Check whether the bucket already exists
        try:
            s3.head_bucket(Bucket=input_data.bucket_name)
            return CreateBucketResult(
                message=f"Bucket '{input_data.bucket_name}' already exists."
            ).model_dump()
        except ClientError as ce:
            if ce.response["Error"]["Code"] != "404":
                raise ce

        region = os.environ.get("AWS_REGION", "us-east-1")
        if region == "us-east-1":
            s3.create_bucket(Bucket=input_data.bucket_name)
        else:
            s3.create_bucket(
                Bucket=input_data.bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        return CreateBucketResult(
            message=f"Bucket '{input_data.bucket_name}' created successfully in {region}."
        ).model_dump()
    except Exception as e:
        logger.error(f"Error creating bucket: {e}")
        raise ValueError(f"Error creating bucket: {e}")

@mcp_tool(name="delete_bucket", description="Delete an S3 bucket")
def delete_bucket(bucket_name: str, force: bool = False) -> dict:
    """Delete an S3 bucket. If force is True, clear the bucket before deletion."""
    s3 = get_s3_client()
    # Validate input using the DeleteBucketInput model
    try:
        input_data = DeleteBucketInput(bucket_name=bucket_name, force=force)
    except ValidationError as e:
        raise ValueError(f"Invalid input for bucket deletion: {e}")

    try:
        # Check whether the bucket exists
        try:
            s3.head_bucket(Bucket=input_data.bucket_name)
        except ClientError:
            return DeleteBucketResult(
                message=f"Bucket '{input_data.bucket_name}' does not exist."
            ).model_dump()

        if input_data.force:
            _clear_bucket(s3, input_data.bucket_name)

        s3.delete_bucket(Bucket=input_data.bucket_name)
        return DeleteBucketResult(
            message=f"Bucket '{input_data.bucket_name}' deleted successfully."
        ).model_dump()
    except Exception as e:
        logger.error(f"Error deleting bucket: {e}")
        raise ValueError(f"Error deleting bucket: {e}")

def _clear_bucket(s3, bucket_name: str):
    """Internal helper to remove all objects from a bucket."""
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        if "Contents" in page:
            objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
            s3.delete_objects(Bucket=bucket_name, Delete={"Objects": objects})
    # Extend here for handling versioned objects if needed.
