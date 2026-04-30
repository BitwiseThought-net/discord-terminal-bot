import os
import pytest
import json
from lib.data_manager import load_data

# Helper to create a temporary JSON file with duplicate keys
# standard json.dump cannot create duplicates, so we write the string manually
def create_duplicate_json(path):
    content = '{"cmd": {"param": "val1", "param": "val2"}}'
    with open(path, 'w') as f:
        f.write(content)

def test_load_data_detects_duplicates(capsys, tmp_path):
    """Verify that duplicate keys trigger a log warning when enabled."""
    json_file = tmp_path / "dup.json"
    create_duplicate_json(json_file)
    
    # 1. Enable detection
    os.environ['DETECT_DUPLICATES'] = 'True'
    data = load_data(str(json_file))
    
    # Verify 'last one wins' logic
    assert data["cmd"]["param"] == "val2"
    
    # Verify console output (captured by pytest capsys fixture)
    captured = capsys.readouterr()
    assert "CRITICAL WARNING: Duplicate key 'param'" in captured.out

def test_load_data_ignores_duplicates_when_disabled(capsys, tmp_path):
    """Verify that duplicate keys do NOT trigger a log warning when disabled."""
    json_file = tmp_path / "dup.json"
    create_duplicate_json(json_file)
    
    # 2. Disable detection
    os.environ['DETECT_DUPLICATES'] = 'False'
    data = load_data(str(json_file))
    
    # Logic should still work
    assert data["cmd"]["param"] == "val2"
    
    # Console should be clean
    captured = capsys.readouterr()
    assert "CRITICAL WARNING" not in captured.out

def test_load_data_file_not_found(capsys):
    """Verify warning when file is missing."""
    data = load_data("non_existent_file.json")
    assert data == {}
    captured = capsys.readouterr()
    assert "Configuration file NOT FOUND" in captured.out

