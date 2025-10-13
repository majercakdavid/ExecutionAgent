# ExecutionAgent 🚀  
**Automate Building, Testing, and Validation of GitHub Projects in Isolated Containers**

ExecutionAgent is a powerful tool that leverages large language models (LLMs) to autonomously **clone, build, install**, and **run test cases** for projects hosted on GitHub—all within isolated containers. With support for multiple programming languages and configurations, ExecutionAgent streamlines development and quality assurance workflows.  
<div style="text-align: center;">
  <img src="execution_agent.png" alt="Alt text" width="300" height="300">
</div>

## 📚 Documentation

- **[Installation & Setup](#-installation)** - Get started quickly
- **[Usage Guide](#-how-it-works)** - Learn how to use ExecutionAgent
- **[Configuration](#-configuration)** - Customize behavior
- **[Architecture](ARCHITECTURE.md)** - Understand the system design
- **[Contributing](CONTRIBUTING.md)** - Help improve ExecutionAgent
- **[Troubleshooting](#-troubleshooting)** - Solve common issues

---

## 📋 Prerequisites

Before using ExecutionAgent, ensure you have the following installed:

- **Python 3.10+** - Required for running the agent
- **Docker** - For containerized build and test environments
- **Git** - For cloning repositories
- **OpenAI API Key** - Required for LLM interactions

### System Requirements
- Linux or macOS (recommended)
- Minimum 8GB RAM
- 20GB free disk space for Docker images and containers

---

## 🛠️ Installation

### Option 1: VSCode Dev Container (Recommended)
To get started in a VSCode Dev Container:  
1. Install the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
2. Clone this repository:
   ```bash
   git clone https://github.com/majercakdavid/ExecutionAgent.git
   cd ExecutionAgent
   ```
3. Open the repository in VSCode, and it will prompt you to reopen in the dev container
4. Set up your OpenAI API key:
   ```bash
   python3.10 setup_api_key.py
   ```

### Option 2: Local Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/majercakdavid/ExecutionAgent.git
   cd ExecutionAgent
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your OpenAI API key:
   ```bash
   python3.10 setup_api_key.py
   ```

---

## ✨ Key Features  
- **Dual Mode Execution**: Run ExecutionAgent with a batch file containing multiple projects or directly with a single GitHub repository URL
- **Autonomous Workflow**: Automatically clone, build, and test GitHub projects with minimal human intervention
- **Multi-Language Support**: Supports Python, C, C++, Java, JavaScript, and more
- **Containerized Execution**: All builds and tests run in isolated Docker containers for safety and reproducibility
- **Dev Container Integration**: Pre-configured for VSCode Dev Containers for seamless development experience
- **Learning Capability**: Agent learns from previous attempts and adjusts its strategy
- **Proven Performance** (based on evaluation of 50 projects):  
  - Build Success Rate: **80%**  
  - Test Execution Rate: **65%**  

---

## 🚀 How It Works  

ExecutionAgent uses an LLM-powered approach to understand project structure, dependencies, and build requirements. It then:
1. Analyzes the repository to detect the programming language and build system
2. Searches for relevant documentation (README, installation guides, CI workflows)
3. Creates a Dockerfile and installation scripts tailored to the project
4. Builds the project in an isolated Docker container
5. Executes the project's test suite
6. Learns from failures and retries with improved strategies

### 1️⃣ Single Repository Mode  
Process a single GitHub repository using the `--repo` option:  
```bash
./ExecutionAgent.sh --repo <github_repo_url> -l <num_cycles>
```  

**Example:**  
```bash
./ExecutionAgent.sh --repo https://github.com/pytest-dev/pytest -l 50
```  

**What happens:**
1. The project name is extracted from the URL
2. The repository's primary programming language is determined automatically
3. The repository is cloned and metadata is set up
4. ExecutionAgent launches its main loop to build the project and run test cases

**Options:**
- `-l <number>`: Sets the number of action cycles the agent can execute (default: 40)
  - Example: `-l 50` allows the agent to perform up to 50 actions

### 2️⃣ Batch File Mode  
Process multiple projects by providing a batch file listing projects in the format:  
```
<project_name> <github_url> <language>
```

**Example batch file (projects.txt):**
```plaintext
scipy https://github.com/scipy/scipy Python

pytest https://github.com/pytest-dev/pytest Python

requests https://github.com/psf/requests Python
```

**Note:** Leave one empty line after each entry.

**Run with:**
```bash
./ExecutionAgent.sh /path/to/projects.txt -l 50
```  

ExecutionAgent will process each project sequentially, performing the same steps as in single repository mode.

### 📊 View Results
To show the results of the last experiment for a specific project:
```bash
python3.10 show_results.py <project_name>
# Example:
python3.10 show_results.py pytest
```

### 🧹 Clean Up
To remove all logs, results, and unset the API token:
```bash
./clean.sh
```
**⚠️ WARNING:** This will delete ALL logs and execution results!

---

## 🔧 Configuration 

### Setting the Number of Cycles per Attempt
Use the `-l` parameter when running ExecutionAgent to control how many actions the agent can perform in each attempt (default: 40).

**Example:**
```bash
./ExecutionAgent.sh --repo https://github.com/example/project -l 60
```

### Setting the Number of Retry Attempts
By default, ExecutionAgent makes **3 attempts** (configurable as `max_retries + 1`). After each attempt, the agent learns from previous failures and adjusts its strategy.

To change the number of attempts:
1. Open `ExecutionAgent.sh`
2. Modify line 17: `local max_retries=2` to your desired value
   - Example: `local max_retries=4` will result in 5 total attempts

### Container Retention Policy
Control whether Docker containers are kept or deleted after execution:

1. Edit `customize.json`
2. Set the `keep_container` option:
   - `"FALSE"` (default): Containers are deleted after execution
   - `"TRUE"`: Containers are retained for later inspection or reuse

**Example customize.json:**
```json
{
  "keep_container": "TRUE"
}
```

**Use Case:** Keeping containers is useful when you want to:
- Inspect the build environment manually
- Debug failed builds interactively
- Reuse containers for faster subsequent runs

### OpenAI API Configuration
Set or update your OpenAI API key:
```bash
python3.10 setup_api_key.py
```

To remove the API key:
```bash
python3.10 remove_api_token.py
```

---

## 📊 Results Summary  

Based on evaluation of **50 diverse GitHub projects**:

| **Metric**              | **Success Rate** |  
|--------------------------|------------------|  
| Build Success Rate       | 80%              |  
| Test Execution Rate      | 65%              |  

**What this means:**
- **80%** of projects were successfully built from source
- **65%** of projects had their test suites successfully executed
- Results demonstrate effectiveness across various languages and build systems

All results are logged in `experimental_setups/experiment_XX`, where `XX` is an incremented experiment number for each invocation of ExecutionAgent.  

## 📁 Output Folder Structure Explanation  

The folder structure under `experimental_setups/experiment_XX` is organized to keep track of the various outputs and logs generated during the execution of the `ExecutionAgent`. Below is a breakdown of the key directories and their contents:  

- **files**: Contains files generated by the ExecutionAgent, such as `Dockerfile`, installation scripts, or any configuration files necessary for setting up the container environment.  
  - Example: `Dockerfile`, `INSTALL.sh`   

- **logs**: Stores raw logs capturing the input prompts and the corresponding outputs from the model during execution. These logs are essential for troubleshooting and understanding the behavior of the agent.  
  - Example: `cycles_list_marshmallow`, `prompt_history_marshmallow`  

- **responses**: Holds the responses generated by the model during the execution process in a structured JSON format. These responses include details about the generated build or test configurations and results.  
  - Example: `model_responses_marshmallow`  

- **saved_contexts**: Contains the saved states of the agent object at each iteration of the execution process. These snapshots are useful for debugging, tracking changes, and extracting subcomponents of the prompt across different cycles.  
  - Example: `cycle_1`, `cycle_10`, etc.  


---

## 🐛 Troubleshooting

### Common Issues

#### API Key Not Set
**Problem:** Error message about missing OpenAI API key  
**Solution:** 
```bash
python3.10 setup_api_key.py
```

#### Docker Permission Errors
**Problem:** Permission denied when accessing Docker  
**Solution:** Add your user to the docker group:
```bash
sudo usermod -aG docker $USER
# Log out and log back in for changes to take effect
```

#### Build Failures
**Problem:** Agent fails to build a project  
**Solutions:**
- Check the logs in `experimental_setups/experiment_XX/logs/`
- Review the generated Dockerfile in `experimental_setups/experiment_XX/files/`
- Try increasing the number of cycles with `-l 60` or higher
- The agent learns from failures; it may succeed on subsequent retries

#### Out of Memory Errors
**Problem:** Docker containers run out of memory  
**Solution:** Increase Docker's memory allocation:
- Docker Desktop: Settings → Resources → Memory (set to at least 8GB)
- Linux: Configure Docker daemon with appropriate memory limits

#### Rate Limiting
**Problem:** OpenAI API rate limit exceeded  
**Solution:** 
- Wait for the rate limit to reset (usually 1 minute)
- Consider upgrading your OpenAI API plan for higher limits

### Getting Help
- Check the [logs directory](#-output-folder-structure-explanation) for detailed execution logs
- Review the [research paper](https://software-lab.org/publications/ExecutionAgent_2024-12-14.pdf) for technical details
- Open an issue on GitHub with:
  - The command you ran
  - Relevant logs from `experimental_setups/experiment_XX/`
  - Error messages

---

## 📜 Research Paper  
Dive into the technical details and evaluation in our [paper](https://software-lab.org/publications/ExecutionAgent_2024-12-14.pdf).  

---

## 🤝 Contributing

We welcome contributions! Here are some ways you can help:

- **Report Bugs:** Open an issue with details about the problem
- **Suggest Features:** Share your ideas for new functionality
- **Improve Documentation:** Help make these docs even better
- **Submit Pull Requests:** Fix bugs or add features

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add feature X"`
5. Push to your fork: `git push origin feature-name`
6. Open a pull request

### Code Style
- Follow existing code formatting
- Add comments for complex logic
- Update documentation for user-facing changes

---

## 📬 Feedback  
Have suggestions or found a bug? We'd love to hear from you!

- **Email:** [fi_bouzenia@esi.dz](mailto:fi_bouzenia@esi.dz)
- **Issues:** Open an issue on [GitHub](https://github.com/majercakdavid/ExecutionAgent/issues)

---

## 📄 License

See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built on top of [Auto-GPT](https://github.com/Significant-Gravitas/Auto-GPT) framework.
