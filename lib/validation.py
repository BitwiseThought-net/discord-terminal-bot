import asyncio

def damerau_levenshtein_distance(s1, s2):
    """Calculates the Damerau-Levenshtein distance between two strings."""
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in range(-1, lenstr1 + 1): d[(i, -1)] = i + 1
    for j in range(-1, lenstr2 + 1): d[(-1, j)] = j + 1
    for i in range(lenstr1):
        for j in range(lenstr2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(d[(i - 1, j)] + 1, d[(i, j - 1)] + 1, d[(i - 1, j - 1)] + cost)
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)
    return d[lenstr1 - 1, lenstr2 - 1]

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

async def validate_output(output, rules, context):
    """Processes recursive validation rules and updates context with nested results."""
    if not rules:
        return True

    async def resolve_val(v):
        if isinstance(v, dict) and "result" in v:
            res_config = v["result"]
            # Interpolate existing context into the nested command
            cmd = res_config.get("command", "").format(**context)
            res_output = await run_comparison_command(cmd)
            
            # If the nested result has a key, save it to the context
            if "key" in res_config:
                context[res_config["key"]] = res_output
                
            return res_output
        if isinstance(v, str):
            return v.format(**context)
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

    # 2. Fuzzy/Approximate equality (Distance <= 2)
    if "~=" in rules:
        target = await resolve_val(rules["~="])
        if damerau_levenshtein_distance(str(output), str(target)) > 2: return False

    # 3. Numerical Comparisons
    for op in [">", "<", ">=", "<="]:
        if op in rules:
            target = await resolve_val(rules[op])
            f_out, f_target = to_float(output), to_float(target)
            if f_out is None or f_target is None: return False
            if op == ">" and not (f_out > f_target): return False
            if op == "<" and not (f_out < f_target): return False
            if op == ">=" and not (f_out >= f_target): return False
            if op == "<=" and not (f_out <= f_target): return False

    # 4. Within (Output is a substring of target string)
    if "within" in rules:
        target = await resolve_val(rules["within"])
        if output not in str(target): return False

    # 5. Contains (Target is a substring of output)
    if "contains" in rules:
        cond = rules["contains"]
        if isinstance(cond, (str, dict)) and not any(k in cond for k in ["or", "and"]):
            target = await resolve_val(cond)
            if str(target) not in output: return False
        elif isinstance(cond, dict):
            if "or" in cond:
                resolved_list = [await resolve_val(i) for i in cond["or"]]
                if not any(str(item) in output for item in resolved_list): return False
            if "and" in cond:
                resolved_list = [await resolve_val(i) for i in cond["and"]]
                if not all(str(item) in output for item in resolved_list): return False

    # 6. Logic: NOT
    if "not" in rules:
        if await validate_output(output, rules["not"], context): return False

    # 7. Logic: AND
    if "and" in rules:
        for r in rules["and"]:
            if not await validate_output(output, r, context): return False

    # 8. Logic: OR
    if "or" in rules:
        passed = False
        for r in rules["or"]:
            if await validate_output(output, r, context):
                passed = True
                break
        if not passed: return False

    return True
