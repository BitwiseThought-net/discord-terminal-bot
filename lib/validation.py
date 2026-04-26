import asyncio

async def run_comparison_command(cmd):
    """Executes a sub-command to get a string for validation comparison."""
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return (stdout.decode() or stderr.decode()).strip()
    except:
        return ""

async def validate_output(output, rules):
    """Processes recursive validation rules, including dynamic command results and numerical comparisons."""
    if not rules:
        return True

    # Resolve "result" commands into strings before comparing
    async def resolve_val(v):
        if isinstance(v, dict) and "result" in v:
            return await run_comparison_command(v["result"].get("command", ""))
        return v

    def to_float(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    # 1. Direct equality
    if "==" in rules:
        target = await resolve_val(rules["=="])
        if output != target: return False

    # 2. Greater Than
    if ">" in rules:
        target = await resolve_val(rules[">"])
        f_out, f_target = to_float(output), to_float(target)
        if f_out is None or f_target is None or not (f_out > f_target): return False

    # 3. Less Than
    if "<" in rules:
        target = await resolve_val(rules["<"])
        f_out, f_target = to_float(output), to_float(target)
        if f_out is None or f_target is None or not (f_out < f_target): return False

    # 4. Within (Output is a substring of target string)
    if "within" in rules:
        target = await resolve_val(rules["within"])
        if output not in str(target): return False

    # 5. Contains (Target is a substring of output)
    if "contains" in rules:
        cond = rules["contains"]
        # Handle case where contains is a direct string or a result object
        if isinstance(cond, (str, dict)) and not any(k in cond for k in ["or", "and"]):
            target = await resolve_val(cond)
            if str(target) not in output: return False
        
        # Handle logical lists inside contains
        elif isinstance(cond, dict):
            if "or" in cond:
                resolved_list = [await resolve_val(i) for i in cond["or"]]
                if not any(str(item) in output for item in resolved_list): return False
            if "and" in cond:
                resolved_list = [await resolve_val(i) for i in cond["and"]]
                if not all(str(item) in output for item in resolved_list): return False

    # 6. Logic: NOT (Inverts inner rules)
    if "not" in rules:
        if await validate_output(output, rules["not"]): return False

    # 7. Logic: AND (All sub-rules must pass)
    if "and" in rules:
        for r in rules["and"]:
            if not await validate_output(output, r): return False

    # 8. Logic: OR (At least one sub-rule must pass)
    if "or" in rules:
        passed = False
        for r in rules["or"]:
            if await validate_output(output, r):
                passed = True
                break
        if not passed: return False

    return True
