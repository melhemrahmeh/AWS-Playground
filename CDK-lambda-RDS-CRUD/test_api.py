import requests
import json

# Replace with your actual API Gateway endpoint (no trailing slash)
API_URL = "https://test-api.execute-api.us-east-1.amazonaws.com/prod/tasks"

def create_task(title, description):
    payload = {
        "action": "create",
        "title": title,
        "description": description
    }
    r = requests.post(API_URL, json=payload)
    print("Create Task Response:", r.status_code, r.text)

def get_task(task_id):
    payload = {
        "action": "read",
        "task_id": task_id
    }
    r = requests.post(API_URL, json=payload)
    print("Get Task Response:", r.status_code, r.text)

def update_task(task_id, title, description):
    payload = {
        "action": "update",
        "task_id": task_id,
        "title": title,
        "description": description
    }
    r = requests.post(API_URL, json=payload)
    print("Update Task Response:", r.status_code, r.text)

def delete_task(task_id):
    payload = {
        "action": "delete",
        "task_id": task_id
    }
    r = requests.post(API_URL, json=payload)
    print("Delete Task Response:", r.status_code, r.text)

if __name__ == "__main__":
    # Test the flow
    create_task("Buy milk", "Remember to get almond milk.")
    get_task(1)   # adjust ID based on your DB data
    update_task(1, "Buy bread", "Whole grain bread.")
    delete_task(1)
