import sys
import argparse
import subprocess
import os

def run_task(cmd):
    print(f"--- Running: {' '.join(cmd)} ---")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing task: {e}")
        sys.exit(1)

def fetch_and_sync():
    """Triggers the Ingestion Microservice."""
    run_task(["python", "microservices/ingestion/run.py"])

def train():
    """Triggers the Model Training Microservice."""
    run_task(["python", "microservices/model_training/train.py"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill-Ex Orchestrator")
    parser.add_argument("task", choices=["fetch-and-sync", "train"], help="Task to execute")
    
    args = parser.parse_args()
    
    # Ensure we are in the project root
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    if args.task == "fetch-and-sync":
        fetch_and_sync()
    elif args.task == "train":
        train()
