import json
import os
from datetime import datetime

LOGS_DIR  = "logs"
TOOLS_DIR = "tools"

os.makedirs(LOGS_DIR,  exist_ok=True)
os.makedirs(TOOLS_DIR, exist_ok=True)


# ---------------------------
# SAFE JSON LOADER (core fix)
# ---------------------------
def safe_load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r") as f:
            content = f.read().strip()
            if not content:
                return default
            return json.loads(content)
    except (json.JSONDecodeError, OSError):
        print(f"⚠️ Corrupted or unreadable file: {path} → resetting")
        return default


# ---------------------------
# GET ALL TOOLS
# ---------------------------
def get_all_tools():
    tools = {}

    for f in os.listdir(TOOLS_DIR):
        if f.endswith(".json"):
            path = os.path.join(TOOLS_DIR, f)

            data = safe_load_json(path, None)
            if not data:
                continue

            # extra safety
            if "name" in data:
                tools[data["name"]] = data

    return tools


# ---------------------------
# SAVE TOOL
# ---------------------------
def save_tool(name, description, code, success_rate=1.0):
    tool = {
        "name":         name,
        "description":  description,
        "code":         code,
        "success_rate": success_rate,
        "created":      datetime.now().isoformat(),
        "uses":         0,
        "fails":        0,
    }

    path = os.path.join(TOOLS_DIR, f"{name}.json")

    try:
        with open(path, "w") as f:
            json.dump(tool, f, indent=2)
    except OSError as e:
        print(f"❌ Failed to save tool {name}: {e}")


# ---------------------------
# UPDATE TOOL SCORE
# ---------------------------
def update_tool_score(name, success: bool):
    path = os.path.join(TOOLS_DIR, f"{name}.json")

    tool = safe_load_json(path, None)
    if not tool:
        return

    tool["uses"] = tool.get("uses", 0) + 1

    if not success:
        tool["fails"] = tool.get("fails", 0) + 1
    else:
        tool["fails"] = tool.get("fails", 0)

    # avoid division by zero
    if tool["uses"] > 0:
        tool["success_rate"] = round(
            1 - (tool["fails"] / tool["uses"]), 2
        )

    try:
        with open(path, "w") as f:
            json.dump(tool, f, indent=2)
    except OSError as e:
        print(f"❌ Failed to update tool {name}: {e}")


# ---------------------------
# LOG INTERACTION (FIXED)
# ---------------------------
def log_interaction(user_input, tool_used, success, error=None):
    log = {
        "time":    datetime.now().isoformat(),
        "input":   user_input,
        "tool":    tool_used,
        "success": success,
        "error":   error,
    }

    logfile = os.path.join(
        LOGS_DIR,
        f"log_{datetime.now().strftime('%Y%m%d')}.json"
    )

    logs = safe_load_json(logfile, [])

    logs.append(log)

    try:
        with open(logfile, "w") as f:
            json.dump(logs, f, indent=2)
    except OSError as e:
        print(f"❌ Failed to write log: {e}")


# ---------------------------
# GET WEAK TOOLS
# ---------------------------
def get_weak_tools():
    tools = get_all_tools()

    return [
        t for t in tools.values()
        if t.get("success_rate", 1) < 0.7 and t.get("uses", 0) > 2
    ]