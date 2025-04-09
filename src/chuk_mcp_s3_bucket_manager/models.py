# src/chuk_mcp_s3_bucket_manager/models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BucketInfo(BaseModel):
    name: str = Field(..., description="Bucket name")
    creation_date: datetime = Field(..., description="Bucket creation date")
    region: Optional[str] = Field(None, description="Bucket region")

class ListBucketsResult(BaseModel):
    buckets: List[BucketInfo] = Field(..., description="List of S3 buckets")

class CreateBucketInput(BaseModel):
    bucket_name: str = Field(..., description="Name of the bucket to create")

class CreateBucketResult(BaseModel):
    message: str = Field(..., description="Creation status message")

class DeleteBucketInput(BaseModel):
    bucket_name: str = Field(..., description="Name of the bucket to delete")
    force: bool = Field(False, description="Force deletion by clearing the bucket first")

class DeleteBucketResult(BaseModel):
    message: str = Field(..., description="Deletion status message")
