# Compose Mate

An enhanced Docker Compose companion tool that provides **automatic updates** and **scheduled tasks** without altering the original `docker-compose.yml` management workflow.

[中文文档](README_zh.md)

## Features

### Preserves Existing Workflow
- Continue managing services using `docker-compose.yml`.
- Users can still manually run `docker compose` commands.
- Automatically runs `docker compose up` when changes are detected, keeping services up to date.

### Enhanced Capabilities
- **File Change Monitoring**: Detects changes in `docker-compose.yml` and related files, automatically applying updates.
- **Cron Job Support**: Adds scheduled task capabilities to `docker compose` through additional configuration.
- **Web Interface**: Enables visual management and manual task execution.
- **Multi-App Support**: Manages multiple `docker-compose` projects simultaneously.
- **Logging System**: Tracks task execution history with log rotation support.

## Installation (Docker-In-Docker)

Run Compose Mate using Docker:

```bash
docker run -d \
  --name compose-mate \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/your/repo:/repo \
  -v /path/to/state:/data \
  -p 8080:8080 \
  ghcr.io/effet/composemate:main
```

Run Compose Mate using Docker Compose:

```yaml
services:
  compose-mate:
    image: ghcr.io/effet/composemate:main
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./repo:/repo
      - ./data:/data
    ports:
      - "8080:8080"
    environment:
      - TZ=Asia/Shanghai
```

### Docker Volumes

- `/var/run/docker.sock`: Required for Docker API access
- `/repo`: Your repository containing docker-compose files
- `/data`: State and log storage

### Environment Variables

- `TZ`: Set timezone (default: UTC)

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

## Web Interface

Access the web interface at `http://localhost:8080` to:
- View application and task status
- Trigger manual reconciliation
- View task logs
- Execute tasks manually
