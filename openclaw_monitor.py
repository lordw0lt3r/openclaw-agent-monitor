"""
openclaw_monitor.py

Main entry point for the OpenClaw Agent Monitor.
Monitors a shared Podman volume for agent activity via watchdog
and displays a borderless, always-on-top status widget on a Linux desktop
using tkinter + Pillow. Right-click the window to close.
"""

import os
import time
import yaml
import tkinter as tk
from PIL import Image, ImageTk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# --- 1. LOAD CONFIGURATION ---
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

CONFIG        = load_config()
SHARED_FOLDER = CONFIG["shared_folder_path"]
TIMEOUT       = CONFIG.get("activity_timeout", 10)

# UI constants
AGENT_COL_WIDTH = 90   # px per agent column
WINDOW_H        = 110  # fixed window height
SIDE_PADDING    = 20   # horizontal padding
MIN_WIDTH       = 220  # minimum window width (empty state)

agent_states = {}  # { agent_id: last_active_timestamp }


# --- 2. FILESYSTEM AGENT DISCOVERY ---
def discover_agents():
    """Scans the agents/ subdirectory to find all known agents.
    No JSON parsing needed — agent IDs are the folder names themselves."""
    agents_dir = os.path.join(SHARED_FOLDER, "agents")
    if not os.path.isdir(agents_dir):
        print(f"[Monitor] agents/ directory not found in: {SHARED_FOLDER}")
        return

    for entry in os.scandir(agents_dir):
        if entry.is_dir() and entry.name not in agent_states:
            agent_states[entry.name] = 0.0  # Registered as SLEEPING
            print(f"[Monitor] Discovered agent: '{entry.name}'")


# --- 3. EVENT-DRIVEN FILE WATCHER ---
class OpenClawHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return

        normalized = os.path.normpath(event.src_path)
        relative   = os.path.relpath(normalized, SHARED_FOLDER)
        parts      = relative.split(os.sep)

        # Activity inside agents/<id>/ → mark agent as WORKING
        if len(parts) >= 2 and parts[0] == "agents":
            agent_id = parts[1]
            # Auto-register agent if not yet known (e.g. new agent added at runtime)
            if agent_id not in agent_states:
                print(f"[Monitor] New agent detected at runtime: '{agent_id}'")
            agent_states[agent_id] = time.time()

    def on_created(self, event):
        """Catches new agent folders created at runtime."""
        if not event.is_directory:
            return

        normalized = os.path.normpath(event.src_path)
        relative   = os.path.relpath(normalized, SHARED_FOLDER)
        parts      = relative.split(os.sep)

        if len(parts) == 2 and parts[0] == "agents":
            agent_id = parts[1]
            if agent_id not in agent_states:
                agent_states[agent_id] = 0.0
                print(f"[Monitor] New agent folder created: '{agent_id}'")


def start_file_watcher():
    observer = Observer()
    observer.schedule(OpenClawHandler(), path=SHARED_FOLDER, recursive=True)
    observer.start()
    print(f"[Monitor] Watching: {SHARED_FOLDER}")
    return observer


# --- 4. GRAPHICAL USER INTERFACE (TKINTER) ---
class MonitorApp:
    def __init__(self, root):
        self.root         = root
        self._last_count  = 0  # Track agent count changes for resize
        win_cfg           = CONFIG.get("window", {})

        x = win_cfg.get("position_x", 100)
        y = win_cfg.get("position_y", 100)

        self.root.geometry(f"{MIN_WIDTH}x{WINDOW_H}+{x}+{y}")
        self.root.configure(bg="#0a0a0a")
        self.root.overrideredirect(True)
        if win_cfg.get("always_on_top", True):
            self.root.attributes("-topmost", True)

        self.root.bind("<Button-3>",      lambda e: self.close_app())
        self.root.bind("<ButtonPress-1>", self._drag_start)
        self.root.bind("<B1-Motion>",     self._drag_motion)
        self._drag_x = 0
        self._drag_y = 0

        self.frame_index   = 0
        self.agent_widgets = {}
        self.assets        = self.load_assets()

        self.main_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.empty_label = tk.Label(
            self.main_frame,
            text="⏳ Waiting for OpenClaw Agents...",
            font=("Courier", 10),
            fg="#555555",
            bg="#0a0a0a"
        )
        self.empty_label.pack(expand=True)

        self.update_ui()

    # --- Drag Logic ---
    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_motion(self, event):
        new_x = self.root.winfo_x() + (event.x - self._drag_x)
        new_y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{new_x}+{new_y}")

    # --- Dynamic Window Resize ---
    def _resize_window(self):
        count = len(agent_states)
        if count == self._last_count:
            return  # Nothing changed, skip resize
        self._last_count = count

        new_w = max(count * AGENT_COL_WIDTH + SIDE_PADDING, MIN_WIDTH)
        # Preserve current X/Y position
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{new_w}x{WINDOW_H}+{x}+{y}")
        print(f"[Monitor] Window resized to {new_w}x{WINDOW_H} for {count} agent(s).")

    # --- Asset Loading ---
    def load_assets(self):
        assets = {"working": [], "sleeping": [], "fallback": False}
        try:
            for i in range(2):
                img_w = Image.open(f"assets/working_{i}.png").resize((32, 32), Image.Resampling.NEAREST)
                img_s = Image.open(f"assets/sleeping_{i}.png").resize((32, 32), Image.Resampling.NEAREST)
                assets["working"].append(ImageTk.PhotoImage(img_w))
                assets["sleeping"].append(ImageTk.PhotoImage(img_s))
        except Exception:
            print("[Info] Assets not found — running in text-only mode.")
            assets["fallback"] = True
        return assets

    # --- Main UI Update Loop (every 500ms) ---
    def update_ui(self):
        discover_agents()
        current_time     = time.time()
        self.frame_index = (self.frame_index + 1) % 2

        # Show/hide empty state
        if agent_states:
            self.empty_label.pack_forget()
        else:
            self.empty_label.pack(expand=True)

        # Resize window if agent count changed
        self._resize_window()

        for idx, agent_id in enumerate(sorted(agent_states.keys())):
            last_active = agent_states[agent_id]
            is_active   = last_active > 0 and (current_time - last_active) < TIMEOUT

            # Create widget on first appearance
            if agent_id not in self.agent_widgets:
                frame = tk.Frame(self.main_frame, bg="#0a0a0a", width=AGENT_COL_WIDTH)
                frame.grid(row=0, column=idx, padx=5)

                img_lbl = tk.Label(frame, bg="#0a0a0a")
                img_lbl.pack(pady=(0, 4))

                status_lbl = tk.Label(frame, font=("Courier", 10, "bold"), bg="#0a0a0a")
                status_lbl.pack()

                tk.Label(
                    frame, text=agent_id[:12],
                    font=("Courier", 9), fg="#e0e0e0", bg="#0a0a0a"
                ).pack()

                self.agent_widgets[agent_id] = {"img": img_lbl, "status": status_lbl}

            # Update sprite and status label
            widgets = self.agent_widgets[agent_id]

            if not self.assets["fallback"]:
                img = self.assets["working"][self.frame_index] if is_active else self.assets["sleeping"][self.frame_index]
                widgets["img"].configure(image=img)
                widgets["img"].image = img

            widgets["status"].configure(
                text  = "WORKING"  if is_active else "SLEEPING",
                fg    = "#00f5d4" if is_active else "#6c757d"
            )

        self.root.after(500, self.update_ui)

    def close_app(self):
        print("[Monitor] Closing.")
        self.root.destroy()


# --- 5. APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    print("[Monitor] Starting OpenClaw Agent Monitor...")
    print("[Monitor] Right-click the window to exit.")

    watcher_observer = start_file_watcher()
    discover_agents()  # Initial scan on startup

    root = tk.Tk()
    app  = MonitorApp(root)

    try:
        root.mainloop()
    finally:
        watcher_observer.stop()
        watcher_observer.join()
        print("[Monitor] Stopped.")
