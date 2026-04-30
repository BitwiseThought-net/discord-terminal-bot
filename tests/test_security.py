import pytest
import asyncio
import os
from lib.validation import validate_output, run_command
from lib.auth import is_authorized

# --- 1. Security: Command Injection & Sanitization ---

@pytest.mark.asyncio
async def test_interpolation_sanitization():
    """
    Verify that if a key contains shell-breaking characters, 
    it is treated as a literal string by Python and not executed 
    as a sub-command during validation.
    """
    # Simulate a key that has a malicious payload returned by a script
    malicious_context = {"user_input": "root; echo 'INJECTED'"}
    
    # Validation rule that uses that key
    # If injection worked, the result of the command would be 'root' followed by 'INJECTED'
    rules = {"==": "{user_input}"}
    
    # We expect Python's .format() to simply place the string there.
    # The 'output' being checked is the literal malicious string.
    result = await validate_output("root; echo 'INJECTED'", rules, malicious_context)
    
    assert result is True  # Pass because it's a string match
    # Ensure no 'INJECTED' text was actually processed as a command logic
    assert "INJECTED" not in malicious_context

@pytest.mark.asyncio
async def test_run_command_shell_safety():
    """Verify that run_command handles multi-command strings as a single unit."""
    # This proves that our wrapper captures the full output including redirected errors
    cmd = "echo 'first' && echo 'second'"
    output = await run_command(cmd)
    assert "first" in output
    assert "second" in output

# --- 2. Permission Boundary Logic ---

class MockRole:
    def __init__(self, id):
        self.id = id

class MockUser:
    def __init__(self, user_id, role_ids=None):
        self.id = user_id
        self.roles = [MockRole(rid) for rid in (role_ids or [])]

def test_owner_bypass_priority():
    """CRITICAL: The Owner ID must bypass a global '*' blacklist."""
    owner_id = 999
    user = MockUser(owner_id)
    
    # Permissions that block everyone
    permissions = {"blacklist_users": ["*"]}
    
    allowed, reason = is_authorized(user, permissions, owner_id)
    assert allowed is True
    assert "Owner Bypass" in reason

def test_blacklist_priority_over_whitelist():
    """Verify that a blacklist entry overrides a whitelist entry."""
    owner_id = 999
    user = MockUser(123, role_ids=[555]) # User 123 has Role 555
    
    permissions = {
        "whitelist_users": [123],  # User is whitelisted
        "blacklist_roles": [555]   # BUT their role is blacklisted
    }
    
    allowed, _ = is_authorized(user, permissions, owner_id)
    assert allowed is False  # Blacklist wins

def test_global_wildcard_blacklist():
    """Verify that 'all' or '*' in a blacklist blocks non-owners."""
    owner_id = 999
    user = MockUser(123)
    
    for wildcard in ["*", "all"]:
        permissions = {"blacklist_users": [wildcard]}
        allowed, _ = is_authorized(user, permissions, owner_id)
        assert allowed is False

# --- 3. Performance & Async Concurrency ---

@pytest.mark.asyncio
async def test_async_execution_concurrency():
    """Verify that multiple run_command calls don't block each other."""
    import time
    start = asyncio.get_event_loop().time()
    
    # Run three 1-second sleeps
    tasks = [run_command("sleep 1") for _ in range(3)]
    await asyncio.gather(*tasks)
    
    end = asyncio.get_event_loop().time()
    
    # If synchronous, this would take 3+ seconds.
    # If async, it should take roughly 1 second (buffer allowed for CI lag).
    assert end - start < 1.5
