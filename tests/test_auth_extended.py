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

def test_auth_global_wildcard_blacklist():
    """Target the global blacklist wildcard branch."""
    user = MockUser(123, [])
    # Case: '*' in blacklist
    permissions = {"blacklist_users": ["*"]}
    allowed, reason = is_authorized(user, permissions, 999)
    assert allowed is False
    assert "Global Blacklist" in reason

    # Case: 'all' in blacklist roles
    permissions_all = {"blacklist_roles": ["all"]}
    allowed_all, _ = is_authorized(user, permissions_all, 999)
    assert allowed_all is False

def test_auth_global_blacklists():
    """Trigger the global user and role wildcard blacklist branches."""
    user = MockUser(123, [456])
    
    # 1. Global User Blacklist
    assert is_authorized(user, {"blacklist_users": ["*"]}, 999)[0] is False
    
    # 2. Global Role Blacklist
    assert is_authorized(user, {"blacklist_roles": ["all"]}, 999)[0] is False

def test_auth_whitelist_denial_log(caplog):
    """Trigger the specific log_warn at the end of the whitelist check."""
    user = MockUser(123, [])
    permissions = {"whitelist_users": [999]} # Only user 999 allowed
    
    with caplog.at_level("WARNING"):
        allowed, reason = is_authorized(user, permissions, 888)
    
    assert allowed is False
    assert "denied access (Not on Whitelist)" in caplog.text

def test_auth_whitelist_success_branches():
    """Target the 'Authorized via Whitelist' success branches."""
    # 1. User is specifically on the whitelist
    user_u = MockUser(999, [])
    perm_u = {"whitelist_users": [999]}
    allowed_u, reason_u = is_authorized(user_u, perm_u, 111)
    assert allowed_u is True
    assert "Authorized via Whitelist" in reason_u

    # 2. User has a role that is on the whitelist
    user_r = MockUser(123, [555])
    perm_r = {"whitelist_roles": [555]}
    allowed_r, reason_r = is_authorized(user_r, perm_r, 111)
    assert allowed_r is True
    assert "Authorized via Whitelist" in reason_r

def test_auth_global_whitelist_wildcards():
    """Target the 'Global Whitelist Access' branch using wildcards."""
    user = MockUser(123, []) # Not specifically listed by ID
    
    # 1. User matches because whitelist has '*'
    perm_u = {"whitelist_users": ["*"]}
    allowed_u, reason_u = is_authorized(user, perm_u, 999)
    assert allowed_u is True
    assert "Global Whitelist Access" in reason_u

    # 2. User matches because role whitelist has 'all'
    perm_r = {"whitelist_roles": ["all"]}
    allowed_r, reason_r = is_authorized(user, perm_r, 999)
    assert allowed_r is True
    assert "Global Whitelist Access" in reason_r

