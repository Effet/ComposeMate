#!/bin/bash
set -e

# Run compose-mate with provided arguments
exec python -m compose_mate.main "$@"
