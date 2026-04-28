# 🗺️ System Architecture: The Digital Paper Trail

This project implements a real-time configuration loop between a **React Dashboard**, a **Node.js API**, and a **Python Discord Bot**. This document tracks the flow of data through the system.

## 🔄 The Data Lifecycle

### 1. The Source of Truth (Disk)
The journey begins at the file path defined by the `COMMANDS_FILE` environment variable in the `.env` file (defaulting to `commands/commands.json`). 
* **Docker Volume Mapping:** Through `docker-compose`, the host's `./commands` folder is mounted to `/app/commands` in both the Bot and Editor containers. This ensures they always interact with the **exact same physical bits** on the disk.

### 2. The API Bridge (Node.js/Express)
When the Editor UI is opened, the Node.js backend (`web-server.js`) acts as the gatekeeper:
* **Environment-Driven Pathing:** The server resolves the `COMMANDS_FILE` variable to an absolute path within the container.
* **Fetching:** Upon a `GET /api/commands` request, the server reads the raw bytes from the disk, parses them into JSON, and serves them to the frontend.
* **Auto-Initialization:** If the file is missing, the server automatically clones `commands.json.example` to ensure a "Plug-and-Play" experience for new users.

### 3. The Visual Brain (React & Monaco)
The frontend (`App.js`) provides the high-fidelity interface:
* **State Management:** Data is fetched via `axios` and injected into the **Monaco Editor** (the engine behind VS Code) for syntax highlighting and easy editing.
* **Validation:** Before any data is sent back, the UI runs `JSON.parse` to validate the structure. If a comma or bracket is missing, the UI blocks the save and alerts the user, preventing a corrupt config from ever hitting the disk.

### 4. The Round Trip (Persistence)
When you click **Save Changes**:
* **Payload:** `axios` sends the updated JSON back to the Node API via a `POST` request.
* **Commit:** `web-server.js` receives the payload and uses `fs.writeFileSync` to overwrite the physical file on the disk.
* **Routing Safety:** The backend uses a specific **Regex Catch-All** (`/^\/(?!api).*/`) to ensure that frontend navigation never interferes with these critical API requests.

### 5. The Active Reload (Python Bot)
The Discord Bot (`bot.py`) completes the loop:
* **File Watching:** The bot is configured to monitor the `COMMANDS_FILE` for changes.
* **Hot-Reloading:** The moment the Editor writes the file to disk, the bot detects the update and reloads its command registry.
* **Result:** Changes made in the web browser are live in Discord instantly—**without restarting the bot.**

---

## 🏗️ Technical Stack
- **Frontend:** React, Monaco Editor, Axios.
- **Backend:** Node.js (v18+), Express.
- **Bot:** Python 3.11, Discord.py.
- **Orchestration:** Docker & Docker Compose.
- **Quality Control:** Jest (Backend), React Testing Library (Frontend), Husky (Git Hooks).

## 🛠️ Troubleshooting the Data Flow

If changes made in the Editor are not appearing in Discord (or vice versa), follow this "Measure Twice" checklist to locate the bottleneck.

### 1. The "Volume Sync" Check
**Problem:** You save in the Editor, but the `commands.json` file on your host machine hasn't changed.
*   **Cause:** Sometimes the Docker daemon loses track of file change events, especially on Windows (WSL2) or macOS.
*   **Fix:** Run `npm run docker:reset` from the root. This forces Docker to unmount and remount the volumes, refreshing the "portal" between your host and the container.

### 2. Permission Mismatches (`EACCES`)
**Problem:** The Editor logs show "Permission Denied" when trying to save.
*   **Cause:** The `commands.json` file might have been created by the root user inside a container, making it un-writable by your local user or the Node.js process.
*   **Fix:** Run `npm run clean:local` from the root. Our custom script uses a temporary Docker container with root privileges to scrub and reset these file permissions.

### 3. Verification Commands
Use these "inside-out" checks to see what each service is actually seeing:
*   **Check Editor's view:** `docker compose exec discord-terminal-bot-editor cat /app/commands/commands.json`
*   **Check Bot's view:** `docker compose exec discord-terminal-bot cat /app/commands/commands.json`
*   **If the views differ:** Your volume mapping in `docker-compose.yml` is likely pointing to the wrong host directory.

### 4. API Pre-flight Failures (CORS)
**Problem:** The Editor UI stays stuck on "Loading..." or shows a Network Error in the browser console.
*   **Cause:** If you are accessing the dashboard via an IP address instead of `localhost`, the browser might block requests.
*   **Fix:** Ensure you are using `http://localhost:1701`. If using a remote server, you must update the `cors` settings in `web-server.js` to permit your specific domain.

---
*Measure twice, cut once.*
