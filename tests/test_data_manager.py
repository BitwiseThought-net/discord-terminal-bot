import os
import pytest
import json
from lib.data_manager import load_data

# Helper to create a temporary JSON file with duplicate keys
def create_duplicate_json(path):
    content = '{"cmd": {"param": "val1", "param": "val2"}}'
    with open(path, 'w') as f:
        f.write(content)

def test_load_data_detects_duplicates(caplog, tmp_path):
    """Verify that duplicate keys trigger a log warning when enabled."""
    json_file = tmp_path / "dup.json"
    create_duplicate_json(json_file)
    
    # Enable detection
    os.environ['DETECT_DUPLICATES'] = 'True'
    
    # We check the 'terminal_bot' logger at the WARNING level
    with caplog.at_level("WARNING"):
        data = load_data(str(json_file))
    
    # Verify 'last one wins' logic
    assert data["cmd"]["param"] == "val2"
    
    # Verify the log message exists in captured logs
    assert "Duplicate key 'param'" in caplog.text

def test_load_data_ignores_duplicates_when_disabled(caplog, tmp_path):
    """Verify that duplicate keys do NOT trigger a log warning when disabled."""
    json_file = tmp_path / "dup.json"
    create_duplicate_json(json_file)
    
    # Disable detection
    os.environ['DETECT_DUPLICATES'] = 'False'
    
    caplog.clear()
    with caplog.at_level("WARNING"):
        data = load_data(str(json_file))
    
    # Logic should still work
    assert data["cmd"]["param"] == "val2"
    
    # Log should be empty of duplicate warnings
    assert "Duplicate key" not in caplog.text

def test_load_data_file_not_found(caplog):
    """Verify warning when file is missing."""
    caplog.clear()
    with caplog.at_level("WARNING"):
        data = load_data("non_existent_file.json")
        
    assert data == {}
    assert "Configuration file NOT FOUND" in caplog.text
