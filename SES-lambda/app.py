import boto3
from botocore.exceptions import ClientError

ses_client = boto3.client('ses', region_name='us-east-1')

SENDER = "new-sender@example.com"
RECIPIENT = "recipient@example.com"
SUBJECT = "Hello from AWS Lambda (HTML Email)!"
CHARSET = "UTF-8"

# HTML body
BODY_HTML = """<html>
<head></head>
<body>
  <h1>Hello!</h1>
  <p>This is a <b>HTML email</b> sent by AWS Lambda every 15 minutes.</p>
</body>
</html>"""

def lambda_handler(event, context):
    try:
        response = ses_client.send_email(
            Source=SENDER,
            Destination={'ToAddresses': [RECIPIENT]},
            Message={
                'Subject': {'Data': SUBJECT, 'Charset': CHARSET},
                'Body': {
                    'Html': {'Data': BODY_HTML, 'Charset': CHARSET}
                }
            }
        )
        print("Email sent! Message ID:", response['MessageId'])
        return {"status": "success", "message_id": response['MessageId']}
    except ClientError as e:
        print("Error:", e.response['Error']['Message'])
        return {"status": "error", "message": e.response['Error']['Message']}