import boto3
import json
import os
import time
import zipfile
from botocore.exceptions import ClientError

AWS_REGION = "us-east-1"
LAMBDA_NAME = "TasksFunction"
API_NAME = "TasksAPI"
TABLE_NAME = "Tasks"
ROLE_NAME = "lambda-dynamodb-crud-role"

iam = boto3.client("iam", region_name=AWS_REGION)
dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
lambda_client = boto3.client("lambda", region_name=AWS_REGION)
apigateway = boto3.client("apigateway", region_name=AWS_REGION)
sts = boto3.client("sts")

ACCOUNT_ID = sts.get_caller_identity()["Account"]

def ensure_dynamodb_table():
    try:
        dynamodb.describe_table(TableName=TABLE_NAME)
        print(f"DynamoDB table '{TABLE_NAME}' already exists.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Creating DynamoDB table '{TABLE_NAME}'...")
            dynamodb.create_table(
                TableName=TABLE_NAME,
                AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
                KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                BillingMode="PAY_PER_REQUEST",
            )
            waiter = dynamodb.get_waiter("table_exists")
            waiter.wait(TableName=TABLE_NAME)
            print(f"Table '{TABLE_NAME}' created successfully.")
        else:
            raise

def create_iam_role():
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }
    try:
        print("Creating IAM role...")
        role = iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy),
        )
        role_arn = role["Role"]["Arn"]
        iam.attach_role_policy(
            RoleName=ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        )
        iam.attach_role_policy(
            RoleName=ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
        )
        print("Waiting for role to propagate...")
        time.sleep(10)
        return role_arn
    except ClientError as e:
        if e.response["Error"]["Code"] == "EntityAlreadyExists":
            return iam.get_role(RoleName=ROLE_NAME)["Role"]["Arn"]
        else:
            raise

def package_lambda():
    print("Packaging Lambda function...")
    with zipfile.ZipFile("lambda-crud.zip", "w") as z:
        z.write("app.py")
    return os.path.abspath("lambda-crud.zip")

def create_or_update_lambda(role_arn, zip_path):
    with open(zip_path, "rb") as f:
        code_bytes = f.read()

    try:
        print("Creating Lambda function...")
        lambda_client.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime="python3.12",
            Role=role_arn,
            Handler="app.lambda_handler",
            Code={"ZipFile": code_bytes},
            Environment={"Variables": {"TABLE_NAME": TABLE_NAME}},
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            print("Updating existing Lambda function...")
            lambda_client.update_function_code(
                FunctionName=LAMBDA_NAME, ZipFile=code_bytes
            )
        else:
            raise

def create_or_get_api():
    apis = apigateway.get_rest_apis()
    for item in apis.get("items", []):
        if item["name"] == API_NAME:
            return item["id"]
    print("Creating API Gateway REST API...")
    api = apigateway.create_rest_api(name=API_NAME)
    return api["id"]

def get_root_resource_id(api_id):
    resources = apigateway.get_resources(restApiId=api_id)
    return next(item["id"] for item in resources["items"] if item["path"] == "/")

def create_resource(api_id, parent_id, path_part):
    resources = apigateway.get_resources(restApiId=api_id)
    for item in resources["items"]:
        if item["path"] == f"/{path_part}" or (path_part == "{id}" and item["path"] == "/tasks/{id}"):
            return item["id"]
    res = apigateway.create_resource(
        restApiId=api_id, parentId=parent_id, pathPart=path_part
    )
    return res["id"]

def create_method(api_id, resource_id, method):
    try:
        apigateway.get_method(restApiId=api_id, resourceId=resource_id, httpMethod=method)
    except ClientError:
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=method,
            authorizationType="NONE",
        )
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=method,
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=f"arn:aws:apigateway:{AWS_REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{AWS_REGION}:{ACCOUNT_ID}:function:{LAMBDA_NAME}/invocations",
        )

def add_lambda_permission(api_id):
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId=f"apigateway-{int(time.time())}",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{AWS_REGION}:{ACCOUNT_ID}:{api_id}/*/*/*",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceConflictException":
            raise

def deploy_api(api_id):
    apigateway.create_deployment(restApiId=api_id, stageName="prod")
    return f"https://{api_id}.execute-api.{AWS_REGION}.amazonaws.com/prod"

if __name__ == "__main__":
    ensure_dynamodb_table()
    role_arn = create_iam_role()
    zip_path = package_lambda()
    create_or_update_lambda(role_arn, zip_path)
    api_id = create_or_get_api()
    root_id = get_root_resource_id(api_id)
    tasks_id = create_resource(api_id, root_id, "tasks")
    task_id_res = create_resource(api_id, tasks_id, "{id}")
    create_method(api_id, tasks_id, "POST")
    create_method(api_id, task_id_res, "GET")
    create_method(api_id, task_id_res, "PUT")
    create_method(api_id, task_id_res, "DELETE")
    add_lambda_permission(api_id)
    api_url = deploy_api(api_id)
    print(f"=== Deployment Complete ===\nAPI URL: {api_url}")
