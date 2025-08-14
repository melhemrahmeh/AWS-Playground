import boto3
from datetime import datetime
import time

# ----------------------------
# 1. Initialize DynamoDB
# ----------------------------
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# ----------------------------
# 2. Create a fresh table with date-based name
# ----------------------------
def create_table():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    table_name = f"Users_{timestamp}"

    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},   # Partition key
            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}  # Sort key
        ],
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'},
            {'AttributeName': 'email', 'AttributeType': 'S'}  # For GSI
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'EmailIndex',
                'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            }
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )
    table.wait_until_exists()
    print(f"Table '{table_name}' created.")
    return table

table = create_table()

# ----------------------------
# 3. Add Users
# ----------------------------
def add_user(user_id, name, email):
    table.put_item(
        Item={
            'user_id': user_id,
            'created_at': str(int(time.time())),  # timestamp as sort key
            'name': name,
            'email': email
        }
    )
    print(f"Added user {name}")

add_user('1', 'Melhem', 'melhem@example.com')
add_user('2', 'Sarah', 'sarah@example.com')
add_user('1', 'Melhem2', 'melhem2@example.com')  # Same user_id, different sort key

# ----------------------------
# 4. List users sorted by email
# ----------------------------
def list_users_sorted_by_email():
    users = []
    scan = table.scan()
    users.extend(scan['Items'])

    while 'LastEvaluatedKey' in scan:
        scan = table.scan(ExclusiveStartKey=scan['LastEvaluatedKey'])
        users.extend(scan['Items'])

    users_sorted = sorted(users, key=lambda x: x['email'])
    return users_sorted

sorted_users = list_users_sorted_by_email()
print("Users sorted by email:")
for user in sorted_users:
    print(user)
