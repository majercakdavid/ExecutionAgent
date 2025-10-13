#!/bin/bash
#
# ExecutionAgent Main Script
# 
# This script is the primary entry point for ExecutionAgent. It handles both single
# repository and batch file modes, manages retries, and orchestrates the entire
# build and test workflow.
#
# Usage:
#   Single repository mode:
#     ./ExecutionAgent.sh --repo <github_repo_url> -l <num_cycles>
#
#   Batch file mode:
#     ./ExecutionAgent.sh /path/to/batch_file.txt -l <num_cycles>
#
# Options:
#   --repo    : GitHub repository URL to process
#   -l        : Number of action cycles per attempt (default: 40)
#
# Examples:
#   ./ExecutionAgent.sh --repo https://github.com/pytest-dev/pytest -l 50
#   ./ExecutionAgent.sh projects.txt -l 60
#

# Default number of action cycles per attempt
num=40

# Function to extract project name from GitHub URL
# Extracts the last component of the URL, which is usually the project name
# Args:
#   $1 - GitHub repository URL
# Returns:
#   Project name (e.g., "pytest" from "https://github.com/pytest-dev/pytest")
extract_project_name() {
  local url="$1"
  echo "$url" | awk -F '/' '{print $(NF)}'
}

# Function to run the command and handle retries with learning
# This implements the retry logic where each attempt learns from previous failures
# Args:
#   $1 - Command to execute
#   $2 - Project name
# Returns:
#   None (exits on success or user abort)
run_with_retries() {
  local command="$1"
  local project_name="$2"
  local max_retries=2  # Total attempts will be max_retries + 1 = 3
  local attempt=1

  # Automatic retry loop (3 attempts by default)
  while [[ $attempt -le $max_retries ]]; do
    echo "======================================================================"
    echo "STARTING ITERATION $attempt:"
    echo "PROJECT: $project_name"
    echo "======================================================================"

    # Execute the build/test command
    eval "$command"
    
    # Check if the attempt succeeded
    result=$(python3.10 post_process.py "$project_name")

    if [[ "$result" == "SUCCESS" ]]; then
      echo "Post-process succeeded."
      return
    fi

    echo "Attempt $attempt failed with FAILURE. Retrying..."
    ((attempt++))
  done

  # Interactive retry loop - prompts user after automatic retries exhausted
  while true; do
    echo "======================================================================"
    echo "PROMPTING USER FOR ADDITIONAL RETRY:"
    echo "PROJECT: $project_name"
    echo "======================================================================"

    read -p "Post-process failed after $max_retries attempts. Do you want to retry again? (yes/no): " user_input
    case "$user_input" in
      [Yy]* ) 
        eval "$command"
        result=$(python3.10 post_process.py "$project_name")
        if [[ "$result" == "SUCCESS" ]]; then
          echo "Post-process succeeded."
          return
        fi
        ;;
      [Nn]* ) 
        echo "Exiting retry loop."
        break
        ;;
      * ) 
        echo "Please answer yes or no."
        ;;
    esac
  done
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo_url="$2"
      shift 2
      ;;
    -l)
      num="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# Initialize ExecutionAgent environment
python3.10 setup_api_key.py                           # Sets up OpenAI API key
python3.10 experimental_setups/increment_experiment.py  # Creates new experiment directory
python3.10 prepare_ai_settings.py                      # Prepares AI configuration

# Handle single repository mode (--repo argument provided)
if [[ -n "$repo_url" ]]; then
  # Validate that a URL was actually provided
  if [[ -z "$repo_url" ]]; then
    echo "Error: --repo argument requires a GitHub URL."
    echo "Usage: ./ExecutionAgent.sh --repo <github_repo_url> -l <num_cycles>"
    exit 1
  fi

  # Extract the project name from the GitHub URL
  project_name=$(extract_project_name "$repo_url")

  # Detect the primary programming language of the repository
  primary_language=$(python3.10 get_main_language.py "$repo_url")
  echo "Primary language: $primary_language"

  # Display processing information
  echo "Processing project: $project_name"
  echo "Repository URL: $repo_url"

  # Initialize Docker configuration
  echo "{}" > ~/.docker/config.json

  # Clone repository and set up metadata
  python3.10 clone_and_set_metadata.py "$project_name" "$repo_url" "$primary_language"

  # Run ExecutionAgent with retries
  run_with_retries "./run.sh --ai-settings ai_settings.yaml -c -l \"$num\" -m json_file --experiment-file \"project_meta_data.json\"" "$project_name"

# Handle batch file mode (file path provided)
elif [[ -f "$repo_url" ]]; then
  file_path="$repo_url"
  echo "Processing batch file: $file_path"

  # Read and process each line in the batch file
  # Expected format: <project_name> <github_url> <language>
  while IFS= read -r line; do
      # Skip empty lines
      [[ -z "$line" ]] && continue
      
      # Parse line components
      project_name=$(echo "$line" | awk '{print $1}')
      github_url=$(echo "$line" | awk '{print $2}')
      language=$(echo "$line" | awk '{print $3}')

      echo "Processing project: $project_name"
      echo "Repository URL: $github_url"
      echo "Language: $language"

      # Initialize Docker configuration
      echo "{}" > ~/.docker/config.json

      # Clone repository and set up metadata
      python3.10 clone_and_set_metadata.py "$project_name" "$github_url" "$language"

      # Run ExecutionAgent with retries
      run_with_retries "./run.sh --ai-settings ai_settings.yaml -c -l \"$num\" -m json_file --experiment-file \"project_meta_data.json\"" "$project_name"
  done < "$file_path"

else
  # Handle invalid input
  echo "Error: Invalid input. Provide a batch file path or use --repo <github_repo_url>."
  echo ""
  echo "Usage:"
  echo "  Single repository: ./ExecutionAgent.sh --repo <github_repo_url> -l <num_cycles>"
  echo "  Batch file:       ./ExecutionAgent.sh /path/to/batch_file.txt -l <num_cycles>"
  echo ""
  echo "Examples:"
  echo "  ./ExecutionAgent.sh --repo https://github.com/pytest-dev/pytest -l 50"
  echo "  ./ExecutionAgent.sh projects.txt -l 60"
  exit 1
fi