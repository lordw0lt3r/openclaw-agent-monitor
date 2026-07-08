#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "OpenClaw Agent Monitor -- Setup"
echo "================================"

# Python check
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python3 not found. Please install it first."
    exit 1
fi

# Virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv || { echo "ERROR: Failed to create venv."; exit 1; }
fi

source .venv/bin/activate

# Dependencies (only if requirements.txt changed or never installed)
if [ ! -f ".venv/.deps_installed" ] || [ "requirements.txt" -nt ".venv/.deps_installed" ]; then
    echo "Installing dependencies..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    touch .venv/.deps_installed
    echo "OK: Dependencies installed."
else
    echo "OK: Dependencies already up to date."
fi

# Config
if [ ! -f "config.yaml" ]; then
    echo ""
    echo "Enter the HOST path of your Podman shared volume."
    echo "(Left side of your -v mount, e.g. /home/user/.openclaw)"
    echo ""
    read -rp "  shared_folder_path: " SHARED_PATH

    [ ! -d "$SHARED_PATH" ] && echo "WARNING: '$SHARED_PATH' does not exist yet -- continuing anyway."

    cp config.example.yaml config.yaml
    sed -i "s|shared_folder_path:.*|shared_folder_path: \"$SHARED_PATH\"|" config.yaml
    echo "OK: config.yaml created."
else
    echo "OK: config.yaml already exists -- skipping."
fi

# Assets
if [ ! -f "assets/working_0.png" ]; then
    echo "Generating pixel art assets..."
    python generate_assets.py || { echo "ERROR: Asset generation failed."; exit 1; }
    echo "OK: Assets generated."
else
    echo "OK: Assets already exist -- skipping."
fi

echo ""
echo "Setup complete. Run './start.sh' to launch the monitor."
