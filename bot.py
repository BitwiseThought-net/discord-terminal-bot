import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 1. SETUP & CREDENTIALS
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
LOG_FILE = os.getenv('LOG_FILE', '').strip()

try:
    # OWNER_ID from .env is the ultimate bypass for all checks
    OWNER_ID = int(os.getenv('OWNER_ID'))
except (TypeError, ValueError):
    OWNER_ID = None

# Set up intents (Server Members is required for role-based checks)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

COMMANDS_FILE = 'commands/commands.json'

# 2. UTILITY FUNCTIONS
def load_data():
    """Reads the JSON commands file in real-time."""
    if not os.path.exists(COMMANDS_FILE):
        return {}
    with open(COMMANDS_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("ERROR: commands.json contains invalid JSON syntax.", flush=True)
            return {}

def log_text(user, channel_id, text):
    """Logs to both the Docker console and the optional LOG_FILE."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User: {user} ({user.id}) | Channel: {channel_id} | Text: {text}"

    # Always log to Docker (Standard Output)
    print(log_entry, flush=True)

    # Log to file ONLY if LOG_FILE environment variable is valid
    if LOG_FILE:
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Logging Error: Could not write to {LOG_FILE}. {e}", flush=True)


def log_action(user, channel_id, about, status):
    """Logs to both the Docker console and the optional LOG_FILE."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User: {user} ({user.id}) | Channel: {channel_id} | About: {about} | Status: {status}"

    # Always log to Docker (Standard Output)
    print(log_entry, flush=True)

    # Log to file ONLY if LOG_FILE environment variable is valid
    if LOG_FILE:
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Logging Error: Could not write to {LOG_FILE}. {e}", flush=True)

def is_authorized(user, permissions):
    """Checks for wildcards (* or all) and IDs in blacklist/whitelist."""
    if user.id == OWNER_ID:
        return True, "Owner Bypass"

    user_role_ids = [role.id for role in user.roles]
    wildcards = ["*", "all"]

    # 1. Blacklist Check (Priority)
    bl_users = permissions.get("blacklist_users", [])
    bl_roles = permissions.get("blacklist_roles", [])

    # Check for wildcards in blacklist
    if any(w in bl_users for w in wildcards) or any(w in bl_roles for w in wildcards):
        return False, "Global Blacklist Imposed"

    # Check specific IDs in blacklist
    if user.id in bl_users:
        return False, "User Blacklisted"
    if any(r_id in bl_roles for r_id in user_role_ids):
        return False, "Role Blacklisted"

    # 2. Whitelist Check (Optional)
    white_u = permissions.get("whitelist_users", [])
    white_r = permissions.get("whitelist_roles", [])

    # If no whitelist is defined, access is granted to non-blacklisted users
    if not white_u and not white_r:
        return True, "Public Access"

    # Check for wildcards in whitelist
    if any(w in white_u for w in wildcards) or any(w in white_r for w in wildcards):
        return True, "Global Whitelist Access"

    # Check specific IDs in whitelist
    if user.id in white_u:
        return True, "User Whitelisted"
    if any(r_id in white_r for r_id in user_role_ids):
        return True, "Role Whitelisted"

    return False, "Unauthorized (Not on Whitelist)"

def get_combined_blocks(data, channel_id_str):
    """Combines channel-specific blocks with global wildcard blocks."""
    specific = data.get(channel_id_str, [])
    global_star = data.get("*", [])
    global_all = data.get("all", [])
    return specific + global_star + global_all

# 3. BOT EVENTS
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'--- Bot Online as {bot.user} ---', flush=True)
    if LOG_FILE:
        print(f'File Logging: {LOG_FILE}', flush=True)

# 4. SLASH COMMAND & AUTOCOMPLETE
@bot.tree.command(name="funfact", description="Run an authorized command")
@app_commands.describe(about="The command nickname from commands.json")
async def execute_alias(interaction: discord.Interaction, about: str):
    data = load_data()
    channel_id_str = str(interaction.channel_id)
    all_blocks = get_combined_blocks(data, channel_id_str)

    target_cmd = None
    last_reason = "Command not found."
    search_about = about.lower() # Case-insensitive normalization

    for block in all_blocks:
        cmds = block.get("commands", {})

        # Create a lowercase map for case-insensitive lookup
        normalized_cmds = {k.lower(): (k, v) for k, v in cmds.items()}

        if search_about in normalized_cmds:
            actual_key, cmd_value = normalized_cmds[search_about]
            allowed, reason = is_authorized(interaction.user, block.get("permissions", {}))
            if allowed:
                target_cmd = cmd_value
                break
            else:
                last_reason = reason

    if not target_cmd:
        log_action(interaction.user, channel_id_str, about, f"DENIED: {last_reason}")
        await interaction.response.send_message(f"❌ Access Denied: {last_reason}", ephemeral=True)
        return

    await interaction.response.defer()

    try:
        process = await asyncio.create_subprocess_shell(
            target_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        log_action(interaction.user, channel_id_str, about, "SUCCESS")
        result = (stdout.decode() or stderr.decode()).strip() or "Success."

        if len(result) > 1900:
            result = result[:1900] + "\n...[Truncated]..."

        #await interaction.followup.send(f"**Alias:** `{alias}`\n```\n{result[:1900]}\n```")
        await interaction.followup.send(f"`FunFact about {about}`\n```\n{result[:1900]}\n```")
        #await interaction.followup.send(f"```\n{result}\n```")

    except Exception as e:
        log_action(interaction.user, channel_id_str, about, f"ERROR: {str(e)}")
        await interaction.followup.send(f"⚠️ Error: `{str(e)}`")

@execute_alias.autocomplete('about')
async def alias_autocomplete(interaction: discord.Interaction, current: str):
    """Dropdown menu with case-insensitive filtering."""
    data = load_data()
    channel_id_str = str(interaction.channel_id)
    all_blocks = get_combined_blocks(data, channel_id_str)

    choices, seen = [], set()
    search_current = current.lower()

    for block in all_blocks:
        allowed, _ = is_authorized(interaction.user, block.get("permissions", {}))
        if allowed:
            cmds = block.get("commands", {})
            for name in cmds.keys():
                if search_current in name.lower() and name not in seen:
                    choices.append(app_commands.Choice(name=name, value=name))
                    seen.add(name)

    return choices[:25]

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("CRITICAL: DISCORD_TOKEN missing in .env.")
