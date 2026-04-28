const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const relativePath = process.env.COMMANDS_FILE || 'commands/commands.json';
const JSON_PATH = path.resolve(__dirname, relativePath);
const EXAMPLE_PATH = `${JSON_PATH}.example`;
const COMMANDS_DIR = path.dirname(JSON_PATH);

const ensureFileExists = () => {
    if (!fs.existsSync(JSON_PATH)) {
        if (fs.existsSync(EXAMPLE_PATH)) {
            console.log(`[Init] Copying ${EXAMPLE_PATH} to ${JSON_PATH}`);
            fs.copyFileSync(EXAMPLE_PATH, JSON_PATH);
        } else {
            console.log(`[Init] Creating new empty file at ${JSON_PATH}`);
            // Ensure directory exists before writing
            if (!fs.existsSync(COMMANDS_DIR)) fs.mkdirSync(COMMANDS_DIR, { recursive: true });
            fs.writeFileSync(JSON_PATH, JSON.stringify({ commands: [] }, null, 4));
        }
    }
};

// API: Fetch JSON data
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

// API: Update JSON data
app.post('/api/commands', (req, res) => {
    try {
        const newData = JSON.stringify(req.body, null, 4);
        fs.writeFileSync(JSON_PATH, newData);
        console.log(`[Update] ${JSON_PATH} updated successfully.`);
        res.status(200).json({ message: "Saved!" });
    } catch (err) {
        console.error("Write Error:", err);
        res.status(500).json({ error: "Failed to write updates." });
    }
});

/**
 * CATCH-ALL ROUTE (REGEX FIX)
 * Serves the React frontend for any path that isn't /api.
 * This prevents the 'PathError' restart loop.
 */
app.get(/^\/(?!api).*/, (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start Server
const PORT = 80;
app.listen(PORT, () => {
    console.log(`\n--- Editor Backend ---`);
    console.log(`Target File: ${JSON_PATH}`);
    console.log(`Internal Port: ${PORT}`);
    console.log(`----------------------\n`);
    ensureFileExists();
});
