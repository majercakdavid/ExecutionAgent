import os
import time
import json
import argparse
import logging
import subprocess
from tqdm import tqdm
from utils import (
    get_logger,
    load_jsonl,
    find_jsonl_files,
    write_jsonl,
    make_patch_from_prfiles,
)
from distutils.util import strtobool
import traceback

logger = get_logger(__name__)
try:
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    world_size = comm.Get_size()
except Exception as e:
    # This error is ok if running locally
    logger.error(f"Failed to import MPI: {repr(e)}")
    rank = 0
    world_size = 1
    comm = None

class SubprocessHandler:
    """
    A context-manager class that launches a subprocess, waits for a success 
    message within a specified timeout, and ensures a graceful termination.
    """
    def __init__(self, command, success_msg, timeout=10, check_output=False, **popen_kwargs):
        """
        :param command: List of command arguments or string to run as a subprocess.
        :param success_msg: The message that indicates successful startup.
        :param timeout: Maximum time (in seconds) to wait for the success message.
        :param check_output: Set to True to read lines from stderr and stdout.
        :param popen_kwargs: Additional keyword arguments to pass to subprocess.Popen.
        """
        self.command = command
        self.success_msg = success_msg
        self.timeout = timeout
        self.check_output = check_output
        self.popen_kwargs = popen_kwargs
        self.process = None

    def __enter__(self):
        # Start the subprocess
        # Note: `text=True` (or `universal_newlines=True`) to read output as text
        #       `stdout=subprocess.PIPE` or `stderr=subprocess.PIPE` to capture output
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            **self.popen_kwargs
        )
        
        # Determine which stream to read from (stdout by default, or stderr if requested)
        stream = self.process.stdout

        start_time = time.time()

        # Continuously read lines until success message or timeout
        while True:
            # Check if process has exited unexpectedly
            if self.process.poll() is not None:
                raise RuntimeError("Process ended unexpectedly before finding success message.")

            line = stream.readline() if stream else ""
            print(line, end="")
            if line:
                # Optional: print or log the line for debugging
                print(line, end="")

                if self.success_msg in line:
                    # Found the success message
                    break

            # Check for timeout
            if (time.time() - start_time) > self.timeout:
                raise TimeoutError(f"Timeout of {self.timeout} seconds exceeded "
                                   "while waiting for success message.")
            
            # Small sleep to avoid busy-waiting
            time.sleep(0.1)

        # Return self so that we can hold this context
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Ensure the subprocess is terminated gracefully
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # If not terminated in time, forcibly kill it
                self.process.kill()

        # By returning False, we do not suppress any exception.
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="Code Execution Service")
    parser.add_argument(
        "--data_dir", type=str, help="Path to the data directory", required=False
    )
    parser.add_argument(
        "--data_path", type=str, help="Path to the data directory", required=False
    )
    parser.add_argument(
        "--data_ratio", type=str, help="Ratio of data to use", required=False
    )
    parser.add_argument(
        "--valid_repos", type=str, help="Path to the patch directory", required=False
    )
    parser.add_argument(
        "--remote_server_url",
        type=str,
        help="Remote server URL to connect to",
        required=False,
    )
    parser.add_argument(
        "--remote_server_auth_url",
        type=str,
        help="Remote server authentication URL",
        required=False,
    )
    parser.add_argument(
        "--output_dir", type=str, help="Path to the output directory", required=False
    )
    return parser.parse_args()

def get_repo_language(repo_name):
    import requests
    # GitHub API URL
    url = f"https://api.github.com/repos/{repo_name}/languages"

    # Send GET request to the URL
    response = requests.get(url)

    # Check if the response is successful
    if response.status_code == 200:
        # Parse JSON response
        languages = response.json()
        
        # Find the language with the maximum value
        most_used_language = max(languages, key=languages.get)
        
        # Output the result
        print(most_used_language)
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")


def write_project_meta_data_file(repo_name, repo_version=None):
    project_meta_data_file = {
        "repetition_handling": "RESTRICT",
        "project_path": repo_name.replace("/", "__"),
        "project_url": f"https://github.com/{repo_name}",
        "budget_control": {
            "name": "NO-TRACK"
        },
        "language": get_repo_language(repo_name),
        "image": "NIL",
        "repo_name": repo_name,
        "repo_version": "NIL" if repo_version is None else repo_version,
        "workflow_content": "jobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n    - name: Checkout\n      uses: actions/checkout@v3\n    - name: Run Tests\n      run: echo \"Done\"\n",
        "keep_container": "FALSE"
    }
    os.makedirs(f"experimental_setups/files/{repo_name.replace('/', '__')}", exist_ok=True)
    with open("project_meta_data.json", "w") as f:
        json.dump(project_meta_data_file, f)
        
def get_highest_numbered_file(directory, prefix):
    """Get the file with the highest number at the end of its name for a given prefix."""
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f[len(prefix):].isdigit()]
    if not files:
        return None
    highest_file = max(files, key=lambda x: int(x[len(prefix):]))
    return highest_file

def write_data(data, output_dir, instance_id, separate_errors=False):
    os.makedirs(output_dir, exist_ok=True)
    if separate_errors:
        with open(os.path.join(output_dir, f"data_{rank}.jsonl"), "a+") as f_data, open(
            os.path.join(output_dir, f"errors_{rank}.jsonl"), "a+"
        ) as f_error:
            if "error" in data:
                f_error.write(json.dumps(data) + "\n")
                f_error.flush()
            else:
                f_data.write(json.dumps(data) + "\n")
                f_data.flush()
    else:
        if not os.path.exists(os.path.join(output_dir, instance_id)):
            os.makedirs(os.path.join(output_dir, instance_id), exist_ok=True)

        with open(
            os.path.join(output_dir, instance_id, WORKFLOW_TESTS_FILE),
            "a+",
        ) as f_data:
            f_data.write(json.dumps(data) + "\n")
            f_data.flush()


def main():
    args = parse_args()

    if args.data_path:
        args.data_path = os.path.join(args.data_dir, args.data_path)
    else:
        args.data_path = args.data_dir

    if args.valid_repos:
        data = args.valid_repos.split(",")
    elif args.meta_path:
        data = []
        for jsonl_file in find_jsonl_files(args.meta_path):
            logger.info(f"Loading metadata from: {jsonl_file}")
            jsonl_file_meta = load_jsonl(os.path.join(args.meta_path, jsonl_file))
            data.extend([sample["instance_id"] for sample in jsonl_file_meta])
    else:
        data = list(sorted(os.listdir(args.data_path)))
        logger.warning(f"Loading data from: {args.data_path}, data: {data}")

    # if comm is None:
    #     data = [
    #         # "twpayne__chezmoi-3258",
    #         # "sul-dlss__libsys-airflow-1044",
    #         # "42organization__42gg.server.dev.v2-693-mod",
    #         # "huggingface__diffusers-6465",
    #         "Blueprints-org__blueprints-211",
    #         # "GU-99__grow-up-pms-154",
    #         "Bearer__bearer-1010",
    #     ]  # , "zarf-dev__zarf-1989"] #, "sul-dlss__libsys-airflow-1082", "marimo-team__marimo-1939"]

    if args.data_ratio:
        logger.warning(f"Data ratio: {args.data_ratio}, data length: {len(data)}")
        min_bound, max_bound = [
            float(bound) / 100 for bound in args.data_ratio.split(":")
        ]
        data = data[int(min_bound * len(data)) : int(max_bound * len(data))]
        logger.warning(f"Data length after filtering: {len(data)}")
    logger.warning(f"Total number of items: {len(data)}")

    for k, v in os.environ.items():
        logger.warning(f"ENVIRONMENT VAR: {k}={v}")

    stats = {
        "total": 0,
        "all_workflow_all_tests": 0,
        "all_workflow_one_test": 0,
        "one_workflow_one_test": 0,
        "no_workflow": 0,
        "failed": 0,
    }
    logger.info(
        "Starting to process data. Number of items: {}".format(
            len(data)
        )
    )

    # Uniform distribution
    # per_rank_data_count = len(data) // world_size
    # start_index = rank * per_rank_data_count
    # end_index = (
    #     start_index + per_rank_data_count if rank != world_size - 1 else len(data)
    # )
    # local_data = data[start_index:end_index]

    # Round robin distribution
    local_data = [data[i] for i in range(rank, len(data), world_size)]
    logger.warning(f"Rank: {rank}, Data count: {len(local_data)}")

    for instance_id in tqdm(local_data, desc="Processing data"):
        if os.path.exists(
            os.path.join(args.output_dir, instance_id, f"workflow_tests.jsonl")
        ):
            logger.warning(
                f"Removing existing file: {os.path.join(args.output_dir, instance_id, f'workflow_tests.jsonl')}"
            )
            os.remove(
                os.path.join(args.output_dir, instance_id, f"workflow_tests.jsonl")
            )

        if not os.path.exists(
            os.path.join(args.data_path, instance_id, WORKFLOW_INFO_FILE)
        ):
            logger.warning(
                f'Instance id: {instance_id}, missing "{WORKFLOW_INFO_FILE}", path: {os.path.join(args.data_path, instance_id, WORKFLOW_INFO_FILE)}, using latest repo version'
            )
            write_project_meta_data_file(instance_id)
            subprocess.call(f"/bin/bash ExecutionAgent.sh --repo https://github.com/{instance_id} -l 25", shell=True)
            files_dir = f"experimental_setups/files/{instance_id.replace('/', '__')}"
            setup_file = get_highest_numbered_file(files_dir, "SETUP_AND_INSTALL.sh_")
            if setup_file:
                setup_file_path = os.path.join(files_dir, setup_file)
                print("="*70)
                print(f"Latest installation script SETUP_AND_INSTALL.sh: {setup_file_path}")
                print("="*70)
                with open(setup_file_path, 'r') as f:
                    print(f.read())
            else:
                print("No SETUP_AND_INSTALL.sh file found.")
                
            os.makedirs(
                os.path.join(args.output_dir, instance_id.replace('/', '__')), exist_ok=True
            )
            subprocess.call(f"cp -r experimental_setups/files/{instance_id.replace('/', '__')} {os.path.join(args.output_dir, instance_id.replace('/', '__'))}", shell=True)
            continue


if __name__ == "__main__":
    proxy = None
    
    with SubprocessHandler(["python", "proxy.py"], "Uvicorn running on http://localhost:5555", timeout=60, check_output=True) as proxy:
        main()
