import os
import json

def load_data(file_path):
    """Reads the JSON commands file and optionally warns if duplicate keys are detected."""
    if not os.path.exists(file_path):
        print(f"WARNING: Configuration file NOT FOUND at {file_path}", flush=True)
        return {}

    # Check environment variable to see if detection is enabled (Default: True)
    detect_enabled = os.getenv('DETECT_DUPLICATES', 'True').lower() == 'true'

    def detect_duplicates(pairs):
        """
        Hook to detect duplicate keys during JSON parsing recursively.
        Only prints warnings if DETECT_DUPLICATES is enabled.
        """
        result = {}
        for key, value in pairs:
            if key in result and detect_enabled:
                print(f"CRITICAL WARNING: Duplicate key '{key}' detected in {file_path}!", flush=True)
                print(f" -> Level Context: Overwriting previous value with new definition for '{key}'.", flush=True)
            result[key] = value
        return result

    with open(file_path, 'r') as f:
        try:
            # If enabled, use the hook to monitor for duplicates at every level of {}
            if detect_enabled:
                return json.load(f, object_pairs_hook=detect_duplicates)
            else:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: {file_path} contains invalid JSON syntax.", flush=True)
            return {}

def get_combined_blocks(data, channel_id_str):
    """Combines channel-specific blocks with global wildcard blocks."""
    # Ensure data is a dictionary to prevent crashes on malformed group definitions
    if not isinstance(data, dict):
        return []
        
    specific = data.get(channel_id_str, [])
    global_star = data.get("*", [])
    global_all = data.get("all", [])
    
    return specific + global_star + global_all
