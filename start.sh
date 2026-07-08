#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Sanity checks
[ ! -d ".venv" ]        && echo "ERROR: Run './setup.sh' first (venv missing)."   && exit 1
[ ! -f "config.yaml" ]  && echo "ERROR: Run './setup.sh' first (config missing)." && exit 1
[ ! -f "assets/working_0.png" ] && echo "ERROR: Run './setup.sh' first (assets missing)." && exit 1

source .venv/bin/activate
exec python openclaw_monitor.py
