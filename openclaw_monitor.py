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
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

CONFIG = load_config()
SHARED_FOLDER = CONFIG["shared_folder"]
TIMEOUT = CONFIG["activity_timeout"]

agent_states = {}

# --- 2. OPENCLAW.JSON PARSER ---
def update_agent_list():
    json_path = os.path.join(SHARED_FOLDER, "openclaw.json")
    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            if "agents" in data:
                for agent in data["agents"]:
                    agent_id = agent.get("id") if isinstance(agent, dict) else agent
                    if agent_id and agent_id not in agent_states:
                        agent_states[agent_id] = 0.0
    except Exception as e:
        print(f"[Error] Failed to read openclaw.json: {e}")

# --- 3. EVENT-DRIVEN FILE WATCHER ---
class OpenClawHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        
        normalized_path = os.path.normpath(event.src_path)
        relative_path = os.path.relpath(normalized_path, SHARED_FOLDER)
        path_parts = relative_path.split(os.sep)
        
        if len(path_parts) > 1 and path_parts[0] == "agents":
            agent_id = path_parts[1]
            agent_states[agent_id] = time.time()

def start_file_watcher():
    observer = Observer()
    handler = OpenClawHandler()
    observer.schedule(handler, path=SHARED_FOLDER, recursive=True)
    observer.start()
    return observer

# --- 4. GRAPHICAL USER INTERFACE (TKINTER) ---
class MonitorApp:
    def __init__(self, root):
        self.root = root
        win_cfg = CONFIG["window"]
        
        # Setup Window
        self.root.geometry(f"{win_cfg['width']}x{win_cfg['height']}+{win_cfg['position_x']}+{win_cfg['position_y']}")
        self.root.configure(bg="#0a0a0a")  # Dark background
        
        # Make it borderless and always on top
        self.root.overrideredirect(True)
        if win_cfg.get("always_on_top", True):
            self.root.attributes("-topmost", True)
            
        # Allow closing the app with a Right-Click
        self.root.bind("<Button-3>", lambda e: self.close_app())

        # Frame Animation State
        self.frame_index = 0
        self.agent_widgets = {} # Stores references to UI labels
        
        # Load Images via Pillow
        self.assets = self.load_assets()
        
        # Main Layout Frame
        self.main_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Start the efficient update loop
        self.update_ui()

    def load_assets(self):
        assets = {"working": [], "sleeping": [], "fallback": False}
        try:
            for i in range(2):
                img_w = Image.open(f"assets/working_{i}.png").resize((32, 32), Image.Resampling.NEAREST)
                img_s = Image.open(f"assets/sleeping_{i}.png").resize((32, 32), Image.Resampling.NEAREST)
                assets["working"].append(ImageTk.PhotoImage(img_w))
                assets["sleeping"].append(ImageTk.PhotoImage(img_s))
        except Exception:
            print("[Info] Assets not found. Ensure PNGs are generated.")
            assets["fallback"] = True
        return assets

    def update_ui(self):
        """Called every 500ms by Tkinter - highly efficient!"""
        update_agent_list()
        current_time = time.time()
        
        # Toggle animation frame (0 -> 1 -> 0)
        self.frame_index = (self.frame_index + 1) % 2
        
        # Build UI dynamically for each agent
        for idx, agent_id in enumerate(sorted(agent_states.keys())):
            last_active = agent_states[agent_id]
            is_active = (current_time - last_active) < TIMEOUT
            
            # Create widget container if it doesn't exist
            if agent_id not in self.agent_widgets:
                frame = tk.Frame(self.main_frame, bg="#0a0a0a", width=80)
                frame.grid(row=0, column=idx, padx=10)
                
                img_lbl = tk.Label(frame, bg="#0a0a0a")
                img_lbl.pack(pady=(0, 5))
                
                status_lbl = tk.Label(frame, font=("Courier", 10, "bold"), bg="#0a0a0a")
                status_lbl.pack()
                
                id_lbl = tk.Label(frame, text=agent_id[:8], font=("Courier", 9), fg="#e0e0e0", bg="#0a0a0a")
                id_lbl.pack()
                
                self.agent_widgets[agent_id] = {"img": img_lbl, "status": status_lbl}
            
            # Update values and images
            widgets = self.agent_widgets[agent_id]
            
            if not self.assets["fallback"]:
                img = self.assets["working"][self.frame_index] if is_active else self.assets["sleeping"][self.frame_index]
                widgets["img"].configure(image=img)
                widgets["img"].image = img # Keep reference to prevent garbage collection
                
            status_text = "WORKING" if is_active else "SLEEPING"
            status_color = "#00f5d4" if is_active else "#6c757d"
            widgets["status"].configure(text=status_text, fg=status_color)

        # Schedule next update in 500 milliseconds (0.5 seconds)
        self.root.after(500, self.update_ui)

    def close_app(self):
        print("Closing Monitor...")
        self.root.destroy()

# --- 5. APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    print("Starting Tkinter OpenClaw Monitor... (Right-Click window to exit)")
    watcher_observer = start_file_watcher()
    
    root = tk.Tk()
    app = MonitorApp(root)
    
    try:
        root.mainloop() # This blocks and efficiently waits for events/timers
    finally:
        watcher_observer.stop()
        watcher_observer.join()
