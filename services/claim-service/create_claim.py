import json
import uuid
import boto3
from datetime import datetime, timezone

# boto3.resource = the friendly, high-level way to talk to DynamoDB.
# Declared OUTSIDE the handler so AWS reuses it on "warm" invocations (faster).
dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("Claims")

def lambda_handler(event, context):
    try:
        # API Gateway hands us the POST body as a JSON *string*, so we parse it.
        body = json.loads(event.get("body") or "{}")

        claim_id = str(uuid.uuid4())                 # unique id for this claim
        now = datetime.now(timezone.utc).isoformat()

        item = {
            "claim_id": claim_id,
            "status": "SUBMITTED",
            "customer_name": body.get("customer_name", "Unknown"),
            "vehicle_number": body.get("vehicle_number", ""),
            "policy_number": body.get("policy_number", ""),
            "description": body.get("description", ""),
            "image_key": body.get("image_key", ""),  # S3 key — filled by upload flow (Day 3)
            "assessment": None,                       # ML verdict attached later
            "created_at": now,
            "updated_at": now,
        }

        table.put_item(Item=item)                    # write the row

        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": "Claim created", "claim_id": claim_id, "status": "SUBMITTED"}),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)}),
        }
