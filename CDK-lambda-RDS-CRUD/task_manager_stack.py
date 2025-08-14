import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secrets,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    Duration
)
from constructs import Construct
import os

class TaskManagerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC
        vpc = ec2.Vpc(self, "TaskManagerVPC", max_azs=2)

        # Security Groups
        db_sg = ec2.SecurityGroup(self, "DBSecurityGroup", vpc=vpc)
        lambda_sg = ec2.SecurityGroup(self, "LambdaSecurityGroup", vpc=vpc)

        # Allow Lambda to connect to RDS
        db_sg.add_ingress_rule(lambda_sg, ec2.Port.tcp(5432), "Allow Lambda to connect to Postgres")

        # DB credentials
        db_secret = secrets.Secret(self, "DBSecret",
            generate_secret_string=secrets.SecretStringGenerator(
                secret_string_template='{"username":"taskadmin"}',  # changed from admin
                generate_string_key="password",
                exclude_punctuation=True
            )
        )

        # RDS PostgreSQL 15.7
        db_instance = rds.DatabaseInstance(self, "TaskManagerDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15_7
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            credentials=rds.Credentials.from_secret(db_secret),
            multi_az=False,
            allocated_storage=20,
            max_allocated_storage=100,
            security_groups=[db_sg],
            publicly_accessible=False,  # safer
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Lambda function
        lambda_fn = _lambda.Function(self, "TaskLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(os.path.join("lambda_src")),
            vpc=vpc,
            security_groups=[lambda_sg],
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "DB_SECRET": db_secret.secret_name,
                "DB_NAME": "postgres",
                "DB_PORT": "5432"
            }
        )

        db_secret.grant_read(lambda_fn)

        # API Gateway
        api = apigw.RestApi(self, "TaskManagerAPI",
            rest_api_name="Task Manager Service"
        )

        tasks = api.root.add_resource("tasks")
        tasks.add_method("GET", apigw.LambdaIntegration(lambda_fn))
        tasks.add_method("POST", apigw.LambdaIntegration(lambda_fn))

        task_id = tasks.add_resource("{id}")
        task_id.add_method("PUT", apigw.LambdaIntegration(lambda_fn))
        task_id.add_method("DELETE", apigw.LambdaIntegration(lambda_fn))

        # Outputs
        cdk.CfnOutput(self, "APIEndpoint", value=api.url)
        cdk.CfnOutput(self, "DBEndpoint", value=db_instance.db_instance_endpoint_address)
        cdk.CfnOutput(self, "DBSecretArn", value=db_secret.secret_arn)
