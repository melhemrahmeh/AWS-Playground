import json
import boto3
import psycopg2
import os

def get_db_credentials():
    client = boto3.client("secretsmanager")
    secret = json.loads(client.get_secret_value(SecretId=os.environ["DB_SECRET"])["SecretString"])
    return secret

def init_db():
    creds = get_db_credentials()
    conn = psycopg2.connect(
        host=creds["host"],
        database=os.environ.get("DB_NAME", "postgres"),
        user=creds["username"],
        password=creds["password"],
        port=os.environ.get("DB_PORT", "5432")
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            description TEXT NOT NULL,
            status TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def lambda_handler(event, context):
    init_db()

    creds = get_db_credentials()
    conn = psycopg2.connect(
        host=creds["host"],
        database=os.environ.get("DB_NAME", "postgres"),
        user=creds["username"],
        password=creds["password"],
        port=os.environ.get("DB_PORT", "5432")
    )
    cur = conn.cursor()

    method = event.get("httpMethod")

    if method == "GET":
        cur.execute("SELECT * FROM tasks;")
        rows = cur.fetchall()
        result = [{"id": r[0], "description": r[1], "status": r[2]} for r in rows]
        cur.close()
        conn.close()
        return {"statusCode": 200, "body": json.dumps(result)}

    elif method == "POST":
        body = json.loads(event.get("body", "{}"))
        cur.execute("INSERT INTO tasks (description, status) VALUES (%s, %s);",
                    (body["description"], body.get("status", "pending")))
        conn.commit()
        cur.close()
        conn.close()
        return {"statusCode": 201, "body": json.dumps({"message": "Task created"})}

    elif method == "PUT":
        task_id = event["pathParameters"]["id"]
        body = json.loads(event.get("body", "{}"))
        cur.execute("UPDATE tasks SET status=%s WHERE id=%s;", (body["status"], task_id))
        conn.commit()
        cur.close()
        conn.close()
        return {"statusCode": 200, "body": json.dumps({"message": "Task updated"})}

    elif method == "DELETE":
        task_id = event["pathParameters"]["id"]
        cur.execute("DELETE FROM tasks WHERE id=%s;", (task_id,))
        conn.commit()
        cur.close()
        conn.close()
        return {"statusCode": 200, "body": json.dumps({"message": "Task deleted"})}

    cur.close()
    conn.close()
    return {"statusCode": 400, "body": json.dumps({"error": "Bad request"})}
