import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';

function App() {
  const [code, setCode] = useState('// Loading commands.json...');
  const [status, setStatus] = useState('');

  // Load the JSON on startup
  useEffect(() => {
    axios.get('/api/commands')
      .then(res => setCode(JSON.stringify(res.data, null, 4)))
      .catch(err => setStatus('Error loading file: ' + err.message));
  }, []);

  const handleSave = () => {
    try {
      const parsedData = JSON.parse(code); // Validate JSON before sending
      setStatus('Saving...');
      axios.post('/api/commands', parsedData)
        .then(() => setStatus('Saved successfully!'))
        .catch(err => setStatus('Save failed: ' + err.message));
    } catch (e) {
      setStatus('Invalid JSON: ' + e.message);
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#1e1e1e', color: 'white' }}>
      <header style={{ padding: '10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333' }}>
        <h2 style={{ margin: 0 }}>Command Editor</h2>
        <div>
          <span style={{ marginRight: '15px', color: status.includes('Error') || status.includes('Invalid') ? '#ff5f56' : '#00ca4e' }}>{status}</span>
          <button onClick={handleSave} style={{ padding: '8px 20px', cursor: 'pointer', backgroundColor: '#0078d4', color: 'white', border: 'none', borderRadius: '4px' }}>
            Save Changes
          </button>
        </div>
      </header>

      <div style={{ flexGrow: 1 }}>
        <Editor
          height="100%"
          defaultLanguage="json"
          theme="vs-dark"
          value={code}
          onChange={(value) => setCode(value)}
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            formatOnPaste: true,
            scrollBeyondLastLine: false,
          }}
        />
      </div>
    </div>
  );
}

export default App;
