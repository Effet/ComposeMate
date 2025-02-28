# Compose Mate

A Docker Compose management tool that helps you automate container operations and schedule tasks.

[中文文档](README_zh.md)

## Features

- Automated Docker Compose management
- File change monitoring and auto-reconciliation
- Scheduled tasks execution with cron syntax
- Web interface for monitoring and control
- Support for multiple applications and tasks
- Logging system with rotation

## Installation

```bash
pip install compose-mate
```

## Usage

Run the application:

```bash
compose-mate --repo-path /path/to/repo [--state-path /path/to/state] [--port 8080]
```

## Configuration

Create a `.cm.yaml` file in your repository:

```yaml
apps:
  - id: app-name
    path: app-path
    tasks:
      - id: task-name
        cron: "*/5 * * * *"
        steps:
          - type: "compose_run"
            compose_service: "service-name"
```

### Task Types

Supports three types of task steps:

1. `compose_run`: Run a one-off container
   ```yaml
   type: "compose_run"
   compose_service: "backup"
   ```

2. `compose_command`: Execute command in running container
   ```yaml
   type: "compose_command"
   compose_service: "redis"
   command: ["redis-cli", "save"]
   ```

3. `rest_api`: Make HTTP requests
   ```yaml
   type: "rest_api"
   compose_service: "web"  # Optional
   endpoint: "http://localhost/api"
   method: "GET"
   ```

## Project Structure

- `.cm-state/`: State and log files
- `logs/`: Application and task logs
- `state.json`: Current state data

## Web Interface

Access the web interface at `http://localhost:8080` to:
- View application and task status
- Trigger manual reconciliation
- View task logs
- Execute tasks manually
