import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

import pathspec
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from compose_mate.core.executor import TaskExecutor
from compose_mate.core.models import AppConfig, State, AppState, TaskState
from core.logging_utils import LogManager


class ConfigChangeHandler(FileSystemEventHandler):
    def __init__(self, manager):
        self.manager = manager
        self.logger = manager.log_manager.get_main_logger()

        # Convert repo_path to absolute path
        self.abs_repo_path = Path(self.manager.repo_path).resolve()
        self.abs_state_path = Path(self.manager.state_path).resolve()

        # Add state path to ignored paths if it's under repo_path
        try:
            self.state_rel_path = self.abs_state_path.relative_to(self.abs_repo_path)
        except ValueError:
            self.state_rel_path = None
        self.gitignore = self._load_gitignore()

    def _load_gitignore(self):
        gitignore_path = self.abs_repo_path / '.gitignore'
        patterns = []

        if gitignore_path.exists():
            with open(gitignore_path) as f:
                patterns.extend(f.readlines())

        # Add state path pattern
        if self.state_rel_path:
            patterns.append(str(self.state_rel_path))

        return pathspec.PathSpec.from_lines(
            pathspec.patterns.GitWildMatchPattern,
            patterns
        )

    def on_modified(self, event):
        try:
            # Convert both paths to absolute before comparing
            abs_path = Path(event.src_path).resolve()
            rel_path = abs_path.relative_to(self.abs_repo_path)

            # Skip if path is under state directory or matches gitignore
            if (self.state_rel_path and str(rel_path).startswith(str(self.state_rel_path))) or \
                    self.gitignore.match_file(str(rel_path)):
                return

            self.logger.info(f"File changed: {event.src_path}")
            self.manager.reconcile()
        except ValueError:
            # Path is not relative to repo_path
            pass


class ComposeManager:
    def __init__(self, repo_path: str, state_path: str):
        self.repo_path = Path(repo_path)
        self.state_path = Path(state_path)
        self.state_file = self.state_path / 'state.json'

        # Initialize logging
        self.log_manager = LogManager(self.state_path)
        self.logger = self.log_manager.get_main_logger()

        self.scheduler = BackgroundScheduler()
        self.executor = TaskExecutor(self)

        # configure file monitoring
        self.observer = Observer()
        self.observer.schedule(
            ConfigChangeHandler(self),
            str(self.repo_path),
            recursive=True
        )

        # start server
        self.state = State(apps={}, tasks={})
        self.load_state()
        self.scheduler.start()
        self.observer.start()
        self.reconcile()

    def load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                    self.state = State(**data)
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to load state file: {e}")
                # keep the default state

    def save_state(self):
        # ensure state directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state.dict(), f, indent=2)

    def load_config(self) -> List[AppConfig]:
        config_file = self.repo_path / '.cm.yaml'
        if not config_file.exists():
            return []

        with open(config_file) as f:
            config = yaml.safe_load(f)

        apps = []
        for app_data in config.get('apps', []):
            apps.append(AppConfig(**app_data))
        return apps

    def reconcile(self):
        self.logger.info("Starting reconciliation")
        try:
            self.scheduler.remove_all_jobs()

            apps = self.load_config()
            current_apps = {app.id: app for app in apps}

            for app_id, app in current_apps.items():
                try:
                    app_path = self.repo_path / app.path
                    if not app_path.exists():
                        self.logger.warning(f"App path not found: {app_path}")
                        continue

                    self._ensure_compose_up(app)

                    self.state.apps[app_id] = AppState(
                        id=app_id,
                        path=app.path,
                        status='running',
                        last_reconcile=datetime.now().isoformat()
                    )

                    for task in app.tasks:
                        try:
                            self.executor.schedule_task(app, task)
                            self.state.tasks[f"{app_id}_{task.id}"] = TaskState(
                                id=task.id,
                                app_id=app_id,
                                status='success'
                            )
                        except Exception as e:
                            self.logger.error(f"Failed to schedule task {task.id}: {e}")
                            self.state.tasks[f"{app_id}_{task.id}"] = TaskState(
                                id=task.id,
                                app_id=app_id,
                                status='failed'
                            )
                except Exception as e:
                    self.logger.error(f"Failed to reconcile app {app_id}: {e}")
                    if app_id in self.state.apps:
                        self.state.apps[app_id].status = 'failed'

            for app_id in list(self.state.apps.keys()):
                if app_id not in current_apps:
                    try:
                        app_state = self.state.apps[app_id]
                        self._ensure_compose_down(app_state)
                    except Exception as e:
                        self.logger.error(f"Failed to stop app {app_id}: {e}")
                    finally:
                        del self.state.apps[app_id]

            for task_key in list(self.state.tasks.keys()):
                app_id = task_key.split('_')[0]
                if app_id not in current_apps:
                    del self.state.tasks[task_key]

        except Exception as e:
            self.logger.error(f"Reconciliation failed: {e}")
        finally:
            self.save_state()

    def _ensure_compose_up(self, app: AppConfig):
        app_path = self.repo_path / app.path
        app_logger = self.log_manager.get_app_logger(app.id)

        try:
            app_logger.info(f"Starting app {app.id}")
            result = subprocess.run(
                ["docker-compose", "--project-directory", str(app_path), "up", "-d", "--build"],
                check=True,
                capture_output=True,
                text=True
            )
            app_logger.info(f"Docker compose output:\n{result.stdout}")
            if result.stderr:
                app_logger.warning(f"Docker compose warnings:\n{result.stderr}")
        except subprocess.CalledProcessError as e:
            app_logger.error(f"Failed to start app: {e.stderr}")
            self.state.apps[app.id] = AppState(
                id=app.id,
                path=app.path,
                status='failed',
                last_reconcile=datetime.now().isoformat()
            )
            raise

    def _ensure_compose_down(self, app_state: AppState):
        app_path = self.repo_path / app_state.path
        try:
            subprocess.run(
                ["docker-compose", "--project-directory", str(app_path), "down"],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to stop app {app_state.id}: {e.stderr}")

    def get_task_log(self, task_id: str) -> str:
        log_file = self.state_path / 'logs' / f'{task_id}.log'
        if not log_file.exists():
            return ''

        with open(log_file) as f:
            return f.read()

    def stop(self):
        try:
            self.scheduler.shutdown()
            self.observer.stop()
            self.observer.join()
            self.save_state()
        except Exception as e:
            self.logger.error(f"Failed to stop services: {e}")
