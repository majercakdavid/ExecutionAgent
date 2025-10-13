"""Commands to search the web with"""

from __future__ import annotations

COMMAND_CATEGORY = "web_search"
COMMAND_CATEGORY_TITLE = "Web Search"

import json
import time
from itertools import islice
import os
import subprocess

from duckduckgo_search import DDGS

from autogpt.agents.agent import Agent
from autogpt.command_decorator import command

DUCKDUCKGO_MAX_ATTEMPTS = 3

@command(
    "search_docker_image",
    "Search for docker images on docker hub",
    {
        "search_term": {
            "type": "string",
            "description": "the search terms",
            "required": True,
        }
    },
)
def search_docker_image(search_term: str, agent):
    """
    Searches for a Docker image using the specified search term.

    Args:
    - search_term (str): The term to search for Docker images.

    Returns:
    - str: The output from the Docker search command.
    """
    # Prepare the Docker search command
    command = ["docker", "search", search_term]

    # Execute the command and capture the output
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Check for errors
    if result.returncode != 0:
        raise Exception(f"Error executing docker search: {result.stderr}")

    # Return the output
    return result.stdout

@command(
    "web_search",
    "Searches the web",
    {
        "query": {
            "type": "string",
            "description": "The search query",
            "required": True,
        }
    },
    aliases=["search"],
)
def web_search(query: str, agent: Agent, num_results: int = 8) -> str:
    """Return the results of a Google search

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The results of the search.
    """
    search_results = []
    attempts = 0

    while attempts < DUCKDUCKGO_MAX_ATTEMPTS:
        if not query:
            return json.dumps(search_results)

        results = DDGS().text(query)
        search_results = list(islice(results, num_results))

        if search_results:
            break

        time.sleep(1)
        attempts += 1

    results = json.dumps(search_results, ensure_ascii=False, indent=4)
    return safe_google_results(results)


@command(
    "google",
    "Google Search",
    {
        "query": {
            "type": "string",
            "description": "The search query",
            "required": True,
        }
    },
    lambda config: bool(config.google_api_key)
    and bool(config.google_custom_search_engine_id),
    "Configure google_api_key and custom_search_engine_id.",
    aliases=["search"],
)
def google(query: str, agent: Agent, num_results: int = 8) -> str | list[str]:
    """Return the results of a Google search using the official Google API

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The results of the search.
    """

    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    try:
        # Get the Google API key and Custom Search Engine ID from the config file
        api_key = agent.config.google_api_key
        custom_search_engine_id = agent.config.google_custom_search_engine_id

        # Initialize the Custom Search API service
        service = build("customsearch", "v1", developerKey=api_key)

        # Send the search query and retrieve the results
        result = (
            service.cse()
            .list(q=query, cx=custom_search_engine_id, num=num_results)
            .execute()
        )

        # Extract the search result items from the response
        search_results = result.get("items", [])

        # Create a list of only the URLs from the search results
        search_results_links = [item["link"] for item in search_results]

    except HttpError as e:
        # Handle errors in the API call
        error_details = json.loads(e.content.decode())

        # Check if the error is related to an invalid or missing API key
        if error_details.get("error", {}).get(
            "code"
        ) == 403 and "invalid API key" in error_details.get("error", {}).get(
            "message", ""
        ):
            return "Error: The provided Google API key is invalid or missing."
        else:
            return f"Error: {e}"
    # google_result can be a list or a string depending on the search results

    # Return the list of search result URLs
    return safe_google_results(search_results_links)


def safe_google_results(results: str | list) -> str:
    """
        Return the results of a Google search in a safe format.

    Args:
        results (str | list): The search results.

    Returns:
        str: The results of the search.
    """
    if isinstance(results, list):
        safe_message = json.dumps(
            [result.encode("utf-8", "ignore").decode("utf-8") for result in results]
        )
    else:
        safe_message = results.encode("utf-8", "ignore").decode("utf-8")
    return safe_message


@command(
    "search_github_repos",
    "Search GitHub for similar repositories",
    {
        "query": {
            "type": "string",
            "description": "Search query for GitHub repositories (e.g., 'autonomous agents', 'build automation')",
            "required": True,
        },
        "num_results": {
            "type": "integer",
            "description": "Number of results to return (default: 10)",
            "required": False,
        }
    },
)
def search_github_repos(query: str, agent: Agent, num_results: int = 10) -> str:
    """Search GitHub for repositories matching the query
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return (default: 10)
        
    Returns:
        str: JSON string containing repository information
    """
    import requests
    
    # GitHub API endpoint for repository search
    url = "https://api.github.com/search/repositories"
    
    # Parameters for the search
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(num_results, 100)  # GitHub API max is 100
    }
    
    try:
        # Send request to GitHub API
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            repos = []
            
            for item in data.get("items", [])[:num_results]:
                repo_info = {
                    "name": item.get("name"),
                    "full_name": item.get("full_name"),
                    "description": item.get("description"),
                    "url": item.get("html_url"),
                    "stars": item.get("stargazers_count"),
                    "language": item.get("language"),
                    "forks": item.get("forks_count"),
                    "topics": item.get("topics", []),
                    "updated_at": item.get("updated_at"),
                }
                repos.append(repo_info)
            
            return json.dumps(repos, indent=2, ensure_ascii=False)
        else:
            return json.dumps({
                "error": f"GitHub API request failed with status code {response.status_code}",
                "message": response.text
            })
    except requests.RequestException as e:
        return json.dumps({
            "error": "Request failed",
            "message": str(e)
        })
