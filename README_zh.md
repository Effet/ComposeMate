# Compose Mate

一个增强型 Docker Compose 伴侣工具，在不改变原有 `docker-compose.yml` 管理方式的前提下，提供 **自动更新** 和 **计划任务** 功能。

## 功能特点

### 保持原有工作流程
- 继续使用 `docker-compose.yml` 进行服务管理。
- 仍然可以手动运行 `docker compose` 命令。
- 监听 `docker-compose.yml` 及相关文件的变更，并自动执行 `docker compose up`，保持服务最新。

### 增强功能
- **文件变更监控**：自动检测 `docker-compose.yml` 及相关文件的更改，并自动应用更新。
- **Cron 任务支持**：通过额外的配置，为 `docker compose` 增加定时任务能力。
- **Web 界面**：提供可视化管理和手动任务执行功能。
- **多应用支持**：同时管理多个 `docker-compose` 项目。
- **日志系统**：记录任务执行历史，并支持日志轮转。

## 安装（Docker-In-Docker）

使用 Docker 运行 Compose Mate：

```bash
docker run -d \
  --name compose-mate \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/your/repo:/repo \
  -p 8080:8080 \
  ghcr.io/effet/composemate:main
```

使用 Docker Compose 运行 Compose Mate：

```yaml
services:
  compose-mate:
    image: ghcr.io/effet/composemate:main
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./repo:/repo
    ports:
      - "8080:8080"
    environment:
      - TZ=Asia/Shanghai
```

### Docker 挂载卷
- `/var/run/docker.sock`：用于访问 Docker API
- `/repo`：存放包含 docker-compose.yml 的代码仓库

### 环境变量
- `TZ`：设置时区（默认：UTC）

## 配置

在您的仓库中创建 `.cm.yaml` 配置文件：

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

### 任务类型

支持以下三种任务步骤：

1. `compose_run`：运行一次性容器
   ```yaml
   type: "compose_run"
   compose_service: "backup"
   ```

2. `compose_command`：在运行中的容器内执行命令
   ```yaml
   type: "compose_command"
   compose_service: "redis"
   command: ["redis-cli", "save"]
   ```

3. `rest_api`：发送 HTTP 请求
   ```yaml
   type: "rest_api"
   compose_service: "web"  # 可选
   endpoint: "http://localhost/api"
   method: "GET"
   ```

## Web 界面

访问 `http://localhost:8080` 以：
- 查看应用和任务状态
- 触发手动协调
- 查看任务日志
- 手动执行任务
