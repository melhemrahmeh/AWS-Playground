import subprocess

# Name of your CDK stack
STACK_NAME = "ResourceStack"

def destroy_stack(stack_name):
    try:
        print(f"Destroying CDK stack: {stack_name} ...")
        result = subprocess.run(
            ["cdk", "destroy", stack_name, "--force"],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("Stack destroyed successfully!")
    except subprocess.CalledProcessError as e:
        print("Error destroying stack:")
        print(e.stderr)

if __name__ == "__main__":
    destroy_stack(STACK_NAME)
