# 🤖 Discord Terminal Bot

A highly flexible, Docker-integrated Discord bot that allows authorized users to execute server-side commands and scripts via dynamic Slash Commands. This bot features an advanced recursive validation engine, real-time configuration monitoring, and granular permission controls.

---

## 🛠 1. Discord Developer Portal Setup

Before deployment, you must register the bot and configure its permissions.

1.  **Create Application**: Go to the [Discord Developer Portal](https://discord.com) and click **New Application**.
2.  **Create Bot User**: Navigate to the **Bot** tab and click **Add Bot**.
3.  **Enable Privileged Intents**: Under the **Bot** tab, toggle **ON**:
    *   **SERVER MEMBERS INTENT**: **Critical.** Required for checking user roles for permission logic.
    *   **MESSAGE CONTENT INTENT**: Required for command processing.
4.  **Token**: Click **Reset Token** to get your bot's unique token. Save this for your `.env` file.
5.  **Invite Bot**: 
    *   Go to **OAuth2** -> **URL Generator**.
    *   Check `bot` and `applications.commands`.
    *   Under **Bot Permissions**, check: `Send Messages`, `Use Slash Commands`, `Read Message History`.
    *   Copy the URL into your browser to add the bot to your server.

---

## ⚙️ 2. Configuration & Environment

The bot is configured via Environment Variables in your `docker-compose.yml` and a JSON command dictionary.

### Environment Variables (.env)
*   `DISCORD_TOKEN`: Your unique bot token.
*   `OWNER_ID`: Your Discord User ID (Bypasses all blacklist/whitelist checks).
*   `COMMANDS_FILE`: Path to your JSON config (e.g., `commands/commands.json`).
*   `LOG_FILE`: (Optional) Path to a persistent log file (e.g., `commands/bot_log.txt`).
*   `LOADING_TIMEOUT`: Seconds to wait (default `1.5`) before showing the loading message.
*   `DETECT_DUPLICATES`: (Boolean) If `True`, the bot warns you in the console if duplicate keys are found in your JSON.

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
          "moo": "fortune -a | cowsay",
          "Oink": {
            "command": "bash -c 'echo $(( (RANDOM % 6) + 1 ))'",
            "key": "die1",
            "validation": {
              "!=": {
                "result": {
                  "command": "bash -c 'echo $(( (RANDOM % 6) + 1 ))'",
                  "key": "die2"
                }
              }
            },
            "output": {
              "pass": "✅ You win! 🎲{die1} & 🎲{die2} (No doubles)",
              "fail": "🐷 OINK! 🎲{die1} & 🎲{die2} (Doubles! You lose)"
            }
          }
        }
      }
    ]
  },
  "funfact": {
    "parameter_name": "about",
    "loading_message": "🕒 *Consulting the ancient scrolls...*",
    "*": [
      {
        "commands": {
          "linux": {
            "command": "fortune linux",
            "prepend": "🐧 **Linux Wisdom:**\n",
            "append": "\n*-- Source: fortune-mod*"
          }
        }
      }
    ]
  },
  "admin": {
    "parameter_name": "task",
    "1234567890": [
      {
        "commands": {
          "check_access": {
            "command": "whoami",
            "key": "user",
            "validation": {
              "==": {
                "result": {
                  "command": "grep 'admin' /app/data/config.txt 2>/dev/null | cut -d: -f2 | grep . || echo 'NONE'",
                  "key": "required_admin"
                }
              }
            },
            "output": {
              "pass": "PASSED: {user} is the authorized admin ({required_admin}).",
              "fail": "DENIED: User {user} does not match required admin {required_admin}."
            }
          }
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

1.  **Project Structure**:
    *   `bot.py`: Main entry point.
    *   `lib/`: Logic library (`auth.py`, `data_manager.py`, `logger.py`, `validation.py`).
    *   `commands/`: Configuration (`commands.json`) and scripts.
    *   `data/`: Persistent data files used by commands (e.g., `config.txt`).
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
*   **Parameter Names**: Custom-defined per command (e.g., `/play game:` vs `/ai prompt:`).
*   **Live Updates**: Changes inside command blocks are **instant**. New root-level commands sync within **60 seconds**.
*   **Autocomplete**: Dynamically filtered by channel and permissions; matches are case-insensitive.

### **Advanced Validation Engine**
Commands can include a `validation` block to check output. Logic can be nested with `and`, `or`, and `not`.
*   `==` / `!=`: Direct string equality or inequality.
*   `~=`: Approximate comparison (Fuzzy matching via Damerau-Levenshtein Distance).
*   `contains`: Checks if output contains a string or list of strings.
*   `within`: Checks if output exists inside a target string.
*   `>`, `<`, `>=`, `<=`: Numerical comparisons for integer or decimal outputs.
*   `result`: Compares command output against the result of a *second* shell command.

### **Dynamic Keys & Formatting**
*   **`key`**: Assign a key to a command or nested `result` to hold its output value.
*   **Interpolation**: Use `{key_name}` inside `prepend`, `append`, `validation`, or `output` strings to inject results dynamically from the execution context.

### **Permission Hierarchy**
1.  **Owner Bypass**: The `OWNER_ID` from `.env` is never restricted.
2.  **Blacklist (Priority)**: Immediate denial if a user/role is blacklisted.
3.  **Whitelist**: If defined, only listed users/roles can see or use the command.
4.  **Wildcards**: Support for `"*"` or `"all"` in blacklists to lock down blocks.

---

## 🛡 6. Security Information

*   **Docker Isolation**: The bot runs in a container. Interaction with the host or other containers is limited to the mounted `/var/run/docker.sock`.
*   **Input Safety**: Users can only select aliases defined in your JSON; they cannot type raw terminal commands directly into Discord.
*   **Audit Trail**: All attempts (User, Channel, Command, and Status) are logged to the console and the optional `LOG_FILE`.
*   **Read-Only Access**: For maximum security, mount sensitive volumes as `:ro` (read-only) in `docker-compose.yml`.
*   **Script Safety**: Ensure all scripts in the `commands/` folder use **LF** line endings (not CRLF) and have execution permissions (`chmod +x`).
*   **Audit Trail**: Every command attempt—including user IDs, channel IDs, and success/fail status—is logged to the console and the optional `LOG_FILE`.
