import os
import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def response(status_code, body=None):
    return {
        "statusCode": status_code,
        "body": json.dumps(body) if body is not None else "",
        "headers": {"Content-Type": "application/json"}
    }

def create_task(body):
    if not body.get("id"):
        return response(400, {"error": "Task must have an 'id'"})
    table.put_item(Item=body)
    return response(201, body)

def get_task(task_id):
    if not task_id:
        return response(400, {"error": "Task ID missing"})
    result = table.get_item(Key={"id": task_id})
    item = result.get("Item")
    if not item:
        return response(404, {"error": "Task not found"})
    return response(200, item)

def update_task(task_id, body):
    if not task_id:
        return response(400, {"error": "Task ID missing"})
    body["id"] = task_id  # ensure ID matches path
    table.put_item(Item=body)
    return response(200, body)

def delete_task(task_id):
    if not task_id:
        return response(400, {"error": "Task ID missing"})
    table.delete_item(Key={"id": task_id})
    return response(204)

def lambda_handler(event, context):
    method = event.get("httpMethod")
    path = event.get("path", "")
    path_params = event.get("pathParameters") or {}
    task_id = path_params.get("id")

    try:
        if method == "POST" and path.endswith("/tasks"):
            body = json.loads(event.get("body") or "{}")
            return create_task(body)

        elif method == "GET" and "/tasks/" in path:
            return get_task(task_id)

        elif method == "PUT" and "/tasks/" in path:
            body = json.loads(event.get("body") or "{}")
            return update_task(task_id, body)

        elif method == "DELETE" and "/tasks/" in path:
            return delete_task(task_id)

        else:
            return response(400, {"error": "Invalid request"})
    except Exception as e:
        return response(500, {"error": str(e)})
