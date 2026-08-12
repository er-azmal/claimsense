import json
import boto3

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("Claims")

def lambda_handler(event, context):
    try:
        # For GET /claims/{claim_id}, API Gateway puts the id here.
        claim_id = (event.get("pathParameters") or {}).get("claim_id")

        if not claim_id:
            return {
                "statusCode": 400,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "claim_id is required"}),
            }

        result = table.get_item(Key={"claim_id": claim_id})
        item = result.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Claim not found"}),
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(item, default=str),  # default=str handles any odd types
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)}),
        }
