const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();

// Middleware: Parse JSON and serve the React build folder
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

/**
 * PATH CONFIGURATION
 * Loads from .env (e.g., COMMANDS_FILE=commands/commands.json)
 * We resolve it based on __dirname to ensure it works inside Docker.
 */
const relativePath = process.env.COMMANDS_FILE || 'commands/commands.json';
const JSON_PATH = path.resolve(__dirname, relativePath);
const EXAMPLE_PATH = `${JSON_PATH}.example`;
const COMMANDS_DIR = path.dirname(JSON_PATH);

/**
 * Ensures the commands file exists. 
 * Automatically initializes from .example if the main file is missing.
 */
const ensureFileExists = () => {
    if (!fs.existsSync(JSON_PATH)) {
        if (fs.existsSync(EXAMPLE_PATH)) {
            console.log(`[Init] Copying ${EXAMPLE_PATH} to ${JSON_PATH}`);
            fs.copyFileSync(EXAMPLE_PATH, JSON_PATH);
        } else {
            console.log(`[Init] Creating new empty commands file at ${JSON_PATH}`);
            if (!fs.existsSync(COMMANDS_DIR)) fs.mkdirSync(COMMANDS_DIR, { recursive: true });
            fs.writeFileSync(JSON_PATH, JSON.stringify({ commands: [] }, null, 4));
        }
    }
};

// --- API ROUTES ---

// Get JSON Data
app.get('/api/commands', (req, res) => {
    ensureFileExists();
    try {
        const data = fs.readFileSync(JSON_PATH, 'utf8');
        res.json(JSON.parse(data));
    } catch (err) {
        console.error("Read Error:", err);
        res.status(500).json({ error: "Could not read commands file." });
    }
});

// Update JSON Data
app.post('/api/commands', (req, res) => {
    try {
        const newData = JSON.stringify(req.body, null, 4);
        fs.writeFileSync(JSON_PATH, newData);
        console.log(`[Update] ${JSON_PATH} updated successfully.`);
        res.status(200).json({ message: "Saved!" });
    } catch (err) {
        console.error("Write Error:", err);
        res.status(500).json({ error: "Failed to write updates to file." });
    }
});

/**
 * CATCH-ALL ROUTE (REGEX FIX)
 * Serves the React frontend for any path that isn't /api.
 * Prevents the PathToRegexp 'Unexpected Token' error.
 */
app.get(/^\/(?!api).*/, (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

/**
 * SERVER START LOGIC
 * Only starts the listener if this file is run directly (node web-server.js).
 * This prevents Jest from throwing EACCES errors on Port 80 during tests.
 */
if (require.main === module) {
    const PORT = 80;
    app.listen(PORT, () => {
        console.log(`\n--- Editor Backend ---`);
        console.log(`Target File: ${JSON_PATH}`);
        console.log(`Internal Port: ${PORT}`);
        console.log(`----------------------\n`);
        ensureFileExists();
    });
}

/**
 * EXPORT FOR TESTING
 * Required so Supertest can hook into the app without conflicting ports.
 */
module.exports = app;
