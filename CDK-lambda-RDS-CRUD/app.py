#!/usr/bin/env python3
import aws_cdk as cdk
from task_manager_stack import TaskManagerStack

app = cdk.App()
TaskManagerStack(app, "TaskManagerStack",
    env=cdk.Environment(account="accountid", region="us-east-1")
)
app.synth()