"""
Utility script to display the results of the last ExecutionAgent run for a specific project.

This script shows:
- The latest generated Dockerfile
- The latest installation script
- The success/failure status of the execution

Usage:
    python show_results.py <project_name>
    
Example:
    python show_results.py pytest
"""

import os
import sys


def get_highest_numbered_file(directory: str, prefix: str) -> str | None:
    """
    Get the file with the highest number suffix for a given prefix.
    
    Files are expected to follow the pattern: {prefix}{number}
    
    Args:
        directory: Directory to search in
        prefix: File name prefix to match (e.g., "Dockerfile_")
        
    Returns:
        The filename with the highest number suffix, or None if no matching files found
        
    Example:
        >>> get_highest_numbered_file("/path/to/dir", "Dockerfile_")
        "Dockerfile_3"  # If Dockerfile_1, Dockerfile_2, Dockerfile_3 exist
    """
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f[len(prefix):].isdigit()]
    if not files:
        return None
    highest_file = max(files, key=lambda x: int(x[len(prefix):]))
    return highest_file


def main():
    """
    Main function to display ExecutionAgent results for a project.
    
    Reads the last experiment from experiments_list.txt and displays
    the generated files and execution status.
    """
    if len(sys.argv) != 2:
        print("Usage: python show_results.py <project_name>")
        sys.exit(1)

    project_name = sys.argv[1]

    # Read the last line of experiments_list.txt to get the latest experiment number
    experiments_file = "experimental_setups/experiments_list.txt"
    if not os.path.exists(experiments_file):
        print(f"Error: {experiments_file} does not exist.")
        sys.exit(1)

    with open(experiments_file, 'r') as f:
        lines = f.readlines()
        if not lines:
            print(f"Error: {experiments_file} is empty.")
            sys.exit(1)
        last_line = lines[-1].strip()

    # Build the files directory path
    files_dir = f"experimental_setups/{last_line}/files/{project_name}"
    if not os.path.exists(files_dir):
        print(f"Error: {files_dir} does not exist.")
        sys.exit(1)

    # Get and display the highest-numbered Dockerfile
    dockerfile = get_highest_numbered_file(files_dir, "Dockerfile_")
    if dockerfile:
        dockerfile_path = os.path.join(files_dir, dockerfile)
        print("=" * 70)
        print(f"Latest Dockerfile: {dockerfile_path}")
        print("=" * 70)
        with open(dockerfile_path, 'r') as f:
            print(f.read())
    else:
        print("No Dockerfile found.")

    # Get and display the highest-numbered SETUP_AND_INSTALL.sh
    setup_file = get_highest_numbered_file(files_dir, "SETUP_AND_INSTALL.sh_")
    if setup_file:
        setup_file_path = os.path.join(files_dir, setup_file)
        print("=" * 70)
        print(f"Latest installation script: {setup_file_path}")
        print("=" * 70)
        with open(setup_file_path, 'r') as f:
            print(f.read())
    else:
        print("No SETUP_AND_INSTALL.sh file found.")

    # Check for SUCCESS file to determine execution status
    success_file = f"experimental_setups/{last_line}/saved_contexts/{project_name}/SUCCESS"
    print("=" * 70)
    if os.path.exists(success_file):
        print("STATUS: SUCCESS ✓")
    else:
        print("STATUS: FAILED ✗")


if __name__ == "__main__":
    main()
