# 🐾 OpenClaw Agent Monitor

> A lightweight, event-driven desktop widget for Linux that visualizes the real-time status of your OpenClaw AI agents — always visible, always on top.

---

## Overview

**OpenClaw Agent Monitor** is a minimal Python desktop tool that watches a **Podman Shared Volume** for activity from running OpenClaw agents. It reads the agent list from `openclaw.json` and tracks file-system activity per agent to determine whether each agent is currently **WORKING** or **SLEEPING**.

The monitor renders a small, frameless **always-on-top window** on your Linux desktop (tkinter + Pillow) — no browser, no terminal, no overhead.

---

## How It Works

```
┌─────────────────────┐      :Z volume      ┌──────────────────────┐
│  OpenClaw Agents    │ ──── JSON files ───▶ │  openclaw_monitor.py │
│  (Podman Container) │   (shared volume)    │  (Desktop Overlay)   │
└─────────────────────┘                      └──────────────────────┘
```

1. OpenClaw writes agent config to `openclaw.json` inside the shared volume.
2. Each agent writes runtime data to `agents/<id>/` subdirectories.
3. `watchdog` detects file changes instantly (event-driven, ~0% CPU).
4. The tkinter overlay updates every 500ms — showing each agent as `WORKING` or `SLEEPING`.

**Agent names** are read from:
```
openclaw.json → agents.list[].id
```

**Agent activity** is tracked via:
```
agents/<id>/sessions/sessions.json  →  last modified timestamp
```

---

## Project Structure

```
openclaw-agent-monitor/
├── openclaw_monitor.py       # Main application
├── generate_assets.py        # Generates pixel-art PNG sprites
├── setup.sh                  # First-time setup (venv, deps, config, assets)
├── start.sh                  # Launch the monitor (run this every time)
├── config.example.yaml       # Configuration template
├── config.yaml               # Your local config (git-ignored)
├── requirements.txt          # Python dependencies
├── assets/                   # Generated PNG sprites (git-ignored)
└── .gitignore
```

---

## Requirements

- Linux (tested on **Manjaro**)
- Python 3.10+
- `tkinter` system package (usually pre-installed)
- A running OpenClaw instance with a Podman shared volume

### System packages (if tkinter is missing)

```bash
# Arch / Manjaro
sudo pacman -S tk

# Ubuntu / Debian
sudo apt install python3-tk
```

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/lordw0lt3r/openclaw-agent-monitor.git
cd openclaw-agent-monitor
```

### 2. Make scripts executable

```bash
chmod +x setup.sh start.sh
```

### 3. Run setup (first time only)

```bash
./setup.sh
```

The setup script will automatically:
- Create a Python virtual environment (`.venv/`)
- Install all dependencies from `requirements.txt`
- Ask for your **Podman shared volume host path** and write `config.yaml`
- Generate pixel-art sprites into `assets/`

### 4. Start the monitor

```bash
./start.sh
```

That's it. Run `./start.sh` every time you want to launch the monitor.

---

## Configuration

All settings live in `config.yaml` (created from `config.example.yaml` during setup).

```yaml
# HOST path of your Podman shared volume
# Must match the left side of your -v mount:
#   -v "${SHARED_FOLDER}:/home/openclaw/.openclaw:Z"
shared_folder_path: "/your/host/path/.openclaw"

# Name of the JSON config file written by OpenClaw
json_filename: "openclaw.json"

# Seconds of inactivity before an agent is shown as SLEEPING
activity_timeout: 10

# Monitor window settings
window:
  width: 600
  height: 150
  position_x: 100
  position_y: 100
  always_on_top: true
```

> ⚠️ `config.yaml` is listed in `.gitignore` and will never be committed.

---

## Podman Volume Setup

The monitor reads from the **host side** of your Podman volume. Your container must be started with:

```bash
-v "${SHARED_FOLDER}:/home/openclaw/.openclaw:Z"
```

The `:Z` flag sets the correct SELinux label for shared access. Set `shared_folder_path` in `config.yaml` to the value of `$SHARED_FOLDER` on your host.

### File permissions

If the shared folder is owned by another user, grant read access via ACL (one-time):

```bash
sudo setfacl -R -m u:$(whoami):rX /your/shared/folder/
```

---

## Usage

| Action | How |
|---|---|
| Move the window | Left-click and drag |
| Close the monitor | Right-click anywhere on the window |
| Regenerate assets | `source .venv/bin/activate && python generate_assets.py` |

---

## Autostart (Manjaro / systemd desktops)

Create a `.desktop` file to launch the monitor automatically on login:

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/openclaw-monitor.desktop << EOF
[Desktop Entry]
Name=OpenClaw Agent Monitor
Exec=/absolute/path/to/repo/start.sh
Type=Application
X-GNOME-Autostart-enabled=true
EOF
```

> Make sure to use the **absolute path** to `start.sh`.

---

## Dependencies

| Package | Purpose |
|---|---|
| `watchdog` | Event-driven file system monitoring |
| `pillow` | Pixel-art sprite generation and rendering |
| `PyYAML` | Loads `config.yaml` |
| `tkinter` | Borderless always-on-top GUI (stdlib) |

---

## License

This project is currently private. License to be determined.
