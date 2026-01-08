import boto3

s3 = boto3.client(
    "s3",
    aws_access_key_id="AKIAS6OVFUAVBGNCXD53",
    aws_secret_access_key="yK34GwI2Ka3YnXbYts40pB1I6EWOStmTgYL",
    region_name="eu-north-1",
)

s3.put_object(
    Bucket="dannavv-bucket",
    Key="test.txt",
    Body=b"hello"
)

print("UPLOAD OK")
