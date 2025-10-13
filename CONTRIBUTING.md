# Contributing to ExecutionAgent

Thank you for your interest in contributing to ExecutionAgent! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

Please be respectful and constructive in all interactions. We are committed to providing a welcoming and inclusive environment for all contributors.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ExecutionAgent.git
   cd ExecutionAgent
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/majercakdavid/ExecutionAgent.git
   ```

## Development Setup

### Option 1: VSCode Dev Container (Recommended)
1. Install [VSCode](https://code.visualstudio.com/) and the [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open the project in VSCode
3. Click "Reopen in Container" when prompted
4. Set up your OpenAI API key:
   ```bash
   python3.10 setup_api_key.py
   ```

### Option 2: Local Development
1. Ensure you have Python 3.10+ installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Docker and ensure it's running
4. Set up your OpenAI API key:
   ```bash
   python3.10 setup_api_key.py
   ```

## How to Contribute

### Reporting Bugs
- Check if the bug has already been reported in [Issues](https://github.com/majercakdavid/ExecutionAgent/issues)
- If not, create a new issue with:
  - Clear, descriptive title
  - Detailed description of the problem
  - Steps to reproduce
  - Expected vs. actual behavior
  - Relevant logs from `experimental_setups/experiment_XX/`
  - Your environment (OS, Python version, Docker version)

### Suggesting Features
- Open an issue with the tag `enhancement`
- Describe the feature and its benefits
- Provide examples or mockups if applicable
- Discuss implementation approach if you have ideas

### Contributing Code

#### Types of Contributions Welcome
- **Bug fixes**: Fix reported issues
- **Features**: Add new functionality
- **Documentation**: Improve README, comments, or add examples
- **Tests**: Add or improve test coverage
- **Performance**: Optimize existing code
- **Refactoring**: Improve code quality and maintainability

#### Before You Start
1. Check existing issues and PRs to avoid duplicating work
2. For large changes, open an issue first to discuss the approach
3. Make sure you understand the codebase architecture

## Code Style Guidelines

### Python Code
- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Maximum line length: 88 characters (Black formatter default)
- Use type hints where appropriate
- Write docstrings for functions and classes

**Example:**
```python
def process_repository(repo_url: str, cycles: int = 40) -> dict:
    """
    Process a GitHub repository by building and testing it.
    
    Args:
        repo_url: The GitHub repository URL
        cycles: Maximum number of action cycles (default: 40)
        
    Returns:
        Dictionary containing build and test results
    """
    # Implementation here
    pass
```

### Code Comments
- Add comments for complex logic
- Keep comments up-to-date with code changes
- Use clear, concise language
- Avoid obvious comments

### Shell Scripts
- Use clear variable names
- Add comments for non-obvious operations
- Follow consistent indentation (2 or 4 spaces)
- Include error handling

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=autogpt tests/
```

### Writing Tests
- Write tests for new features and bug fixes
- Ensure tests are reproducible and isolated
- Use descriptive test names
- Follow existing test structure in the `tests/` directory

**Example:**
```python
def test_repository_cloning():
    """Test that repository cloning works correctly."""
    # Test implementation
    pass
```

## Submitting Changes

### Creating a Pull Request

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes**:
   - Follow the code style guidelines
   - Add tests if applicable
   - Update documentation as needed

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add clear, descriptive commit message"
   ```
   
   **Commit message guidelines:**
   - Use present tense: "Add feature" not "Added feature"
   - Be specific and descriptive
   - Reference issue numbers when applicable: "Fix #123"

4. **Keep your branch up-to-date**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**:
   - Go to the [repository](https://github.com/majercakdavid/ExecutionAgent)
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template with:
     - Clear description of changes
     - Related issue numbers
     - Testing performed
     - Any breaking changes

### Pull Request Review Process
- Maintainers will review your PR
- Address any requested changes
- Once approved, your PR will be merged
- Celebrate! 🎉

## Development Tips

### Useful Commands
```bash
# Clean all logs and results
./clean.sh

# View results for a specific project
python3.10 show_results.py <project_name>

# Run ExecutionAgent on a test repository
./ExecutionAgent.sh --repo https://github.com/test/repo -l 30
```

### Debugging
- Check logs in `experimental_setups/experiment_XX/logs/`
- Review generated files in `experimental_setups/experiment_XX/files/`
- Use saved contexts in `experimental_setups/experiment_XX/saved_contexts/`

### Directory Structure
```
ExecutionAgent/
├── autogpt/           # Main agent code
├── scripts/           # Helper scripts
├── experimental_setups/  # Execution logs and results
├── tests/            # Test files
├── requirements.txt  # Python dependencies
└── README.md        # Main documentation
```

## Questions?

If you have questions about contributing:
- Check existing documentation
- Search [closed issues](https://github.com/majercakdavid/ExecutionAgent/issues?q=is%3Aissue+is%3Aclosed)
- Open a new issue with the `question` tag
- Email: [fi_bouzenia@esi.dz](mailto:fi_bouzenia@esi.dz)

## Recognition

All contributors will be recognized in the project. Thank you for helping make ExecutionAgent better!
