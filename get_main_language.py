"""
Utility module for detecting the primary programming language of a GitHub repository.

This module uses the GitHub API to fetch language statistics for a repository
and determines the primary language based on the number of bytes of code.
"""

import requests


def get_repo_languages(owner: str, repo: str) -> None:
    """
    Fetch and print the primary programming language of a GitHub repository.
    
    The primary language is determined by the largest byte count among all
    languages used in the repository. The function prints the result to stdout
    rather than returning it, making it suitable for use in shell scripts.
    
    Args:
        owner: GitHub repository owner (username or organization)
        repo: Repository name
        
    Returns:
        None. Prints the primary language name to stdout.
        
    Example:
        >>> get_repo_languages("pytest-dev", "pytest")
        Python
        
    Note:
        This function prints to stdout for integration with shell scripts.
        To capture the output programmatically, use subprocess or similar.
    """
    # GitHub API URL for languages of a repository
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"

    try:
        # Send a GET request to the GitHub API
        response = requests.get(url)

        # Check for successful response
        if response.status_code == 200:
            languages = response.json()
            if languages:
                # Sort languages by byte size (largest first) and get the primary language
                primary_language = max(languages, key=languages.get)
                print(f"{primary_language}")
                # Uncomment to see all languages with their byte usage:
                # print("All languages with byte usage:")
                # for lang, bytes_used in languages.items():
                #     print(f"- {lang}: {bytes_used} bytes")
            else:
                print("No languages detected for this repository.")
        else:
            print(f"Failed to fetch languages: {response.status_code} {response.reason}")
    except requests.RequestException as e:
        print(f"Error during request: {e}")


# Example usage
# Replace 'owner' and 'repo' with the repository's owner and name
owner = "pytest-dev"
repo = "pytest"
get_repo_languages(owner, repo)