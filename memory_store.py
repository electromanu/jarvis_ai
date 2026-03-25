import json
import os
from datetime import datetime

MEMORY_FILE = "jarvis_memory.json"
jarvis_memory = {}
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "conversation_history": [],
            "user_preferences":     {},
            "frequent_commands":    {},
            "last_session":         None,
            "user_name":            "sir",
            "notes":                []
        }
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "conversation_history": [],
            "user_preferences":     {},
            "frequent_commands":    {},
            "last_session":         None,
            "user_name":            "sir",
            "notes":                []
        }

def save_memory(memory: dict):
    memory["last_session"] = datetime.now().isoformat()
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[JARVIS] Could not save memory: {e}")

def update_frequent_commands(memory: dict, command: str):
    freq = memory.get("frequent_commands", {})
    freq[command] = freq.get(command, 0) + 1
    memory["frequent_commands"] = freq

def get_top_commands(memory: dict, n=5):
    freq = memory.get("frequent_commands", {})
    sorted_cmds = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [cmd for cmd, count in sorted_cmds[:n]]

def add_note(memory: dict, note: str):
    notes = memory.get("notes", [])
    notes.append({
        "text": note,
        "time": datetime.now().isoformat()
    })
    memory["notes"] = notes[-50:]  # keep last 50 notes only

def get_session_summary(memory: dict):
    last = memory.get("last_session")
    top  = get_top_commands(memory, 3)
    name = memory.get("user_name", "sir")
    if last:
        return f"Welcome back {name}. Last session: {last[:10]}. Top commands: {', '.join(top) if top else 'none yet'}."
    return f"First time setup complete {name}. I am ready."