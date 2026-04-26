def is_authorized(user, permissions, owner_id):
    """Checks for wildcards (* or all) and IDs in blacklist/whitelist."""
    if user.id == owner_id:
        return True, "Owner Bypass"
        
    user_role_ids = [role.id for role in user.roles]
    wildcards = ["*", "all"]
    
    # 1. Blacklist Check (Priority)
    bl_users = permissions.get("blacklist_users", [])
    bl_roles = permissions.get("blacklist_roles", [])
    
    if any(w in bl_users for w in wildcards) or any(w in bl_roles for w in wildcards):
        return False, "Global Blacklist Imposed"
        
    if user.id in bl_users or any(r_id in bl_roles for r_id in user_role_ids):
        return False, "Access Blacklisted"
        
    # 2. Whitelist Check (Optional)
    white_u = permissions.get("whitelist_users", [])
    white_r = permissions.get("whitelist_roles", [])
    
    if not white_u and not white_r:
        return True, "Public Access"
        
    if any(w in white_u for w in wildcards) or any(w in white_r for w in wildcards):
        return True, "Global Whitelist Access"
        
    if user.id in white_u or any(r_id in white_r for r_id in user_role_ids):
        return True, "Authorized via Whitelist"
        
    return False, "Unauthorized (Not on Whitelist)"
