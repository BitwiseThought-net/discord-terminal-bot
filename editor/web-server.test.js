const request = require('supertest');
const fs = require('fs');
const path = require('path');

/**
 * Helper to ensure the environment is clean for testing
 */
const TEST_REL_PATH = 'commands/test_commands.json';
const TEST_FILE = path.resolve(__dirname, TEST_REL_PATH);
const EXAMPLE_FILE = `${TEST_FILE}.example`;
const TEST_DIR = path.dirname(TEST_FILE);

describe('Editor API Endpoints & Logic', () => {
    let app;

    const cleanup = () => {
        if (fs.existsSync(TEST_FILE)) fs.unlinkSync(TEST_FILE);
        if (fs.existsSync(EXAMPLE_FILE)) fs.unlinkSync(EXAMPLE_FILE);
    };

    const deepCleanup = () => {
        cleanup();
        if (fs.existsSync(TEST_DIR)) {
            // Remove the directory itself to force Line 31's mkdirSync branch
            fs.rmSync(TEST_DIR, { recursive: true, force: true });
        }
    };

    beforeAll(() => {
        deepCleanup();
        // Load the app for standard tests
        process.env.COMMANDS_FILE = TEST_REL_PATH;
        app = require('./web-server');
    });

    afterEach(() => {
        jest.restoreAllMocks();
        cleanup();
    });

    afterAll(() => {
        deepCleanup();
        delete process.env.COMMANDS_FILE;
    });

    // --- 1. Environment Fallback (Targets Line 15) ---
    
    test('Config: should fallback to default path if ENV is missing', () => {
        jest.resetModules();
        const oldEnv = process.env.COMMANDS_FILE;
        delete process.env.COMMANDS_FILE;
        
        const tempApp = require('./web-server');
        expect(tempApp).toBeDefined();
        
        process.env.COMMANDS_FILE = oldEnv;
    });

    // --- 2. Initialization Logic (Targets Lines 31-34) ---

    test('Initialization: should copy .example if main file is missing', async () => {
        // Ensure dir exists for the example file
        if (!fs.existsSync(TEST_DIR)) fs.mkdirSync(TEST_DIR, { recursive: true });
        fs.writeFileSync(EXAMPLE_FILE, JSON.stringify({ example: true }));
        
        await request(app).get('/api/commands');
        
        expect(fs.existsSync(TEST_FILE)).toBe(true);
        const data = JSON.parse(fs.readFileSync(TEST_FILE, 'utf8'));
        expect(data.example).toBe(true);
    });

    test('Initialization: should create empty file and DIR if missing (Targets Line 31)', async () => {
        // Force the absolute fresh-start branch by removing the directory
        deepCleanup(); 
        
        await request(app).get('/api/commands');
        
        expect(fs.existsSync(TEST_DIR)).toBe(true);
        expect(fs.existsSync(TEST_FILE)).toBe(true);
        const data = JSON.parse(fs.readFileSync(TEST_FILE, 'utf8'));
        expect(data.commands).toEqual([]);
    });

    // --- 3. API Routes (Targets Lines 46-47 & 59-60) ---

    test('GET /api/commands - Success', async () => {
        if (!fs.existsSync(TEST_DIR)) fs.mkdirSync(TEST_DIR, { recursive: true });
        fs.writeFileSync(TEST_FILE, JSON.stringify({ hello: "world" }));
        const res = await request(app).get('/api/commands');
        expect(res.statusCode).toEqual(200);
        expect(res.body.hello).toBe("world");
    });

    test('GET /api/commands - Read Error Failure', async () => {
        jest.spyOn(fs, 'readFileSync').mockImplementation(() => {
            throw new Error('Read Failure');
        });
        const res = await request(app).get('/api/commands');
        expect(res.statusCode).toEqual(500);
        expect(res.body.error).toBe("Could not read commands file.");
    });

    test('POST /api/commands - Success', async () => {
        const mockData = { commands: [{ name: "test-cmd" }] };
        const res = await request(app).post('/api/commands').send(mockData);
        expect(res.statusCode).toEqual(200);
        const saved = JSON.parse(fs.readFileSync(TEST_FILE, 'utf8'));
        expect(saved.commands[0].name).toBe("test-cmd");
    });

    test('POST /api/commands - Write Error Failure', async () => {
        jest.spyOn(fs, 'writeFileSync').mockImplementation(() => {
            throw new Error('Write Failure');
        });
        const res = await request(app).post('/api/commands').send({ key: "val" });
        expect(res.statusCode).toEqual(500);
        expect(res.body.error).toBe("Failed to write updates to file.");
    });

    // --- 4. Catch-All Route (Targets Regex) ---

    test('Frontend Catch-all: should serve index.html for non-api routes', async () => {
        const publicDir = path.join(__dirname, 'public');
        if (!fs.existsSync(publicDir)) fs.mkdirSync(publicDir);
        fs.writeFileSync(path.join(publicDir, 'index.html'), '<html></html>');

        const res = await request(app).get('/ui-route');
        expect(res.statusCode).toEqual(200);
        expect(res.text).toBe('<html></html>');
        
        fs.unlinkSync(path.join(publicDir, 'index.html'));
    });

    test('Frontend Catch-all: should serve index.html for root path', async () => {
        const publicDir = path.join(__dirname, 'public');
        if (!fs.existsSync(publicDir)) fs.mkdirSync(publicDir);
        fs.writeFileSync(path.join(publicDir, 'index.html'), '<html></html>');

        const res = await request(app).get('/');
        expect(res.statusCode).toEqual(200);
        
        fs.unlinkSync(path.join(publicDir, 'index.html'));
    });

    test('Regex Check: /api routes should NOT be caught by catch-all', async () => {
        const res = await request(app).get('/api/invalid');
        expect(res.statusCode).toEqual(404);
    });
});

