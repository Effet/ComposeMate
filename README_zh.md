# Compose Mate

一个 Docker Compose 管理工具，帮助您自动化容器操作和调度任务。

## 功能特点

- 自动化 Docker Compose 管理
- 文件变更监控和自动协调
- 使用 cron 语法执行计划任务
- Web 界面进行监控和控制
- 支持多应用和任务管理
- 日志系统（含日志轮转）

## 安装

```bash
pip install compose-mate
```

## ��用方法

运行应用：

```bash
compose-mate --repo-path /path/to/repo [--state-path /path/to/state] [--port 8080]
```

## 配置说明

在您的代码仓库中创建 `.cm.yaml` 配置文件：

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

支持三种任务步骤类型：

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

## 项目结构

- `.cm-state/`：状态和日志文件
- `logs/`：应用和任务日志
- `state.json`：当前状态数据

## Web 界面

访问 `http://localhost:8080` 可以：
- 查看应用和任务状态
- 触发手动协调
- 查看任务日志
- 手动执行任务
