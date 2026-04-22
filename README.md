# 🤖 Discord Terminal Bot (Docker Edition)

A secure, Docker-integrated Discord bot that allows authorized users to execute server-side commands via Discord Slash Commands (`/exec`). This bot is designed to run within an isolated container while maintaining the ability to manage the host's Docker engine and execute local scripts.

---

## 🛠 1. Discord Developer Portal Setup

Before the bot can function, you must register the application and configure the necessary privileged intents.

1.  **Create Application:** Go to the [Discord Developer Portal](https://discord.com) and click **New Application**.
2.  **Create Bot User:** Navigate to the **Bot** tab and click **Add Bot**.
3.  **Enable Privileged Intents:** Under the **Bot** tab, scroll down to the **Privileged Gateway Intents** section and toggle **ON**:
    *   **SERVER MEMBERS INTENT**: **Critical.** Required for the bot to check user roles for blacklist/whitelist logic.
    *   **MESSAGE CONTENT INTENT**: Required for the bot to sync and process slash command inputs.
4.  **Reset/Copy Token:** Click **Reset Token** to generate your bot's unique token. Save this for your configuration.
5.  **OAuth2 URL Generator (Invite Bot):**
    *   Go to **OAuth2** -> **URL Generator**.
    *   Check `bot` and `applications.commands`.
    *   Under **Bot Permissions**, check: `Send Messages`, `Use Slash Commands`, `Read Message History`.
    *   Copy the generated URL into your browser to invite the bot to your server.

---

## ⚙️ 2. Configuration & Environment

### Environment Variables (.env)
The bot requires a `.env` file in the root directory to store sensitive credentials:
*   `DISCORD_TOKEN`: Your unique bot token from the Developer Portal.
*   `OWNER_ID`: Your numerical Discord User ID (Bypasses all permission checks).

### Docker Compose Parameters
*   **`PYTHONUNBUFFERED=1`**: Forces Python to flush logs immediately to the Docker console for real-time monitoring.
*   **`LOG_FILE`**: (Optional) Path to a log file (e.g., `commands/bot_log.txt`). If left blank, whitespace, or removed, the bot will log **only** to the Docker console.
*   **User**: `user: root` is required in the compose file to allow the bot to interact with the Docker socket.
*   **Volumes**: 
    *   `./commands:/app/commands`: Maps your local configuration, scripts, and logs.
    *   `/var/run/docker.sock:/var/run/docker.sock`: Provides the bot permission to control other containers on the host.

---

## 📄 3. Command Dictionary (commands.json)

The bot reads `commands/commands.json` in real-time for every command. You can update this file without restarting the container.

### Structure
Each **Channel ID** (or the wildcards `"*"` or `"all"`) maps to an **Array (List)** of command blocks. This allows you to stack different sets of commands with varying permissions in the same channel.

```json
{
  "*": [
    {
      "comment": "Global commands available in every channel to everyone",
      "commands": {
        "ping": "echo 'pong'",
        "uptime": "uptime -p"
      }
    }
  ],
  "YOUR_CHANNEL_ID_HERE": [
    {
      "comment": "Restricted Admin Commands",
      "permissions": {
        "whitelist_roles": [987654321],
        "blacklist_users": [123456789],
        "whitelist_users": [],
        "blacklist_roles": []
      },
      "commands": {
        "restart_web": "docker restart website_container",
        "update_scripts": "sh /app/commands/update.sh"
      }
    },
    {
      "comment": "Public commands allowed in this specific channel",
      "commands": {
        "list_backups": "ls /app/commands/backups"
      }
    }
  ]
}

## 🚀 4. Installation & Deployment
Follow these steps to deploy the bot on your server:
- File Preparation: Ensure bot.py, Dockerfile, docker-compose.yml, requirements.txt, and .env are all present in your project root directory.
- Initialization: Create a subfolder named commands/ and place your commands.json inside it.
- Building and Starting: Open your terminal in the project root and execute docker compose up --build -d. This command builds the image with the Docker CLI and launches the bot as a background service.
- Live Monitoring: To see command execution results and internal bot logs in real-time, run docker compose logs -f.
- Applying Changes: If you modify the Dockerfile or requirements.txt, re-run docker compose up --build -d to refresh the container image.

## 🔍 5. Usage & Logic
Once deployed, the bot integrates into your server via Slash Commands:
- Interacting: Simply type /exec in a configured channel.
- Context-Aware Autocomplete: The command dropdown list dynamically filters aliases based on your specific User ID, Roles, and the Current Channel. Commands you are not authorized to run will be hidden.
- Real-time Config: You can edit commands.json on your server at any time. Changes take effect instantly without needing to restart the container.
- Permission Hierarchy:
  # Owner Bypass: The OWNER_ID defined in your .env file is exempt from all restrictions and can run any command.
  # Blacklist Priority: If a user or their role is blacklisted in a specific command block, they are denied immediately, even if they are whitelisted elsewhere.
  # Optional Permissions: If the permissions section or a specific whitelist is missing, the command set is public. If a whitelist is present, only those listed IDs/Roles can use the commands.
  # Wildcards: Command blocks assigned to "*" or "all" are automatically combined with channel-specific commands and available globally.

## 🛡 6. Security Information
Security is critical when allowing terminal access via a chat interface:
- Docker Socket: Mounting /var/run/docker.sock provides the bot with root-level access to your Docker engine. This allows it to manage other containers. Only whitelist trusted users and roles.
- Isolation: The bot is restricted to its container environment. It cannot access host system files unless they are specifically mounted as volumes in docker-compose.yml.
- Script Safety: When running shell scripts (.sh), ensure they have execution permissions on the host (e.g., chmod +x script.sh).
- Audit Trail: Every command attempt (Authorized or Denied) is logged to the Docker console and the optional LOG_FILE defined in your environment, providing a full history of user activity.
- Fail-safe Defaults: If the commands.json file is malformed or a permission block is missing, the bot handles errors gracefully without crashing, defaulting to the safest restricted state.

