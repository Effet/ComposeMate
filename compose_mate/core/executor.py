import subprocess
from datetime import datetime
from pathlib import Path

import requests

from core.models import AppConfig, TaskConfig, StepConfig


class TaskExecutor:
    def __init__(self, manager):
        self.manager = manager

    def schedule_task(self, app: AppConfig, task: TaskConfig):
        job_id = f"{app.id}_{task.id}"

        self.manager.scheduler.add_job(
            self.execute_task,
            'cron',
            args=[app, task],
            id=job_id,
            **self._parse_cron(task.cron)
        )

    def execute_task(self, app: AppConfig, task: TaskConfig):
        app_path = self.manager.repo_path / app.path
        logger = self.manager.log_manager.get_task_logger(app.id, task.id)

        for step in task.steps:
            try:
                if step.type == 'compose_run':
                    self._execute_compose_run(app_path, step.compose_service)
                elif step.type == 'compose_command':
                    self._execute_compose_command(app_path, step.compose_service, step.command)
                elif step.type == 'rest_api':
                    self._execute_rest_api(app_path, step)

                logger.info(f"Step {step.type} executed successfully")
                self.manager.state.tasks[f"{app.id}_{task.id}"].last_run = datetime.now().isoformat()
                self.manager.state.tasks[f"{app.id}_{task.id}"].status = 'success'

            except Exception as e:
                error_msg = f"Step {step.type} failed: {str(e)}"
                logger.error(error_msg)
                self.manager.state.tasks[f"{app.id}_{task.id}"].status = 'failed'
                raise

    def _execute_compose_run(self, app_path: Path, service: str):
        cmd = ["docker-compose", "--project-directory", str(app_path), "run", "--rm", service]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")

    def _execute_compose_command(self, app_path: Path, service: str, command: list):
        cmd = ["docker-compose", "--project-directory", str(app_path), "exec", "-T", service] + command
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")

    def _execute_rest_api(self, app_path: Path, step: StepConfig):
        if not step.compose_service:
            # direct call
            response = requests.request(
                method=step.method,
                url=step.endpoint
            )
            response.raise_for_status()
            return

        curl_cmd = f"curl -X {step.method} '{step.endpoint}' -s -f"

        # try curl
        cmd = ["docker-compose", "--project-directory", str(app_path), "exec", "-T",
               step.compose_service, "sh", "-c", f"command -v curl >/dev/null 2>&1 && {curl_cmd}"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return

        # try wget
        wget_cmd = f"wget -O - --method={step.method} '{step.endpoint}' -q"
        cmd = ["docker-compose", "--project-directory", str(app_path), "exec", "-T",
               step.compose_service, "sh", "-c", f"command -v wget >/dev/null 2>&1 && {wget_cmd}"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return

        # try python
        python_cmd = f"""python3 -c 'import urllib.request as r; req=r.Request("{step.endpoint}",method="{step.method}"); r.urlopen(req)'"""
        cmd = ["docker-compose", "--project-directory", str(app_path), "exec", "-T",
               step.compose_service, "sh", "-c", python_cmd]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"All HTTP request methods failed: {result.stderr}")

    def _log_execution(self, log_file: Path, message: str):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")

    def _parse_cron(self, cron_str: str) -> dict:
        parts = cron_str.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_str}")

        return {
            'minute': parts[0],
            'hour': parts[1],
            'day': parts[2],
            'month': parts[3],
            'day_of_week': parts[4]
        }
