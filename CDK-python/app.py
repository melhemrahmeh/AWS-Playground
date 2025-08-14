#!/usr/bin/env python3
import aws_cdk as cdk
from deploy_resources import ResourceStack

app = cdk.App()
ResourceStack(app, "ResourceStack")
app.synth()
