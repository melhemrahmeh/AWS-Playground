from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_iam as iam,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class ResourceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket
        bucket = s3.Bucket(
            self,
            "ResourceBucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Create VPC
        vpc = ec2.Vpc(
            self,
            "ResourceVPC",
            max_azs=2
        )

        # Create IAM role for EC2
        role = iam.Role(
            self,
            "EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )

        # Allow EC2 role to put/delete objects in the bucket
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject", "s3:DeleteObject"],
                resources=[f"{bucket.bucket_arn}/*"]
            )
        )

        # User data script for EC2 instance
        user_data_script = f"""#!/bin/bash
        yum update -y
        yum install -y aws-cli
        echo "Hello CDK" > /tmp/test.txt
        aws s3 cp /tmp/test.txt s3://{bucket.bucket_name}/test.txt
        echo "File uploaded"
        aws s3 rm s3://{bucket.bucket_name}/test.txt
        echo "File deleted"
        """

        # Create EC2 instance
        instance = ec2.Instance(
            self,
            "ResourceInstance",
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            vpc=vpc,
            role=role,
            user_data=ec2.UserData.custom(user_data_script)
        )

        # Outputs
        CfnOutput(self, "BucketName", value=bucket.bucket_name)
        CfnOutput(self, "EC2PublicIP", value=instance.instance_public_ip)
