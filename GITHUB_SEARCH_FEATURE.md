# GitHub Repository Search Feature

## Overview
This feature allows ExecutionAgent to search GitHub for similar repositories, helping users discover related automation tools, CI/CD systems, and agent-based solutions.

## Implementation

### 1. Agent Command: `search_github_repos`
Added to `autogpt/commands/web_search.py`, this command can be called by the ExecutionAgent during execution to search GitHub repositories.

**Usage within the agent:**
```python
search_github_repos(query="autonomous agent build automation", num_results=10)
```

**Returns:** JSON string containing repository information including:
- Repository name and full name
- Description
- URL
- Star count
- Primary language
- Fork count
- Topics
- Last update date

### 2. Standalone Script: `search_similar_repositories.py`
A user-friendly command-line script for searching GitHub repositories outside of the agent context.

**Usage examples:**

Basic search:
```bash
python search_similar_repositories.py
```

Custom number of results:
```bash
python search_similar_repositories.py -n 20
```

With additional keywords:
```bash
python search_similar_repositories.py -k "continuous integration" "docker"
```

Save results to file:
```bash
python search_similar_repositories.py -o results.json
```

## Example Output

When the script runs successfully (requires network access to GitHub API), it produces output like:

```
Searching GitHub for: autonomous agent build automation testing
------------------------------------------------------------

Found 15234 repositories
Showing top 10 results:

1. microsoft/autogen
   ⭐ Stars: 25,432 | 🍴 Forks: 3,456
   💻 Language: Python
   🔗 URL: https://github.com/microsoft/autogen
   🏷️  Topics: ai, automation, agents, llm, gpt
   📝 Enable Next-Gen Large Language Model Applications. Join our Discord: https://discord.gg/autogen...

2. Significant-Gravitas/AutoGPT
   ⭐ Stars: 164,221 | 🍴 Forks: 43,765
   💻 Language: Python
   🔗 URL: https://github.com/Significant-Gravitas/AutoGPT
   🏷️  Topics: ai, autonomous-agents, gpt-4, python
   📝 AutoGPT is the vision of accessible AI for everyone, to use and to build on...

[... more results ...]
```

## Technical Details

### GitHub API Integration
- Uses GitHub REST API v3 search endpoint
- Searches repositories with query string
- Sorts by star count (popularity)
- Returns up to 100 results per request (GitHub API limit)
- Handles rate limiting gracefully

### Error Handling
- Network connectivity issues
- GitHub API rate limits
- Invalid queries
- Empty results

### Features
- Configurable result count
- Custom keyword search
- JSON output for programmatic use
- Formatted console output for human readability
- Topics/tags support

## Use Cases

1. **Research**: Discover similar automation tools and frameworks
2. **Comparison**: Find alternative solutions for build automation
3. **Integration**: Identify potential tools to integrate with ExecutionAgent
4. **Learning**: Study how other projects approach similar problems
5. **Benchmarking**: Find repositories to test against ExecutionAgent

## Future Enhancements

Potential improvements for this feature:
- GitHub personal access token support for higher rate limits
- Filter by language, stars, or activity
- Advanced search operators (e.g., "stars:>1000")
- Cache results to reduce API calls
- Integration with other code hosting platforms (GitLab, Bitbucket)
- Similarity scoring based on repository metadata and topics
