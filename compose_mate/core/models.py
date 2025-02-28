from typing import List, Optional

from pydantic import BaseModel


class StepConfig(BaseModel):
    type: str
    compose_service: str
    command: Optional[List[str]] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None


class TaskConfig(BaseModel):
    id: str
    cron: str
    steps: List[StepConfig]


class AppConfig(BaseModel):
    id: str
    path: str
    tasks: List[TaskConfig]


class AppState(BaseModel):
    id: str
    path: str
    status: str  # 'running' or 'stopped'
    last_reconcile: str  # ISO format timestamp


class TaskState(BaseModel):
    id: str
    app_id: str
    last_run: Optional[str] = None  # ISO format timestamp
    status: str  # 'success' or 'failed'


class State(BaseModel):
    apps: dict[str, AppState]
    tasks: dict[str, TaskState]
