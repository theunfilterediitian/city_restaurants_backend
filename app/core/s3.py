import uuid
import boto3
from botocore.config import Config
from app.core.config import settings


s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
    config=Config(signature_version="s3v4"),
)


def upload_file_to_s3(file, folder: str) -> str:
    ext = file.filename.split(".")[-1]
    key = f"{folder}/{uuid.uuid4()}.{ext}"

    s3.upload_fileobj(
        file.file,
        settings.AWS_S3_BUCKET,
        key,
        ExtraArgs={"ContentType": file.content_type},
    )

    return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def delete_file_from_s3(image_url: str):
    """
    Extracts S3 key from full URL and deletes object
    """
    base = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/"
    key = image_url.replace(base, "")

    s3.delete_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=key
    )
