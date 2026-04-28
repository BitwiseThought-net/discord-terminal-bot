const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const COMMANDS_DIR = path.join(__dirname, 'commands');
const JSON_PATH = path.join(COMMANDS_DIR, 'commands.json');
const EXAMPLE_PATH = path.join(COMMANDS_DIR, 'commands.json.example');

const ensureFileExists = () => {
    if (!fs.existsSync(JSON_PATH)) {
        if (fs.existsSync(EXAMPLE_PATH)) {
            console.log("commands.json missing. Initializing from example...");
            fs.copyFileSync(EXAMPLE_PATH, JSON_PATH);
        } else {
            console.log("Creating empty commands file...");
            fs.writeFileSync(JSON_PATH, JSON.stringify({ commands: [] }, null, 4));
        }
    }
};

app.get('/api/commands', (req, res) => {
    ensureFileExists();
    try {
        const data = fs.readFileSync(JSON_PATH, 'utf8');
        res.json(JSON.parse(data));
    } catch (err) {
        res.status(500).json({ error: "Read Error" });
    }
});

app.post('/api/commands', (req, res) => {
    try {
        const newData = JSON.stringify(req.body, null, 4);
        fs.writeFileSync(JSON_PATH, newData);
        res.status(200).json({ message: "Saved" });
    } catch (err) {
        res.status(500).json({ error: "Write Error" });
    }
});

app.get(/^\/(?!api).*/, (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = 80;
app.listen(PORT, () => {
    console.log(`Editor Backend running on port ${PORT}`);
    ensureFileExists();
});
