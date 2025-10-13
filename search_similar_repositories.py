#!/usr/bin/env python3
"""
Script to search GitHub for repositories similar to ExecutionAgent.
This script uses the GitHub API to find repositories with similar functionality.
"""

import json
import requests
import sys

def search_similar_repositories(keywords=None, num_results=10):
    """
    Search GitHub for repositories similar to ExecutionAgent.
    
    Args:
        keywords (list): Additional keywords to include in search
        num_results (int): Number of results to return (default: 10)
        
    Returns:
        list: List of repository information dictionaries
    """
    # Default search terms based on ExecutionAgent's features
    base_query = "autonomous agent build automation testing"
    
    if keywords:
        query = base_query + " " + " ".join(keywords)
    else:
        query = base_query
    
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
        print(f"Searching GitHub for: {query}")
        print("-" * 60)
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            total_count = data.get('total_count', 0)
            repos = []
            
            print(f"\nFound {total_count} repositories")
            print(f"Showing top {num_results} results:\n")
            
            for idx, item in enumerate(data.get("items", [])[:num_results], 1):
                repo_info = {
                    "name": item.get("name"),
                    "full_name": item.get("full_name"),
                    "description": item.get("description", "No description available"),
                    "url": item.get("html_url"),
                    "stars": item.get("stargazers_count"),
                    "language": item.get("language", "Not specified"),
                    "forks": item.get("forks_count"),
                    "topics": item.get("topics", []),
                    "updated_at": item.get("updated_at"),
                }
                repos.append(repo_info)
                
                # Print formatted output
                print(f"{idx}. {repo_info['full_name']}")
                print(f"   ⭐ Stars: {repo_info['stars']:,} | 🍴 Forks: {repo_info['forks']:,}")
                print(f"   💻 Language: {repo_info['language']}")
                print(f"   🔗 URL: {repo_info['url']}")
                if repo_info['topics']:
                    print(f"   🏷️  Topics: {', '.join(repo_info['topics'][:5])}")
                desc = repo_info['description']
                if desc and len(desc) > 100:
                    desc = desc[:97] + "..."
                print(f"   📝 {desc}")
                print()
            
            return repos
        else:
            error_msg = f"GitHub API request failed with status code {response.status_code}"
            if response.status_code == 403:
                print(f"Error: {error_msg}")
                print("This might be due to rate limiting or network restrictions.")
                print("Try again later or use a GitHub personal access token.")
            else:
                print(f"Error: {error_msg}")
                print(f"Message: {response.text}")
            return []
            
    except requests.RequestException as e:
        print(f"Error: Request failed - {str(e)}")
        return []

def save_results_to_file(repos, filename="similar_repositories.json"):
    """Save search results to a JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(repos, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {filename}")
    except Exception as e:
        print(f"Error saving results: {str(e)}")

def main():
    """Main function to run the search"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Search GitHub for repositories similar to ExecutionAgent"
    )
    parser.add_argument(
        "-n", "--num-results",
        type=int,
        default=10,
        help="Number of results to return (default: 10)"
    )
    parser.add_argument(
        "-k", "--keywords",
        nargs="+",
        help="Additional keywords to include in search"
    )
    parser.add_argument(
        "-o", "--output",
        help="Save results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Search for similar repositories
    repos = search_similar_repositories(
        keywords=args.keywords,
        num_results=args.num_results
    )
    
    # Save results if output file specified
    if args.output and repos:
        save_results_to_file(repos, args.output)
    
    return 0 if repos else 1

if __name__ == "__main__":
    sys.exit(main())
