"""Create the configured S3 bucket if necessary."""

from botocore.exceptions import ClientError

from src import config
from src.core import get_s3_client


def create_bucket():
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=config.S3_BUCKET)
    except ClientError as exc:
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status != 404:
            raise
        params = {"Bucket": config.S3_BUCKET}
        if config.S3_REGION != "us-east-1":
            params["CreateBucketConfiguration"] = {"LocationConstraint": config.S3_REGION}
        s3.create_bucket(**params)
    return config.S3_BUCKET


if __name__ == "__main__":
    print(f"Bucket ready: {create_bucket()}")
