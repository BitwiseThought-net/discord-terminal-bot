from datetime import datetime

def log_action(user, channel_id, slash_cmd, param_val, status, log_file):
    """Logs to both the Docker console and the optional log_file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User: {user} ({user.id}) | Channel: {channel_id} | /{slash_cmd}: {param_val} | Status: {status}"
    
    print(log_entry, flush=True)
    
    if log_file:
        try:
            with open(log_file, 'a') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Logging Error: {e}", flush=True)

def log_text(user, channel_id, text, log_file):
    """Simplified text logger."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User: {user} ({user.id}) | Channel: {channel_id} | Text: {text}"
    print(log_entry, flush=True)
    if log_file:
        with open(log_file, 'a') as f:
            f.write(log_entry + "\n")
