import json
import boto3
import uuid

s3 = boto3.client("s3", region_name="ap-south-1")
BUCKET = "claimsense-images-azmal"

def lambda_handler(event, context):
    try:
        # claim_id comes as a query string: /upload-url?claim_id=xxx
        params = event.get("queryStringParameters") or {}
        claim_id = params.get("claim_id")

        if not claim_id:
            return {
                "statusCode": 400,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "claim_id is required"}),
            }

        # Build a unique S3 key for this claim's image
        image_key = f"claims/{claim_id}/{uuid.uuid4()}.jpg"

        # Generate a presigned PUT URL, valid 5 minutes
        presigned_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET,
                "Key": image_key,
                "ContentType": "image/jpeg",
            },
            ExpiresIn=300,
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"upload_url": presigned_url, "image_key": image_key}),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)}),
        }
