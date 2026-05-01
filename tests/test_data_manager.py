import os
import pytest
import json
from lib.data_manager import load_data, get_combined_blocks

# Helper to create a temporary JSON file with duplicate keys
def create_duplicate_json(path):
    # standard json.dump cannot create duplicates, so we write the string manually
    content = '{"cmd": {"param": "val1", "param": "val2"}}'
    with open(path, 'w') as f:
        f.write(content)

def test_load_data_detects_duplicates(caplog, tmp_path):
    """Verify that duplicate keys trigger a log warning when enabled."""
    json_file = tmp_path / "dup.json"
    create_duplicate_json(json_file)
    
    # Enable detection
    os.environ['DETECT_DUPLICATES'] = 'True'
    
    with caplog.at_level("WARNING"):
        data = load_data(str(json_file))
    
    # Verify 'last one wins' logic
    assert data["cmd"]["param"] == "val2"
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
    
    assert data["cmd"]["param"] == "val2"
    assert "Duplicate key" not in caplog.text

def test_load_data_file_not_found(caplog):
    """Verify warning when file is missing."""
    caplog.clear()
    with caplog.at_level("WARNING"):
        data = load_data("non_existent_file.json")
        
    assert data == {}
    assert "Configuration file NOT FOUND" in caplog.text

def test_get_combined_blocks_merging():
    """Verify that Global '*' blocks are merged into specific commands."""
    mock_data = {
        "*": {
            "*": [{"commands": {"global_cmd": "echo global"}}]
        },
        "play": {
            "*": [{"commands": {"specific_cmd": "echo specific"}}]
        }
    }
    
    # Check 'play' command in a random channel
    blocks = get_combined_blocks(mock_data, "play", "12345")
    
    # We expect 2 blocks (Specific first, Global second)
    assert len(blocks) == 2
    
    # Combine all commands from blocks to verify presence
    all_cmds = {}
    for b in blocks:
        all_cmds.update(b.get("commands", {}))
        
    assert "global_cmd" in all_cmds
    assert "specific_cmd" in all_cmds

def test_global_precedence_logic():
    """Verify that Specific command definitions override Global '*' definitions."""
    mock_data = {
        "*": {
            "*": [{"commands": {"version": "echo v1.0"}}]
        },
        "admin": {
            "*": [{"commands": {"version": "echo v2.0-beta"}}]
        }
    }
    
    # Get blocks for 'admin'
    blocks = get_combined_blocks(mock_data, "admin", "999")
    
    # Logic check: bot.py iterates through blocks and breaks at the first match.
    # Therefore, the first block in the list must be the specific one.
    first_block_cmds = blocks[0].get("commands", {})
    assert first_block_cmds["version"] == "echo v2.0-beta"
    
    # Second block should be the global fallback
    second_block_cmds = blocks[1].get("commands", {})
    assert second_block_cmds["version"] == "echo v1.0"

def test_get_combined_blocks_no_global():
    """Verify logic still works if no '*' root key exists."""
    mock_data = {
        "fun": {
            "all": [{"commands": {"ping": "pong"}}]
        }
    }
    blocks = get_combined_blocks(mock_data, "fun", "any_id")
    assert len(blocks) == 1
    assert blocks[0]["commands"]["ping"] == "pong"

def test_load_data_invalid_json(caplog):
    """Target the JSONDecodeError branch."""
    with open("invalid.json", "w") as f:
        f.write("{ invalid json: [ }")
    
    data = load_data("invalid.json")
    assert data == {}
    assert "invalid JSON syntax" in caplog.text
    os.remove("invalid.json")

def test_get_combined_blocks_malformed_input():
    """Target the 'if not isinstance(full_data, dict)' branch."""
    assert get_combined_blocks("not a dict", "cmd", "123") == []
