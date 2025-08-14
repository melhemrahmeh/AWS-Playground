import requests
import json
import uuid

# Replace this with your deployed API URL
API_URL = "https://ubwwfaec84.execute-api.us-east-1.amazonaws.com/prod"

def pretty_print(title, response):
    print(f"\n=== {title} ===")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)

def run_tests():
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    task_data = {"id": task_id, "title": "Learn AWS Lambda", "status": "pending"}

    # Create (POST)
    r = requests.post(f"{API_URL}/tasks", json=task_data)
    pretty_print("CREATE", r)

    # Read (GET)
    r = requests.get(f"{API_URL}/tasks/{task_id}")
    pretty_print("READ", r)

    # Update (PUT)
    updated_data = {"title": "Learn AWS Lambda + API Gateway", "status": "done"}
    r = requests.put(f"{API_URL}/tasks/{task_id}", json=updated_data)
    pretty_print("UPDATE", r)

    # Delete (DELETE)
    r = requests.delete(f"{API_URL}/tasks/{task_id}")
    pretty_print("DELETE", r)

    # Confirm deletion
    r = requests.get(f"{API_URL}/tasks/{task_id}")
    pretty_print("CONFIRM DELETION", r)

if __name__ == "__main__":
    run_tests()
