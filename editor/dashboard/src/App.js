import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';

function App() {
  const [code, setCode] = useState('// Loading commands.json...');
  const [status, setStatus] = useState('Checking system status...');

  // 1. Load the JSON on startup
  useEffect(() => {
    axios.get('/api/commands')
      .then(res => {
        // Stringify with 4-space indentation for readability
        setCode(JSON.stringify(res.data, null, 4));
        setStatus('Ready');
      })
      .catch(err => {
        const errorMsg = err.response?.data?.error || err.message;
        setStatus('Error loading file: ' + errorMsg);
      });
  }, []);

  // 2. Handle the Save process
  const handleSave = () => {
    try {
      // Step A: Client-side validation
      // This prevents sending broken JSON to your bot!
      const parsedData = JSON.parse(code);

      setStatus('Saving to disk...');

      // Step B: Send to Node.js Backend
      axios.post('/api/commands', parsedData)
        .then(() => {
          setStatus('Saved successfully!');
          // Clear the status message after 3 seconds
          setTimeout(() => setStatus('Ready'), 3000);
        })
        .catch(err => {
          const errorMsg = err.response?.data?.error || err.message;
          setStatus('Save failed: ' + errorMsg);
        });
    } catch (e) {
      // Catch syntax errors before the request is even made
      setStatus('Invalid JSON Syntax: ' + e.message);
    }
  };

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#1e1e1e',
      color: 'white',
      fontFamily: 'sans-serif'
    }}>
      {/* Header Bar */}
      <header style={{
        padding: '10px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid #333',
        backgroundColor: '#252526'
      }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.2rem', color: '#0078d4' }}>Bot Command Editor</h2>
          <small style={{ color: '#888' }}>Editing: commands.json</small>
        </div>

        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{
            marginRight: '20px',
            fontSize: '0.9rem',
            color: status.includes('Error') || status.includes('Invalid') ? '#ff5f56' : '#00ca4e'
          }}>
            {status}
          </span>
          <button
            onClick={handleSave}
            style={{
              padding: '8px 24px',
              cursor: 'pointer',
              backgroundColor: '#0078d4',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontWeight: 'bold',
              transition: 'background 0.2s'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#005a9e'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#0078d4'}
          >
            Save Changes
          </button>
        </div>
      </header>

      {/* Code Editor Container */}
      <div style={{ flexGrow: 1, overflow: 'hidden' }}>
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
            automaticLayout: true,
            tabSize: 4
          }}
        />
      </div>
    </div>
  );
}

export default App;
