const request = require('supertest');
const fs = require('fs');
const path = require('path');

// 1. Force the environment variable BEFORE requiring the app
process.env.COMMANDS_FILE = 'commands/test_commands.json';
const app = require('./web-server');

// 2. Calculate the exact same path the server uses
const TEST_FILE = path.resolve(__dirname, process.env.COMMANDS_FILE);
const TEST_DIR = path.dirname(TEST_FILE);

describe('Editor API Endpoints', () => {

  // Create test directory and cleanup before/after
  const cleanup = () => { if (fs.existsSync(TEST_FILE)) fs.unlinkSync(TEST_FILE); };

  beforeAll(() => {
    if (!fs.existsSync(TEST_DIR)) fs.mkdirSync(TEST_DIR, { recursive: true });
    cleanup();
  });

  afterAll(cleanup);

  test('GET /api/commands should return 200', async () => {
    const res = await request(app).get('/api/commands');
    expect(res.statusCode).toEqual(200);
    expect(typeof res.body).toBe('object');
  });

  test('POST /api/commands should save data', async () => {
    const mockData = { commands: [{ name: "test-cmd" }] };
    const res = await request(app)
      .post('/api/commands')
      .send(mockData);

    expect(res.statusCode).toEqual(200);

    // 3. Verify it exists at the EXACT path the server wrote to
    expect(fs.existsSync(TEST_FILE)).toBe(true);

    // 4. Verify content matches
    const saved = JSON.parse(fs.readFileSync(TEST_FILE, 'utf8'));
    expect(saved.commands[0].name).toBe("test-cmd");
  });
});
