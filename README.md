# 🐾 OpenClaw Agent Monitor

> A lightweight, file-based desktop monitor for OpenClaw agents — always watching, always on top.

---

## Overview

**OpenClaw Agent Monitor** is a minimal Python desktop tool that observes the status of running OpenClaw agents in real time. It works by watching a **Podman Shared Volume** — a folder mounted into one or more containers — for JSON status files written by each agent. When a file changes, the monitor updates its display instantly.

The monitor renders a small, **always-on-top window** on your Linux desktop (via `pygame` or `tkinter`) so you always have a live overview of your agents without switching windows.

---

## How It Works

```
┌─────────────────────┐        watches         ┌──────────────────────┐
│  OpenClaw Agents    │ ──── JSON files ──────▶ │  openclaw_monitor.py │
│  (Podman Container) │   (shared volume)       │  (Desktop Overlay)   │
└─────────────────────┘                         └──────────────────────┘
```

1. Each OpenClaw agent writes its status to a `.json` file inside a **Podman shared volume**.
2. `watchdog` detects any file changes in that folder instantly.
3. The desktop overlay window updates and displays the current agent states.

---

## Project Structure

```
openclaw-agent-monitor/
├── openclaw_monitor.py   # Main application entry point
├── assets/               # GIF animations and UI assets
├── config.yaml           # Configuration (paths, window position)
├── requirements.txt      # Python dependencies
└── .gitignore
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/lordw0lt3r/openclaw-agent-monitor.git
cd openclaw-agent-monitor
```

### 2. Create a virtual environment & install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure

Edit `config.yaml` and set the `shared_folder_path` to the path of your Podman shared volume mount.

```yaml
shared_folder_path: "/run/user/1000/podman/volumes/openclaw_shared"
window_position_x: 0
window_position_y: 0
```

### 4. Run

```bash
python openclaw_monitor.py
```

---

## Dependencies

| Package    | Purpose                                      |
|------------|----------------------------------------------|
| `watchdog` | Monitors the shared folder for file changes  |
| `pygame`   | Renders the always-on-top desktop overlay    |

---

## License

This project is currently private. License to be determined.
