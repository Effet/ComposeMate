import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LogManager:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.log_path = state_path / 'logs'
        self.log_path.mkdir(parents=True, exist_ok=True)

        # Setup main logger
        self._setup_main_logger()

    def _setup_main_logger(self):
        logger = logging.getLogger('compose_mate')
        logger.setLevel(logging.INFO)

        # # Console handler
        # console = logging.StreamHandler(sys.stdout)
        # console.setFormatter(logging.Formatter(
        #     '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        # ))
        # logger.addHandler(console)

        # File handler
        file_handler = RotatingFileHandler(
            self.log_path / 'cm.log',
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

    def get_main_logger(self) -> logging.Logger:
        return logging.getLogger('compose_mate')

    def get_app_logger(self, app_id: str) -> logging.Logger:
        logger = logging.getLogger(f'compose_mate.app.{app_id}')
        # Prevent propagation to parent loggers
        logger.propagate = False
        logger.setLevel(logging.INFO)

        app_log_dir = self.log_path / app_id
        app_log_dir.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            app_log_dir / 'app.log',
            maxBytes=1024 * 1024,
            backupCount=5
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)

        return logger

    def get_task_logger(self, app_id: str, task_id: str) -> logging.Logger:
        logger = logging.getLogger(f'compose_mate.app.{app_id}.task.{task_id}')
        # Prevent propagation to parent loggers
        logger.propagate = False
        logger.setLevel(logging.INFO)

        task_log_dir = self.log_path / app_id / 'tasks'
        task_log_dir.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            task_log_dir / f'{task_id}.log',
            maxBytes=1024 * 1024,
            backupCount=5
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)

        return logger
