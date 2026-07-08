import os
import time
import yaml
import json
import threading
import pygame
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 1. LOAD CONFIGURATION ---
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

CONFIG = load_config()
SHARED_FOLDER = CONFIG["shared_folder"]
TIMEOUT = CONFIG["activity_timeout"]

# Global runtime state for agents: { "agent_id": last_active_timestamp }
agent_states = {}

# --- 2. OPENCLAW.JSON PARSER ---
def update_agent_list():
    """Reads registered agents from the static openclaw.json file."""
    json_path = os.path.join(SHARED_FOLDER, "openclaw.json")
    if not os.path.exists(json_path):
        print(f"[Warning] openclaw.json not found at: {json_path}")
        return

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            # Adapting to OpenClaw structure: extracting the list of agents
            if "agents" in data:
                for agent in data["agents"]:
                    agent_id = agent.get("id") if isinstance(agent, dict) else agent
                    if agent_id and agent_id not in agent_states:
                        agent_states[agent_id] = 0.0  # Initially set to sleeping
    except Exception as e:
        print(f"[Error] Failed to read openclaw.json: {e}")

# --- 3. EVENT-DRIVEN FILE WATCHER (WATCHDOG) ---
class OpenClawHandler(FileSystemEventHandler):
    """Listens for file modifications inside the agents/ directory."""
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Expected path structure: .../SHARED_FOLDER/agents/Sub_Agent_A/sessions/sessions.json
        normalized_path = os.path.normpath(event.src_path)
        relative_path = os.path.relpath(normalized_path, SHARED_FOLDER)
        path_parts = relative_path.split(os.sep)
        
        if len(path_parts) > 1 and path_parts[0] == "agents":
            agent_id = path_parts[1]
            # Update the activity timestamp to the current time
            agent_states[agent_id] = time.time()

def start_file_watcher():
    observer = Observer()
    handler = OpenClawHandler()
    observer.schedule(handler, path=SHARED_FOLDER, recursive=True)
    observer.start()
    return observer

# --- 4. GRAPHICAL USER INTERFACE (PYGAME) ---
def main_ui():
    pygame.init()
    pygame.font.init()
    
    # Window configuration from YAML
    win_cfg = CONFIG["window"]
    
    # Set OS window position before initializing the display mode
    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{win_cfg['position_x']},{win_cfg['position_y']}"
    
    flags = pygame.NOFRAME  # Borderless window
    if win_cfg.get("always_on_top", True):
        flags |= pygame.ALWAYS_ON_TOP
        
    screen = pygame.display.set_mode((win_cfg["width"], win_cfg["height"]), flags)
    pygame.display.set_caption("OpenClaw Monitor")
    
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier", 12, bold=True)
    
    # LOAD ASSETS (with safe fallback handling)
    try:
        img_working = pygame.image.load("assets/agent_working.gif").convert_alpha()
        img_sleeping = pygame.image.load("assets/agent_sleeping.gif").convert_alpha()
        has_assets = True
    except Exception:
        print("[Info] No asset images found. Using colored squares as fallback.")
        has_assets = False

    running = True
    while running:
        # Event Loop (required to keep the OS from marking the window as unresponsive)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        # Fill background with a dark slate/black color
        screen.fill((10, 10, 10))
        
        # Dynamically refresh agent list in case new sub-agents are registered at runtime
        update_agent_list()
        
        current_time = time.time()
        agents = sorted(list(agent_states.keys()))
        
        # Grid layout rendering settings
        margin_x = 20
        start_y = 30
        box_width = 80
        
        for i, agent_id in enumerate(agents):
            # Evaluate if the agent is currently active based on the timeout
            last_active = agent_states[agent_id]
            is_active = (current_time - last_active) < TIMEOUT
            
            x_pos = margin_x + (i * (box_width + 15))
            
            # 1. Render Graphic / Animation
            if has_assets:
                img = img_working if is_active else img_sleeping
                screen.blit(img, (x_pos + (box_width//2 - 16), start_y))
            else:
                # Fallback: Green square for working, dark gray for sleeping
                color = (0, 230, 115) if is_active else (50, 50, 50)
                pygame.draw.rect(screen, color, (x_pos + (box_width//2 - 16), start_y, 32, 32))
                if not is_active:
                    # Render a subtle 'Zz' indicator in fallback mode
                    zzz_text = font.render("Zz", True, (100, 100, 100))
                    screen.blit(zzz_text, (x_pos + (box_width//2 + 10), start_y - 10))

            # 2. Render Status Text ("WORKING" / "SLEEPING")
            status_str = "WORKING" if is_active else "SLEEPING"
            status_color = (0, 230, 115) if is_active else (150, 150, 150)
            status_text = font.render(status_str, True, status_color)
            screen.blit(status_text, (x_pos + (box_width//2 - status_text.get_width()//2), start_y + 40))

            # 3. Render Agent ID (Truncated if too long for the box layout)
            display_id = agent_id if len(agent_id) <= 10 else agent_id[:8] + ".."
            id_text = font.render(display_id, True, (240, 240, 240))
            screen.blit(id_text, (x_pos + (box_width//2 - id_text.get_width()//2), start_y + 55))

        pygame.display.flip()
        clock.tick(30)  # Capping at 30 FPS dramatically reduces host CPU usage

    pygame.quit()

# --- 5. APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    print("Starting OpenClaw Monitor...")
    update_agent_list()
    
    # Initialize and start the Watchdog filesystem observer in a separate background thread
    watcher_observer = start_file_watcher()
    
    # Run the main UI loop (must remain on the main thread for GUI rendering)
    try:
        main_ui()
    finally:
        # Ensure the background thread is cleanly stopped when the application exits
        watcher_observer.stop()
        watcher_observer.join()
        print("Monitor cleanly terminated.")
