import argparse
import logging
import os
import signal
import sys
from pathlib import Path

from compose_mate.core.manager import ComposeManager
from compose_mate.web.app import start_web_server


def parse_args():
    parser = argparse.ArgumentParser(description='Compose Mate')
    parser.add_argument(
        '--repo-path',
        type=str,
        required=True,
        help='Path to the repository containing docker-compose files'
    )
    parser.add_argument(
        '--state-path',
        type=str,
        help='Path to store state files (default: <repo-path>/.cm-state)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Web interface port (default: 8080)'
    )

    args = parser.parse_args()

    # use default value if state_path is not specified
    if not args.state_path:
        args.state_path = os.path.join(args.repo_path, '.cm-state')

    return args


def signal_handler(signum, frame):
    logging.info("Shutting down...")
    if hasattr(signal_handler, 'manager'):
        signal_handler.manager.stop()
    sys.exit(0)


def main():
    args = parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    Path(args.state_path).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(args.state_path, 'logs')).mkdir(exist_ok=True)

    manager = ComposeManager(args.repo_path, args.state_path)
    signal_handler.manager = manager

    start_web_server(manager, port=args.port)


if __name__ == '__main__':
    main()
