# ExecutionAgent Architecture

This document provides an overview of ExecutionAgent's architecture and explains how its components work together to autonomously build and test GitHub projects.

## Table of Contents
- [High-Level Overview](#high-level-overview)
- [Core Components](#core-components)
- [Execution Flow](#execution-flow)
- [Key Files and Directories](#key-files-and-directories)
- [Agent Workflow](#agent-workflow)
- [Extension Points](#extension-points)

## High-Level Overview

ExecutionAgent is built on top of the Auto-GPT framework and uses Large Language Models (LLMs) to intelligently interact with GitHub repositories. The system follows a cyclical approach where it:

1. **Analyzes** the project structure and documentation
2. **Plans** the build and test strategy
3. **Executes** actions in a containerized environment
4. **Learns** from successes and failures
5. **Retries** with improved strategies when needed

```
┌─────────────────────────────────────────────────────────────┐
│                     ExecutionAgent                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Analysis   │───▶│   Planning   │───▶│  Execution   │ │
│  │   Engine     │    │   System     │    │   Engine     │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│         │                                        │          │
│         │              ┌──────────────┐          │          │
│         └─────────────▶│   Learning   │◀─────────┘          │
│                        │   & Memory   │                     │
│                        └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
              │                      │
              ▼                      ▼
     ┌────────────────┐    ┌────────────────┐
     │  GitHub API    │    │ Docker Engine  │
     └────────────────┘    └────────────────┘
```

## Core Components

### 1. BaseAgent (`autogpt/agents/base.py`)

The `BaseAgent` class is the heart of ExecutionAgent. It orchestrates the entire execution process.

**Key Responsibilities:**
- Managing the agent's lifecycle and state
- Constructing prompts for the LLM
- Executing commands via the command registry
- Maintaining context across cycles
- Learning from previous attempts

**Important Methods:**
- `think()`: Executes one reasoning cycle
- `construct_base_prompt()`: Builds context-aware prompts
- `search_documentation()`: Searches for installation documentation
- `find_workflows()`: Locates CI/CD workflows
- `interact_with_shell()`: Executes shell commands

### 2. Command Registry (`autogpt/models/command_registry.py`)

Manages all available commands that the agent can execute.

**Available Commands:**
- File operations (read, write, append)
- Web browsing and search
- Code analysis and execution
- Shell command execution
- Docker container management

### 3. Planning System (`autogpt/core/planning/`)

Handles prompt engineering and strategy formulation.

**Components:**
- `templates.py`: Prompt templates and constraints
- Planning strategies for different scenarios
- Response parsing and validation

**Key Templates:**
- `PLAN_PROMPT_CONSTRAINTS`: Defines agent limitations
- `PLAN_PROMPT_RESOURCES`: Available resources
- `PLAN_PROMPT_PERFORMANCE_EVALUATIONS`: Success criteria

### 4. Memory System

Stores and retrieves information across execution cycles.

**Types of Memory:**
- **Short-term**: Current cycle context
- **Long-term**: Learning from previous attempts stored in `problems_memory/`
- **Search Results**: Documentation found for the project

### 5. Workspace Management

Manages file operations within isolated workspaces.

**Locations:**
- `execution_agent_workspace/`: Runtime workspace
- `experimental_setups/experiment_XX/`: Logged results
  - `files/`: Generated Dockerfiles and scripts
  - `logs/`: Execution logs
  - `responses/`: LLM responses
  - `saved_contexts/`: Agent state snapshots

### 6. Docker Integration

Handles containerized build and test execution.

**Managed by:**
- `manage_docker_images.py`: Docker lifecycle management
- Custom Dockerfiles generated per project
- Isolated container environments for safety

## Execution Flow

### Phase 1: Initialization
```
User Input (Repo URL or Batch File)
    ↓
Extract Project Metadata
    ↓
Detect Programming Language
    ↓
Clone Repository
    ↓
Initialize Agent
```

### Phase 2: Analysis
```
Search for Documentation
    ↓
Find CI/CD Workflows
    ↓
Analyze Project Structure
    ↓
Identify Build System
```

### Phase 3: Planning & Execution (Cyclical)
```
┌─────────────────────────────────┐
│ Construct Prompt with Context   │
│   - Goals                       │
│   - Available commands          │
│   - Current state               │
│   - Previous learnings          │
└─────────────────┬───────────────┘
                  ↓
┌─────────────────────────────────┐
│ LLM Reasoning                   │
│   - Analyze situation           │
│   - Select next action          │
│   - Generate command            │
└─────────────────┬───────────────┘
                  ↓
┌─────────────────────────────────┐
│ Execute Command                 │
│   - File operations             │
│   - Shell commands              │
│   - Docker operations           │
└─────────────────┬───────────────┘
                  ↓
┌─────────────────────────────────┐
│ Update State & Memory           │
│   - Log results                 │
│   - Update context              │
│   - Learn from outcome          │
└─────────────────┬───────────────┘
                  ↓
        Success? ──No──▶ Continue Cycle (if cycles remain)
            │
           Yes
            ↓
        Complete
```

### Phase 4: Learning & Retry
```
Attempt Failed?
    ↓
Extract Failure Patterns
    ↓
Update problems_memory/
    ↓
Retry with Enhanced Strategy
```

## Key Files and Directories

### Entry Points
- **`ExecutionAgent.sh`**: Main script for running the agent
- **`run.sh`**: Alternative runner script

### Core Logic
- **`autogpt/agents/base.py`**: Base agent implementation
- **`autogpt/core/planning/templates.py`**: Prompt templates
- **`autogpt/prompts/generator.py`**: Dynamic prompt generation
- **`autogpt/prompts/prompt.py`**: Prompt builder

### Utilities
- **`get_main_language.py`**: Language detection
- **`clone_and_set_metadata.py`**: Repository setup
- **`manage_docker_images.py`**: Docker lifecycle
- **`post_process.py`**: Result analysis
- **`show_results.py`**: Result display

### Configuration
- **`ai_settings.yaml`**: Agent goals and configuration
- **`customize.json`**: User customization options
- **`prompt_files/`**: Custom prompt configurations
- **`plugins_config.yaml`**: Plugin settings

### Output Directories
- **`experimental_setups/experiment_XX/`**: Per-run results
- **`problems_memory/`**: Learning from failures
- **`search_logs/`**: Documentation search cache

## Agent Workflow

### Cycle Structure

Each cycle consists of:

1. **Think Phase**
   ```python
   command_name, arguments, thoughts = agent.think(instruction)
   ```
   - Constructs prompt with current context
   - Queries LLM for next action
   - Parses response into structured command

2. **Execute Phase**
   ```python
   result = command_registry.execute(command_name, arguments)
   ```
   - Validates command and arguments
   - Executes in appropriate context (shell, Docker, filesystem)
   - Captures output and errors

3. **Update Phase**
   ```python
   agent.update_memory(command_name, arguments, result)
   ```
   - Logs execution details
   - Updates agent state
   - Stores learnings for future cycles

### Context Building

The agent builds rich context by incorporating:

- **Project Information**: URL, language, structure
- **Documentation**: Found README, installation guides
- **Workflows**: Detected CI/CD configurations
- **Previous Memory**: Learnings from past attempts
- **Current State**: Files created, commands executed
- **Goals**: Build successfully, run tests

### Learning Mechanism

**Problem Memory** (`problems_memory/`):
- Stores project-specific learnings
- Used in subsequent attempts
- Helps avoid repeating mistakes
- Example: "Project X requires system package Y before building"

**Search Cache** (`search_logs/`):
- Caches documentation search results
- Reduces repeated API calls
- Speeds up subsequent runs

## Extension Points

### Adding New Commands

1. Create command in `autogpt/commands/`
2. Register in command registry
3. Add to prompt templates if needed
4. Update agent capabilities

### Custom Prompt Strategies

1. Add templates in `autogpt/core/planning/templates.py`
2. Modify prompt generation in `autogpt/prompts/generator.py`
3. Update `ai_settings.yaml` with new goals

### Plugin Integration

1. Create plugin following plugin template
2. Configure in `plugins_config.yaml`
3. Plugin commands automatically available to agent

### Docker Customization

1. Modify base Dockerfile templates
2. Adjust Docker management in `manage_docker_images.py`
3. Update container lifecycle policies in `customize.json`

## Data Flow

### Input Data
```
GitHub URL → Project Metadata → Repository Clone → Analysis
```

### Processing Data
```
Agent State ↔ LLM Prompts ↔ Commands ↔ Execution Results
     ↓                                        ↓
Memory Storage ←────────────────── Logs & Context
```

### Output Data
```
Execution Logs
    ↓
Saved Contexts
    ↓
LLM Responses
    ↓
Build Artifacts (Dockerfile, scripts)
    ↓
Results Summary
```

## Performance Considerations

### Cycle Budget
- Default: 40 cycles per attempt
- Configurable via `-l` parameter
- Trade-off between thoroughness and cost

### Retry Strategy
- Default: 3 total attempts
- Each attempt learns from previous
- Exponential improvement expected

### Token Management
- Careful prompt construction to stay within limits
- Context summarization for long histories
- Selective memory inclusion

## Security Model

### Isolation
- All builds run in Docker containers
- No direct host system access
- Controlled file system operations

### Sandboxing
- Limited command set available
- Shell commands validated
- No arbitrary code execution from LLM output

## Debugging and Observability

### Log Levels
- Prompt history: Full LLM interactions
- Cycle list: Command sequence
- Responses: Structured LLM outputs
- Saved contexts: Complete agent state snapshots

### Inspection Points
- Review prompts: `experimental_setups/experiment_XX/logs/prompt_history_*`
- Check commands: `experimental_setups/experiment_XX/logs/cycles_list_*`
- Analyze responses: `experimental_setups/experiment_XX/responses/`
- Debug state: `experimental_setups/experiment_XX/saved_contexts/`

## Future Enhancements

Potential areas for architectural improvements:

1. **Multi-Agent Systems**: Parallel execution of multiple projects
2. **Human-in-the-Loop**: Interactive decision points
3. **Advanced Memory**: Vector-based knowledge retrieval
4. **Custom Agents**: Project-specific agent specialization
5. **Web Interface**: GUI for monitoring and control

---

For implementation details, refer to the source code with inline comments. For usage information, see the [README](README.md).
