import os
import json

def load_data(file_path):
    """Reads the JSON commands file in real-time if it exists."""
    if not os.path.exists(file_path):
        print(f"WARNING: Configuration file NOT FOUND at {file_path}", flush=True)
        return {}
    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: {file_path} contains invalid JSON syntax.", flush=True)
            return {}

def get_combined_blocks(data, channel_id_str):
    """Combines channel-specific blocks with global wildcard blocks."""
    specific = data.get(channel_id_str, [])
    global_star = data.get("*", [])
    global_all = data.get("all", [])
    return specific + global_star + global_all
