import pytest
from lib.auth import is_authorized

class MockRole:
    def __init__(self, id): self.id = id

class MockUser:
    def __init__(self, id, role_ids):
        self.id = id
        self.roles = [MockRole(rid) for rid in role_ids]

def test_auth_empty_permissions():
    """Verify that empty permission blocks allow public access."""
    user = MockUser(123, [555])
    # No blacklist, no whitelist defined
    allowed, reason = is_authorized(user, {}, 999)
    assert allowed is True
    assert "Public Access" in reason

def test_auth_multiple_roles_blacklist():
    """Verify that if ONE of a user's many roles is blacklisted, they are denied."""
    user = MockUser(123, [101, 202, 303])
    permissions = {"blacklist_roles": [202]}
    allowed, reason = is_authorized(user, permissions, 999)
    assert allowed is False
    assert "Blacklisted" in reason

def test_auth_whitelist_with_wrong_user():
    """Verify that if a whitelist exists, users not on it are denied."""
    user = MockUser(123, [role_id for role_id in [111]])
    permissions = {"whitelist_users": [456]}
    allowed, reason = is_authorized(user, permissions, 999)
    assert allowed is False
    assert "Not on Whitelist" in reason
