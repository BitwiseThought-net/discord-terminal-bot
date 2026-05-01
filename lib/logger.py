import logging
import sys

# Configure the logging format and level
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("terminal_bot")

def log_action(user, channel_id, slash_cmd, param_val, status):
    """Logs action details using the standard logging library."""
    user_id = getattr(user, 'id', 'Unknown')
    user_name = str(user)
    message = f"User: {user_name} ({user_id}) | Channel: {channel_id} | /{slash_cmd}: {param_val} | Status: {status}"
    logger.info(message)

def log_text(user, channel_id, text):
    """Logs raw text events using the standard logging library."""
    user_id = getattr(user, 'id', 'System' if str(user) == 'System' else 'Unknown')
    user_name = str(user)
    message = f"User: {user_name} ({user_id}) | Channel: {channel_id} | Text: {text}"
    logger.info(message)

def log_warn(text):
    """Logs system warnings."""
    logger.warning(text)

def log_error(text):
    """Logs system errors."""
    logger.error(text)
