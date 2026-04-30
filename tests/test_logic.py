import pytest
import asyncio
from lib.validation import validate_output
from lib.auth import is_authorized

@pytest.mark.asyncio
async def test_numeric_validation_pass():
    # Test that 10 >= 5 passes
    rules = {">=": "5"}
    context = {}
    assert await validate_output("10", rules, context) is True

@pytest.mark.asyncio
async def test_pig_game_logic():
    # Simulate Oink/Pig game: fail if die1 == die2
    context = {"die2": "6"}
    rules = {"!=": "{die2}"}

    # die1 is 6, die2 is 6 -> should fail
    assert await validate_output("6", rules, context) is False
    # die1 is 5, die2 is 6 -> should pass
    assert await validate_output("5", rules, context) is True

def test_auth_blacklist():
    # Mock user and roles
    class MockRole:
        def __init__(self, id): self.id = id
    class MockUser:
        def __init__(self, id, roles):
            self.id = id
            self.roles = roles

    permissions = {"blacklist_users": [123]}
    user = MockUser(123, [])

    allowed, reason = is_authorized(user, permissions, 999)
    assert allowed is False
    assert "Blacklisted" in reason
