# 🛠️ Development Guide

This document outlines the development workflow, testing procedures, and maintenance commands for the Discord Terminal Bot and Editor.

## 🚀 Getting Started

1. **Enable Git Hooks**:
   Run `npm install` in the root directory. This automatically initializes **Husky** to protect the branch from broken code.
2. **Environment Setup**:
   Ensure your `.env` file contains the `COMMANDS_FILE` path (e.g., `COMMANDS_FILE=commands/commands.json`).
3. **Launch the Stack**:
   ```bash
   docker compose up --build -d
   ```
# 🧪 Testing Strategy

## 🧪 Testing & CI
We use a "Layered Defense" to ensure code quality across the Python and Node.js components. 
This project uses **Husky** for pre-push hooks and **GitHub Actions** for PR verification.
- To run tests locally: `npm test --prefix editor`
- All PRs must pass CI checks before they can be merged.


## 🏃 Running Tests

We use a "Layered Defense" to ensure code quality:
To verify the code locally, you can use the following orchestrator commands from the **root** directory.

### Local Checks (Pre-Push Git Hooks)
Every time you `git push`, the system automatically runs:
- **Backend Tests**: Validates the Express API logic.
- **Frontend Tests**: Ensures the React UI components render correctly.

To run these manually:
- Run all tests: `npm run test:all`
- Editor only: `npm run test:editor`
- Dashboard only: `npm run test:dashboard`


| Command | Scope | Description |
| :--- | :--- | :--- |
| `npm run test:all` | **Full Project** | This will automatically install any missing dependencies and run the full suite for both the backend and frontend. |
| `npm run test:editor` | **Backend API** | Runs Jest tests for the Node.js Express server. |
| `npm run test:dashboard` | **Frontend UI** | Runs React Testing Library for the Dashboard. |
> **Note:** By default, these commands suppress security audits to keep output clean. To see full vulnerability reports, run `npm run install:all:audit`.

## 🛡️ Security Audits
By default, `npm run test:all` suppresses security audits to keep the output clean.
To perform a full security check across all sub-projects, run:
```bash
npm run install:all:audit
```

### Remote Checks (GitHub Actions)
Every Pull Request to `main` triggers the **CI Quality Gate**. This runs in a clean Ubuntu environment to verify that your changes are safe for production.

## 🧹 Maintenance & Cleanup
Docker builds and Python execution can accumulate "layer bloat" and cache files. Use these root-level shortcuts to keep your system lean:

| Command | Description |
| :--- | :--- |
| `npm run docker:clean` | Removes dangling image layers (Safe for regular use). |
| `npm run docker:purge` | **Nuclear Option**: Removes all unused images and volumes. |
| `npm run docker:reset` | Fully stops the project, wipes volumes, and rebuilds from scratch. |
| `npm run clean:local` | Deletes all local `node_modules`, build files, and Python `__pycache__`. |

## 🗺️ Architecture Reference
For a deep dive into how data moves through this project, refer to the [System Architecture Guide](./ARCHITECTURE.md).

---
*Measure twice, cut once.*
