import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Import refactored logic from the lib directory
from lib.validation import validate_output
from lib.data_manager import load_data, get_combined_blocks
from lib.auth import is_authorized
from lib.logger import log_action, log_text

# 1. SETUP & CREDENTIALS
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
LOG_FILE = os.getenv('LOG_FILE', '').strip()
# COMMANDS_FILE is now pulled from the environment variable set in docker-compose
COMMANDS_FILE = os.getenv('COMMANDS_FILE', 'commands/commands.json').strip()

# Fetch LOADING_TIMEOUT from environment with a default of 1.5
try:
    LOADING_TIMEOUT = float(os.getenv('LOADING_TIMEOUT', 1.5))
except (TypeError, ValueError):
    LOADING_TIMEOUT = 1.5

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

# 3. DYNAMIC LOGIC GENERATORS
def create_callback(cmd_name, param_name):
    # We use 'query' as a fixed internal name for the argument
    async def callback(interaction: discord.Interaction, query: str):
        # We treat 'query' as the value of the parameter defined in JSON
        param_value = query
        
        if not param_value:
            return await interaction.response.send_message("❌ Missing parameter.", ephemeral=True)
            
        full_data = load_data(COMMANDS_FILE)
        cmd_group_config = full_data.get(cmd_name, {})
        all_blocks = get_combined_blocks(cmd_group_config, str(interaction.channel_id))
        
        target_cmd, last_reason = None, "Not found"
        prepend_str, append_str, validation_rules = "", "", None
        search_val = param_value.lower()
        
        for block in all_blocks:
            cmds = block.get("commands", {})
            # Create a lowercase mapping for case-insensitive lookup
            norm_cmds = {k.lower(): (k, v) for k, v in cmds.items()}
            
            if search_val in norm_cmds:
                actual_key, cmd_data = norm_cmds[search_val]
                allowed, reason = is_authorized(interaction.user, block.get("permissions", {}), OWNER_ID)
                
                if allowed:
                    # Support both string format and object format for commands
                    if isinstance(cmd_data, dict):
                        target_cmd = cmd_data.get("command")
                        prepend_str = cmd_data.get("prepend", "")
                        append_str = cmd_data.get("append", "")
                        validation_rules = cmd_data.get("validation")
                    else:
                        target_cmd = cmd_data
                    break
                else:
                    last_reason = reason
                    
        if not target_cmd:
            log_action(interaction.user, interaction.channel_id, cmd_name, param_value, f"DENIED: {last_reason}", LOG_FILE)
            return await interaction.response.send_message(f"❌ {last_reason}", ephemeral=True)
            
        await interaction.response.defer()

        # Prep loading text with fallback
        loading_text = cmd_group_config.get("loading_message")
        if not loading_text or not str(loading_text).strip():
            loading_text = "Processing..."

        # Create the subprocess task but don't 'await' it immediately
        process_task = asyncio.create_task(asyncio.create_subprocess_shell(
            target_cmd, 
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        ))

        loading_msg = None
        try:
            # Wait for parameterized LOADING_TIMEOUT. If the task finishes, it goes to 'done'.
            done, pending = await asyncio.wait([process_task], timeout=LOADING_TIMEOUT)

            if not done:
                # Command is taking longer than the timeout, send the loading message
                loading_msg = await interaction.followup.send(loading_text)
                # Now wait for it to finish completely
                process = await process_task
            else:
                # Command finished instantly!
                process = process_task.result()

            stdout, stderr = await process.communicate()
            log_action(interaction.user, interaction.channel_id, cmd_name, param_value, "SUCCESS", LOG_FILE)
            
            # Decode and strip standard output
            cmd_output = (stdout.decode() or stderr.decode()).strip()
            
            # Run validation logic if rules are present (Awaited from the imported lib function)
            if validation_rules:
                if not await validate_output(cmd_output, validation_rules):
                    cmd_output = "Validation failed"
            
            # Apply Prepend and Append logic
            final_result = f"{prepend_str}{cmd_output}{append_str}"
            
            output_content = f"`{cmd_name.capitalize()} {param_name}: {param_value}`\n```\n{final_result[:1900]}\n```"
            
            if loading_msg:
                await loading_msg.edit(content=output_content)
            else:
                await interaction.followup.send(output_content)
                
        except Exception as e:
            err_text = f"⚠️ Error: `{e}`"
            if loading_msg:
                await loading_msg.edit(content=err_text)
            else:
                await interaction.followup.send(err_text)
            
    return callback

def create_autocomplete(cmd_name):
    async def autocomplete(interaction: discord.Interaction, current: str):
        full_data = load_data(COMMANDS_FILE)
        cmd_group_config = full_data.get(cmd_name, {})
        all_blocks = get_combined_blocks(cmd_group_config, str(interaction.channel_id))
        choices, seen = [], set()
        search_curr = current.lower()
        
        for block in all_blocks:
            # Check permissions for autocomplete visibility
            allowed, _ = is_authorized(interaction.user, block.get("permissions", {}), OWNER_ID)
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

    data = load_data(COMMANDS_FILE)
    existing_cmds = [cmd.name for cmd in bot.tree.get_commands()]
    new_found = False
    
    for cmd_name, config in data.items():
        if cmd_name not in existing_cmds:
            # Extract specific parameter name from JSON (defaults to 'about')
            param_name = config.get("parameter_name", "about")
            
            # 1. Generate the callback function
            callback = create_callback(cmd_name, param_name)
            
            # 2. Rename the internal 'query' arg to the JSON's 'param_name'
            # and add a description for the Discord UI.
            renamed_callback = app_commands.rename(query=param_name)(callback)
            described_callback = app_commands.describe(query=f"Select {param_name}")(renamed_callback)
            
            # 3. Create the dynamic command object
            new_cmd = app_commands.Command(
                name=cmd_name,
                description=f"Commands for {cmd_name}",
                callback=described_callback
            )
            
            # 4. Register autocomplete to the internal parameter name 'query'
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
    print(f"Loading Timeout set to: {LOADING_TIMEOUT}s", flush=True)
    
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

