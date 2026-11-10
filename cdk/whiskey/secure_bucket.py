"""NF-10 / design §8: every bucket goes through this helper."""

from aws_cdk import RemovalPolicy
from aws_cdk import aws_s3 as s3
from constructs import Construct


def secure_bucket(scope: Construct, id: str, **kw) -> s3.Bucket:
    return s3.Bucket(
        scope,
        id,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        enforce_ssl=True,
        encryption=s3.BucketEncryption.S3_MANAGED,
        object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
        versioned=False,
        removal_policy=RemovalPolicy.DESTROY,
        auto_delete_objects=True,
        **kw,
    )
