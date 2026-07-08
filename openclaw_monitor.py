"""
openclaw_monitor.py

Main entry point for the OpenClaw Agent Monitor.
Monitors a shared Podman volume for an openclaw.json file via watchdog
and displays a borderless, always-on-top status widget on a Linux desktop
using tkinter + Pillow. Right-click the window to close.
"""

import os
import time
import yaml
import json
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
JSON_FILENAME = CONFIG.get("json_filename", "openclaw.json")
TIMEOUT       = CONFIG.get("activity_timeout", 10)

agent_states = {}  # { agent_id: last_active_timestamp }


# --- 2. OPENCLAW.JSON PARSER ---
def update_agent_list():
    json_path = os.path.join(SHARED_FOLDER, JSON_FILENAME)
    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            agents_block = data.get("agents", {})
            agent_list = agents_block.get("list", [])
            for agent in agent_list:
                agent_id = agent.get("id")
                if agent_id and agent_id not in agent_states:
                    agent_states[agent_id] = 0.0  # Starts as SLEEPING
    except json.JSONDecodeError as e:
        print(f"[Error] Invalid JSON syntax in {JSON_FILENAME}: {e}")
    except PermissionError as e:
        print(f"[Error] Cannot read file (check :Z volume permissions): {e}")
    except Exception as e:
        print(f"[Error] Unexpected error reading {JSON_FILENAME}: {e}")


# --- 3. EVENT-DRIVEN FILE WATCHER ---
class OpenClawHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return

        normalized_path = os.path.normpath(event.src_path)
        relative_path   = os.path.relpath(normalized_path, SHARED_FOLDER)
        path_parts      = relative_path.split(os.sep)

        # Refresh agent list when the main JSON config changes
        if path_parts == [JSON_FILENAME]:
            update_agent_list()
            return

        # Mark agent as active when something inside agents/<id>/ changes
        if len(path_parts) >= 2 and path_parts[0] == "agents":
            agent_id = path_parts[1]
            agent_states[agent_id] = time.time()
            print(f"[Monitor] Activity detected: '{agent_id}'")


def start_file_watcher():
    observer = Observer()
    handler  = OpenClawHandler()
    observer.schedule(handler, path=SHARED_FOLDER, recursive=True)
    observer.start()
    print(f"[Monitor] Watching: {SHARED_FOLDER}")
    return observer


# --- 4. GRAPHICAL USER INTERFACE (TKINTER) ---
class MonitorApp:
    def __init__(self, root):
        self.root    = root
        win_cfg      = CONFIG.get("window", {})

        w = win_cfg.get("width", 600)
        h = win_cfg.get("height", 150)
        x = win_cfg.get("position_x", 100)
        y = win_cfg.get("position_y", 100)

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg="#0a0a0a")
        self.root.overrideredirect(True)
        if win_cfg.get("always_on_top", True):
            self.root.attributes("-topmost", True)

        # Right-click to close, left-click drag to move
        self.root.bind("<Button-3>",  lambda e: self.close_app())
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
        update_agent_list()
        current_time = time.time()
        self.frame_index = (self.frame_index + 1) % 2

        if agent_states:
            self.empty_label.pack_forget()
        else:
            self.empty_label.pack(expand=True)

        for idx, agent_id in enumerate(sorted(agent_states.keys())):
            last_active = agent_states[agent_id]
            is_active   = last_active > 0 and (current_time - last_active) < TIMEOUT

            if agent_id not in self.agent_widgets:
                frame = tk.Frame(self.main_frame, bg="#0a0a0a", width=80)
                frame.grid(row=0, column=idx, padx=10)

                img_lbl = tk.Label(frame, bg="#0a0a0a")
                img_lbl.pack(pady=(0, 5))

                status_lbl = tk.Label(frame, font=("Courier", 10, "bold"), bg="#0a0a0a")
                status_lbl.pack()

                tk.Label(
                    frame, text=agent_id[:12],
                    font=("Courier", 9), fg="#e0e0e0", bg="#0a0a0a"
                ).pack()

                self.agent_widgets[agent_id] = {"img": img_lbl, "status": status_lbl}

            widgets = self.agent_widgets[agent_id]

            if not self.assets["fallback"]:
                img = self.assets["working"][self.frame_index] if is_active else self.assets["sleeping"][self.frame_index]
                widgets["img"].configure(image=img)
                widgets["img"].image = img  # Prevent garbage collection

            status_text  = "WORKING"  if is_active else "SLEEPING"
            status_color = "#00f5d4" if is_active else "#6c757d"
            widgets["status"].configure(text=status_text, fg=status_color)

        self.root.after(500, self.update_ui)

    def close_app(self):
        print("[Monitor] Closing.")
        self.root.destroy()


# --- 5. APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    print("[Monitor] Starting OpenClaw Agent Monitor...")
    print("[Monitor] Right-click the window to exit.")

    watcher_observer = start_file_watcher()
    update_agent_list()  # Initial parse on startup

    root = tk.Tk()
    app  = MonitorApp(root)

    try:
        root.mainloop()
    finally:
        watcher_observer.stop()
        watcher_observer.join()
        print("[Monitor] Stopped.")
