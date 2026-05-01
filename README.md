# 🤖 Discord Terminal Bot

A **Programmable Discord-to-System Interface** designed to bridge the gap between chat-based interaction and server-side shell execution. This project provides a secure, modular framework for triggering, validating, and managing complex terminal operations through a structured automation engine.

But what IS it??
Well... It's a highly flexible, Docker-integrated Discord bot that allows authorized users to execute server-side commands and scripts via dynamic Slash Commands. This bot features an advanced recursive validation engine, real-time configuration monitoring, and granular permission controls.

In short....
This project is a High-Stability Command Orchestration Platform that effectively transforms Discord into a mobile command center for server management. At its core, the tool bridges the gap between chat-based interactions and secure server-side shell execution through a modular, JSON-driven architecture.
Unlike standard bots that simply 'echo' terminal output, this platform features a sophisticated Recursive Validation Engine. It can interrogate command results using fuzzy string matching via the Damerau-Levenshtein algorithm, perform complex numerical comparisons, and handle stateful interpolation ... *INHALE* ... allowing one command's output to serve as a variable for the next. This enables complex workflows, from infrastructure monitoring to interactive logic-based games like Pig, all without touching the source code.
To ensure professional-grade reliability, the entire system is built as a Dockerized monorepo with a Node.js/React-based Web Editor for real-time configuration. Most importantly, the project adheres to a 100% Code Coverage standard across both its Python and Node.js components. Every logic branch and error handler is protected by an automated BYO CI/CD pipeline, ensuring that the bot remains secure and responsive even under heavy load or configuration changes. It’s the ideal solution for developers who demand the flexibility of a remote terminal with the rigorous safety and testing standards of enterprise software.

.... "short".

## 🚀 Core Functionality

### 🛠️ Dynamic Command Mapping
*   **JSON-Driven Architecture**: Commands are defined as data, mapping Discord Slash Commands directly to shell scripts or terminal utilities without requiring source code modifications.
*   **Hot-Reloading**: The bot monitors configuration changes in real-time, allowing for instant updates to the command library across Discord.

### 🧠 Advanced Validation & Logic Engine
*   **Fuzzy String Matching**: Implemented **Damerau-Levenshtein** algorithm to handle typos and near-matches in terminal output.
*   **Numerical & Logical Operators**: Supports complex comparisons (`>`, `<=`, etc.) and recursive logic (`and`, `or`, `not`) to evaluate command results.
*   **Stateful Interpolation**: Captures and stores output from sub-processes into temporary variables for cross-command comparison and response formatting.

### 🖥️ Integrated Web Dashboard
*   **Headless Management**: A dedicated **Node.js/React** editor provides a graphical interface for managing the command library.
*   **Shared Volume Architecture**: Leveraging Docker volumes, the dashboard and bot stay perfectly synchronized, ensuring a "Single Point of Truth" configuration.

### 🔒 Multi-Layered Security & Permissions
*   **Hierarchical Access**: Granular **Whitelist** and **Blacklist** controls for specific Discord Users and Roles.
*   **Global Wildcards**: Support for root-level settings (`*`) that apply to all commands or specific command groups.
*   **Owner Fail-safe**: A hard-coded administrator bypass ensuring persistent access even in the event of configuration errors.

### ⚡ Performance & Feedback
*   **Intelligent Async Loading**: An asynchronous execution system that triggers customizable "Processing..." messages for high-latency scripts.
*   **Standardized Logging**: Full integration with Python’s standard `logging` library to maintain a robust, Docker-compatible audit trail.
*   **Response Formatting**: Dynamic `prepend` and `append` templates to wrap raw terminal data in clean, readable Discord markdown.

### 🧪 The Gold Standard of Reliability
*   **100% Code Coverage**: Both the Python Bot engine and the Node.js API are verified with **100% unit test coverage**, ensuring every error handler and logic branch is protected by CI/CD quality gates.


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
*   `LOADING_TIMEOUT`: Seconds to wait (default `1.5`) before showing the loading message.
*   `DETECT_DUPLICATES`: (Boolean) If `True`, the bot warns you in the console if duplicate keys are found in your JSON.

---

## 📄 3. Command Configuration (commands.json)

The bot monitors this file in the background. Adding a new top-level key registers a new Slash Command with Discord automatically within 60 seconds.

### **Configuration Structure Example**
```json
{
  "*": {
    "*": [
      {
        "comment": "Global shared commands, available to all slash-commands",
        "commands": {
          "date": { "command": "date" }
        }
      }
    ]
  },
  "play": {
    "parameter_name": "game",
    "loading_message": "🎲 *Rolling the dice...*",
    "*": [
      {
        "comment": "Public games with a specific user blacklist",
        "permissions": { "blacklist_users": [333333333] },
        "commands": {
          "GuessWhat": "echo 'Chicken butt!!'",
          "moo": "fortune -a | cowsay",
          "mooooooooooooooo": "fortune -l | cowsay",
          "no": "/app/commands/no-as-a-service.sh",
          "nooooooooooooooo": "/app/commands/no-as-a-service.sh | cowsay",
          "Roll a D20": { 
            "command": "bash -c 'echo $(( (RANDOM % 20) + 1 ))'",
            "prepend": "🎲 **Result:** "
          },
          "Pig": {
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
          "ask": "python3 /app/commands/ollama_client.py --prompt"
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
*   **Audit Trail**: All attempts (User, Channel, Command, and Status) are logged to the console.
*   **Read-Only Access**: For maximum security, mount sensitive volumes as `:ro` (read-only) in `docker-compose.yml`.
*   **Script Safety**: Ensure all scripts in the `commands/` folder use **LF** line endings (not CRLF) and have execution permissions (`chmod +x`).
*   **Audit Trail**: Every command attempt (including user IDs, channel IDs, and success/fail status) is logged to the console and the optional `LOG_FILE`.

## 🛠️ Internal Systems
For a detailed look at how data moves from the commands json, edited by the included dashboard editor, to be loaded by the Discord bot, see the [System Architecture Guide](./ARCHITECTURE.md).

## 👩‍💻 For Developers
Interested in contributing or modifying the bot? See our [Development Guide](./DEVELOPMENT.md).

