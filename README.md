# 🤖 Discord Terminal Bot

A highly flexible, Docker-integrated Discord bot that allows authorized users to execute server-side commands and scripts via dynamic Slash Commands. This bot features an advanced validation engine, real-time configuration monitoring, and granular permission controls.

---

## 🛠 1. Discord Developer Portal Setup

Before deployment, you must register the bot and configure its permissions.

1.  **Create Application**: Go to the [Discord Developer Portal](https://discord.com) and click **New Application**.
2.  **Create Bot User**: Navigate to the **Bot** tab and click **Add Bot**.
3.  **Enable Privileged Intents**: Under the **Bot** tab, toggle **ON**:
    *   **SERVER MEMBERS INTENT**: **Critical.** Required for the bot to check user roles for permission logic.
    *   **MESSAGE CONTENT INTENT**: Required for command processing.
4.  **Token**: Click **Reset Token** to get your bot's unique token. Save this for your `.env` file.
5.  **Invite Bot**: 
    *   Go to **OAuth2** -> **URL Generator**.
    *   Check `bot` and `applications.commands`.
    *   Under **Bot Permissions**, check: `Send Messages`, `Use Slash Commands`, `Read Message History`.
    *   Copy the URL into your browser to add the bot to your server.

---

## ⚙️ 2. Configuration & Environment

The bot is configured entirely through Environment Variables and a JSON command dictionary.

### Environment Variables (.env)
*   `DISCORD_TOKEN`: Your unique bot token.
*   `OWNER_ID`: Your Discord User ID (Bypasses all blacklist/whitelist checks).
*   `COMMANDS_FILE`: Path to your JSON config (e.g., `commands/commands.json`).
*   `LOG_FILE`: (Optional) Path to a persistent log file.
*   `LOADING_TIMEOUT`: Time in seconds (default `1.5`) before the "Loading" message appears for long-running commands.

---

## 📄 3. Command Configuration (commands.json)

The bot monitors this file in the background. Adding a new top-level key registers a new Slash Command with Discord automatically within 60 seconds.

### **Configuration Structure Example**
```json
{
  "play": {
    "parameter_name": "game",
    "loading_message": "🎲 *Rolling the dice...*",
    "*": [
      {
        "comment": "Public games with a specific user blacklist",
        "permissions": { "blacklist_users": [333333333] },
        "commands": {
          "Roll a D20": { 
            "command": "bash -c 'echo $(( (RANDOM % 20) + 1 ))'",
            "prepend": "🎲 **Result:** "
          },
          "GuessWhat": "echo 'Chicken butt!!'",
          "moo": "fortune -a | cowsay"
        }
      }
    ]
  },
  "ai": {
    "parameter_name": "prompt",
    "loading_message": "🤖 *Querying Ollama AI...*",
    "1234567890": [
      {
        "comment": "Admin-only AI access in a specific channel",
        "permissions": { "whitelist_roles": [999999999] },
        "commands": {
          "ask": "python3 /app/commands/query_ollama.py --prompt"
        }
      }
    ]
  }
}
```

---

## 🚀 4. Installation & Deployment

1.  **Project Structure**: Ensure your project is organized as follows:
    *   `bot.py`: Main entry point.
    *   `lib/`: Contains `auth.py`, `data_manager.py`, `logger.py`, and `validation.py`.
    *   `commands/`: Contains `commands.json` and any local scripts (e.g., `.sh`, `.py`).
2.  **Launch**: Execute the following command from the root directory:
    ```bash
    docker compose up --build -d
    ```
3.  **Monitor**: View real-time activity and startup logs:
    ```bash
    docker compose logs -f
    ```

---

## 🔍 5. Functionality & Logic

### **Dynamic Slash Commands**
*   **Root Keys**: Every top-level key in your JSON becomes a unique `/command`.
*   **Parameter Names**: Defined by `parameter_name` in JSON (e.g., `/play game:` vs `/ai prompt:`).
*   **Live Updates**: Changes inside command blocks are **instant**. New root-level commands sync within **60 seconds**.

### **Advanced Validation Engine**
Commands can include a `validation` block to check output before displaying it:
*   `==`: Direct string equality.
*   `contains`: Checks if output contains a string (supports `and`/`or` lists).
*   `within`: Checks if output exists inside a larger provided string.
*   `>` / `<`: Numerical comparison (if output is an integer or decimal).
*   `not`: Negates any validation rule.
*   `result`: Compares the command output against the result of a *second* shell command.

### **Permission Hierarchy**
1.  **Owner Bypass**: The `OWNER_ID` is never restricted.
2.  **Blacklist (Priority)**: Any user or role in a `blacklist_` is denied immediately.
3.  **Whitelist**: If defined, only listed users/roles can see and use the command.
4.  **Wildcards**: Support for `"*"` or `"all"` in blacklists to lock down commands to the Owner only.

---

## 🛡 6. Security Information

*   **Docker Isolation**: The bot runs in a container. It can only interact with the host or other containers via the mounted `/var/run/docker.sock`.
*   **Read-Only Access**: For maximum security, mount sensitive volumes as `:ro` (read-only) in `docker-compose.yml`.
*   **Script Safety**: Ensure all scripts in the `commands/` folder use **LF** line endings (not CRLF) and have execution permissions (`chmod +x`).
*   **Audit Trail**: Every command attempt—including user IDs, channel IDs, and success/fail status—is logged to the console and the optional `LOG_FILE`.
