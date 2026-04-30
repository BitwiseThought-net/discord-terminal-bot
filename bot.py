import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Import refactored logic from the lib directory
from lib.validation import validate_output, run_command
from lib.data_manager import load_data, get_combined_blocks
from lib.auth import is_authorized
from lib.logger import log_action, log_text, log_warn, log_error

# 1. SETUP & CREDENTIALS
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
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
        prepend_str, append_str, validation_rules, variable_key = "", "", None, None
        custom_output_config = None
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
                        variable_key = cmd_data.get("key")
                        custom_output_config = cmd_data.get("output")
                    else:
                        target_cmd = cmd_data
                    break
                else:
                    last_reason = reason
                    
        if not target_cmd:
            log_action(interaction.user, interaction.channel_id, cmd_name, param_value, f"DENIED: {last_reason}")
            return await interaction.response.send_message(f"❌ {last_reason}", ephemeral=True)
            
        await interaction.response.defer()

        # Prep loading text with fallback
        loading_text = cmd_group_config.get("loading_message")
        if not loading_text or not str(loading_text).strip():
            loading_text = "Processing..."

        # Create the subprocess task using the standardized library helper
        process_task = asyncio.create_task(run_command(target_cmd))

        loading_msg = None
        try:
            # Wait for parameterized LOADING_TIMEOUT. If the task finishes, it goes to 'done'.
            done, pending = await asyncio.wait([process_task], timeout=LOADING_TIMEOUT)

            if not done:
                # Command is taking longer than the timeout, send the loading message
                loading_msg = await interaction.followup.send(loading_text)
                # Now wait for it to finish completely
                cmd_output = await process_task
            else:
                # Command finished instantly!
                cmd_output = process_task.result()

            log_action(interaction.user, interaction.channel_id, cmd_name, param_value, "SUCCESS")
            
            # Build initial context for string interpolation
            context = {}
            if variable_key:
                context[variable_key] = cmd_output

            # Run validation logic (context updated by lib/validation.py if nested keys exist)
            validation_passed = True
            if validation_rules:
                validation_passed = await validate_output(cmd_output, validation_rules, context)

            # Determine Final Output
            if custom_output_config and isinstance(custom_output_config, dict):
                # Use custom pass/fail strings from JSON
                template = custom_output_config.get("pass" if validation_passed else "fail", "")
                try:
                    # Apply interpolation from the accumulated context
                    final_display = template.format(**context) if context else template
                except KeyError:
                    final_display = template
            else:
                # Use standard behavior (command output + prepend/append)
                display_text = cmd_output if validation_passed else "Validation failed"
                
                # Update main key in context if validation failed to reflect the error string
                if not validation_passed and variable_key:
                    context[variable_key] = display_text
                
                try:
                    final_prepend = prepend_str.format(**context) if context else prepend_str
                    final_append = append_str.format(**context) if context else append_str
                except KeyError:
                    final_prepend, final_append = prepend_str, append_str
                
                final_display = f"{final_prepend}{display_text}{final_append}"
            
            output_content = f"`{cmd_name.capitalize()} {param_name}: {param_value}`\n```\n{final_display[:1900]}\n```"
            
            if loading_msg:
                await loading_msg.edit(content=output_content)
            else:
                await interaction.followup.send(output_content)
                
        except Exception as e:
            err_text = f"⚠️ Error: `{e}`"
            log_error(f"Critical execution failure for {cmd_name}: {e}")
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
        log_warn(f"Sync Aborted: {COMMANDS_FILE} does not exist.")
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
            log_text(bot.user, "System", f"Registered new command: /{cmd_name} [{param_name}]")
            new_found = True
            
    if new_found:
        try:
            await bot.tree.sync()
            log_text(bot.user, "System", "Discord command tree synced successfully.")
        except Exception as e:
            log_error(f"Failed to sync command tree: {e}")

@tasks.loop(minutes=1)
async def check_for_new_commands():
    if not bot.is_ready():
        return
    await sync_commands_from_json()

# 5. BOT EVENTS
@bot.event
async def on_ready():
    # Log starting configuration
    log_text(bot.user, "System", f"Targeting COMMANDS_FILE: {COMMANDS_FILE}")
    log_text(bot.user, "System", f"Loading Timeout set to: {LOADING_TIMEOUT}s")
    
    # Initial registration
    await sync_commands_from_json()
    
    # Start the background monitor
    if not check_for_new_commands.is_running():
        check_for_new_commands.start()
        
    log_text(bot.user, "System", "Bot Online | Monitor Active")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        log_error("CRITICAL: DISCORD_TOKEN missing in .env.")

