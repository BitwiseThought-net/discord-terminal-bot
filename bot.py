import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# 1. SETUP & CREDENTIALS
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
LOG_FILE = os.getenv('LOG_FILE', '').strip()
COMMANDS_FILE = os.getenv('COMMANDS_FILE', 'commands/commands.json').strip()

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

# 2. UTILITY FUNCTIONS
def load_data():
    """Reads the JSON commands file in real-time if it exists."""
    if not os.path.exists(COMMANDS_FILE):
        print(f"WARNING: Configuration file NOT FOUND at {COMMANDS_FILE}", flush=True)
        return {}
    with open(COMMANDS_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: {COMMANDS_FILE} contains invalid JSON syntax.", flush=True)
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

def log_action(user, channel_id, slash_cmd, param_val, status):
    """Logs to both the Docker console and the optional LOG_FILE."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] User: {user} ({user.id}) | Channel: {channel_id} | /{slash_cmd}: {param_val} | Status: {status}"
    
    # Always log to Docker (Standard Output)
    print(log_entry, flush=True)
    
    # Log to file ONLY if LOG_FILE environment variable is valid
    if LOG_FILE:
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Logging Error: {e}", flush=True)

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

# 3. DYNAMIC LOGIC GENERATORS
def create_callback(cmd_name, param_name):
    # We use 'query' as a fixed internal name for the argument
    async def callback(interaction: discord.Interaction, query: str):
        # We treat 'query' as the value of the parameter defined in JSON
        param_value = query
        
        if not param_value:
            return await interaction.response.send_message("❌ Missing parameter.", ephemeral=True)
            
        data = load_data().get(cmd_name, {})
        all_blocks = get_combined_blocks(data, str(interaction.channel_id))
        target_cmd, last_reason = None, "Not found"
        search_val = param_value.lower()
        
        for block in all_blocks:
            cmds = block.get("commands", {})
            # Create a lowercase mapping for case-insensitive lookup
            norm_cmds = {k.lower(): (k, v) for k, v in cmds.items()}
            if search_val in norm_cmds:
                actual_key, cmd_string = norm_cmds[search_val]
                allowed, reason = is_authorized(interaction.user, block.get("permissions", {}))
                if allowed:
                    target_cmd = cmd_string
                    break
                else:
                    last_reason = reason
                    
        if not target_cmd:
            log_action(interaction.user, interaction.channel_id, cmd_name, param_value, f"DENIED: {last_reason}")
            return await interaction.response.send_message(f"❌ {last_reason}", ephemeral=True)
            
        await interaction.response.defer()
        
        try:
            process = await asyncio.create_subprocess_shell(target_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            log_action(interaction.user, interaction.channel_id, cmd_name, param_value, "SUCCESS")
            result = (stdout.decode() or stderr.decode()).strip() or "Success."
            await interaction.followup.send(f"`{cmd_name.capitalize()} {param_name}: {param_value}`\n```\n{result[:1900]}\n```")
        except Exception as e:
            await interaction.followup.send(f"⚠️ Error: `{e}`")
            
    return callback

def create_autocomplete(cmd_name):
    async def autocomplete(interaction: discord.Interaction, current: str):
        data = load_data().get(cmd_name, {})
        all_blocks = get_combined_blocks(data, str(interaction.channel_id))
        choices, seen = [], set()
        search_curr = current.lower()
        
        for block in all_blocks:
            # Check permissions for autocomplete visibility
            allowed, _ = is_authorized(interaction.user, block.get("permissions", {}))
            if allowed:
                cmds = block.get("commands", {})
                for name in cmds.keys():
                    if search_curr in name.lower() and name not in seen:
                        choices.append(app_commands.Choice(name=name, value=name))
                        seen.add(name)
                        
        return choices[:25]
        
    return autocomplete

# 4. MONITOR & REGISTRATION
async def sync_commands_from_json():
    # Verify file exists before trying to sync
    if not os.path.exists(COMMANDS_FILE):
        print(f"Sync Aborted: {COMMANDS_FILE} does not exist.", flush=True)
        return

    data = load_data()
    existing_cmds = [cmd.name for cmd in bot.tree.get_commands()]
    new_found = False
    
    for cmd_name, config in data.items():
        if cmd_name not in existing_cmds:
            # Extract specific parameter name from JSON
            param_name = config.get("parameter_name", "about")
            
            # 1. Generate the callback function
            callback = create_callback(cmd_name, param_name)
            
            # 2. Rename the internal 'query' arg to the JSON's 'param_name'
            # Note: We must register autocomplete to the INTERNAL name 'query'
            renamed_callback = app_commands.rename(query=param_name)(callback)
            described_callback = app_commands.describe(query=f"Select {param_name}")(renamed_callback)
            
            # 3. Create the dynamic command object
            new_cmd = app_commands.Command(
                name=cmd_name,
                description=f"Commands for {cmd_name}",
                callback=described_callback
            )
            
            # 4. Register autocomplete to the specific renamed parameter
            new_cmd.autocomplete('query')(create_autocomplete(cmd_name))
            
            bot.tree.add_command(new_cmd)
            print(f"Detected and registered new command: /{cmd_name} [{param_name}]", flush=True)
            new_found = True
            
    if new_found:
        await bot.tree.sync()
        print("Slash commands re-synced with Discord.", flush=True)

@tasks.loop(minutes=1)
async def check_for_new_commands():
    if not bot.is_ready():
        return
    await sync_commands_from_json()

# 5. BOT EVENTS
@bot.event
async def on_ready():
    # Log starting configuration
    print(f"Targeting COMMANDS_FILE: {COMMANDS_FILE}", flush=True)
    
    # Initial registration
    await sync_commands_from_json()
    
    # Start the background monitor
    if not check_for_new_commands.is_running():
        check_for_new_commands.start()
        
    print(f'--- {bot.user} Online | Monitor Active ---', flush=True)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("CRITICAL: DISCORD_TOKEN missing in .env.")

