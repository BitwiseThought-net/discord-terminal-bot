# 🗺️ System Architecture: The Digital Paper Trail

This project implements a real-time configuration loop between a **React Dashboard**, a **Node.js API**, and a **Python Discord Bot**. This document tracks the flow of data through the system.

## 🔄 The Data Lifecycle

### 1. The Source of Truth (Disk)
The journey begins at the file path defined by `COMMANDS_FILE` in the `.env` file (defaulting to `commands/commands.json`). 
* **Docker Volume Mapping:** Through `docker-compose`, the host's `./commands` folder is mounted to `/app/commands` in both the Bot and Editor containers, ensuring they always see the exact same data.

### 2. The API Bridge (Node.js/Express)
When the Editor UI is opened, the Node.js backend (`web-server.js`) acts as the gatekeeper:
* **Fetching:** Upon a `GET /api/commands` request, the server reads the raw bytes from the disk, parses them into JSON, and serves them to the frontend.
* **Initialization:** If the file is missing, the server automatically clones `commands.json.example` to ensure zero-config startups.

### 3. The Visual Brain (React & Monaco)
The frontend (`App.js`) provides the interface:
* **State Management:** Data is stored in React state and injected into the **Monaco Editor** (the engine behind VS Code) for high-fidelity editing.
* **Validation:** Before any data is sent back, the UI validates the JSON structure. If you miss a comma or a bracket, the UI blocks the save and alerts you, preventing the bot from crashing.

### 4. The Round Trip (Persistence)
When you click **Save Changes**:
* **Payload:** `axios` sends a `POST` request with the updated JSON string.
* **Commit:** Node.js receives the payload and uses `fs.writeFileSync` to overwrite the physical file on the disk.

### 5. The Active Reload (Python Bot)
The Discord Bot (`bot.py`) completes the loop:
* **File Watching:** The bot is configured to monitor `commands.json` for changes.
* **Hot-Reloading:** The moment the Editor writes the file to disk, the bot detects the update and reloads its command registry.
* **Result:** Changes made in the web browser are live in Discord instantly—**without restarting the bot.**

---

## 🏗️ Technical Stack
- **Frontend:** React, Monaco Editor, Axios.
- **Backend:** Node.js, Express.
- **Bot:** Python 3.11, Discord.py.
- **Orchestration:** Docker & Docker Compose.
