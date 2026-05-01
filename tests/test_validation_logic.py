import pytest
import asyncio
# ADDED: run_command to the imports
from lib.validation import validate_output, run_command

@pytest.mark.asyncio
async def test_complex_logic_nesting():
    """Test (A OR B) AND (NOT C) logic."""
    context = {"val": "10"}
    rules = {
        "and": [
            {"or": [{"==": "10"}, {"==": "20"}]},
            {"not": {"==": "5"}}
        ]
    }
    
    # "10" is (10 or 20) AND is not 5 -> True
    assert await validate_output("10", rules, context) is True
    # "5" fails the second part -> False
    assert await validate_output("5", rules, context) is False
    # "30" fails the first part -> False
    assert await validate_output("30", rules, context) is False

@pytest.mark.asyncio
async def test_validation_float_error_handling():
    """Ensure numerical operators don't crash on non-numeric strings."""
    context = {}
    rules = {">": "5"}
    # Comparing "abc" > 5 should return False gracefully via the try/except block
    assert await validate_output("abc", rules, context) is False

@pytest.mark.asyncio
async def test_run_command_exception(caplog):
    """Target the try/except block in run_command to hit 100% coverage."""
    # Passing None forces an internal exception in the subprocess logic
    with caplog.at_level("ERROR"):
        result = await run_command(None)
    
    assert result == ""
    assert "Validation Subprocess Error" in caplog.text

@pytest.mark.asyncio
async def test_within_operator():
    """Verify 'within' operator (substring of target)."""
    assert await validate_output("apple", {"within": "apple pie"}, {}) is True
    assert await validate_output("orange", {"within": "apple pie"}, {}) is False

@pytest.mark.asyncio
async def test_logical_or_pass():
    """Verify 'or' logic short-circuiting."""
    rules = {"or": [{"==": "a"}, {"==": "b"}]}
    # Matches 'a', so it should return True immediately
    assert await validate_output("a", rules, {}) is True

@pytest.mark.asyncio
async def test_contains_logic_extended():
    """Verify 'contains' with simple string and complex list objects."""
    # Simple match
    assert await validate_output("hello world", {"contains": "hello"}, {}) is True
    
    # List match (OR logic inside contains)
    rules_or = {"contains": {"or": ["apple", "banana"]}}
    assert await validate_output("I like bananas", rules_or, {}) is True
    assert await validate_output("I like cherries", rules_or, {}) is False

@pytest.mark.asyncio
async def test_validation_missing_branches():
    """Target the remaining logic branches in validation.py."""
    ctx = {"target": "root"}

    # 1. Fuzzy Matching Branch (~=)
    assert await validate_output("helo", {"~=": "hello"}, {}) is True
    assert await validate_output("abcdef", {"~=": "hello"}, {}) is False

    # 2. Contains 'AND' logic failure branch
    rules_and = {"contains": {"and": ["apple", "banana"]}}
    assert await validate_output("I have an apple", rules_and, {}) is False

    # 3. Logical 'OR' failure branch (All sub-rules fail)
    rules_or = {"or": [{"==": "x"}, {"==": "y"}]}
    assert await validate_output("z", rules_or, {}) is False

    # 4. Logical 'AND' failure branch
    rules_and_fail = {"and": [{"==": "a"}, {"==": "b"}]}
    assert await validate_output("a", rules_and_fail, {}) is False

    # 5. Result with interpolation branch
    # This tests the resolve_val branch where command uses {key}
    # Mocking run_command isn't needed if we use a simple echo
    rules_res = {"==": {"result": {"command": "echo {target}", "key": "found"}}}
    assert await validate_output("root", rules_res, ctx) is True
    assert ctx["found"] == "root"

@pytest.mark.asyncio
async def test_fuzzy_transposition_branch():
    """Target the transposition (swap) logic branch in Damerau-Levenshtein."""
    # 'ca' -> 'ac' is a transposition (distance 1)
    # This specifically triggers the 'if i > 0 and j > 0' logic path
    assert await validate_output("ac", {"~=": "ca"}, {}) is True
    
    # 'tset' -> 'test' is another transposition
    assert await validate_output("tset", {"~=": "test"}, {}) is True

@pytest.mark.asyncio
async def test_not_logic_failure():
    """Ensure we hit the 'False' branch of the NOT operator."""
    # Target the line: if await validate_output(...): return False
    rules = {"not": {"==": "fail"}}
    assert await validate_output("fail", rules, {}) is False

@pytest.mark.asyncio
async def test_fuzzy_matching_transposition_and_substitution():
    """
    Force the Damerau-Levenshtein transposition branch.
    Strings need length > 2 to hit the 'i > 0 and j > 0' condition.
    """
    # 'bac' vs 'abc' is a transposition (distance 1)
    assert await validate_output("bac", {"~=": "abc"}, {}) is True
    
    # 'aXbc' vs 'abXc' (transposition of internal characters)
    assert await validate_output("abXc", {"~=": "aXbc"}, {}) is True

@pytest.mark.asyncio
async def test_validation_empty_rules():
    """Hit the 'if not rules: return True' branch."""
    assert await validate_output("anything", None, {}) is True

@pytest.mark.asyncio
async def test_fuzzy_substitution_cost_branch():
    """
    Specifically targets the substitution cost logic in Damerau-Levenshtein.
    'ABC' -> 'AXC' is a pure substitution at index 1.
    """
    # 1. Direct substitution (Distance 1)
    assert await validate_output("AXC", {"~=": "ABC"}, {}) is True
    
    # 2. Maximum allowed substitution (Distance 2)
    # 'ABC' -> 'AXY' (B substituted for X, C substituted for Y)
    assert await validate_output("AXY", {"~=": "ABC"}, {}) is True
    
    # 3. Beyond allowed substitution (Distance 3)
    # 'ABC' -> 'XYZ'
    assert await validate_output("XYZ", {"~=": "ABC"}, {}) is False

@pytest.mark.asyncio
async def test_force_transposition_assignment():
    """
    Forces the final unvisited statement in Damerau-Levenshtein.
    Requires a swap ('ba' vs 'ab') where the transposition cost 
    becomes the winning minimum value.
    """
    # Comparing 'abc' to 'bac'
    # The transposition of 'a' and 'b' must be the winning path for the d[i,j] assignment.
    assert await validate_output("bac", {"~=": "abc"}, {}) is True

@pytest.mark.asyncio
async def test_numeric_float_conversion_failure():
    """
    Ensures we hit the 'except: return False' in the numerical ops loop.
    This happens if resolve_val returns something that float() hates.
    """
    # Rules expects a number, but we provide a string that can't be a float
    assert await validate_output("10", {">": "not_a_number"}, {}) is False

@pytest.mark.asyncio
async def test_contains_result_object():
    """
    Target the branch: 
    elif isinstance(cond, (str, dict)) and not any(k in cond for k in ["or", "and"]):
    specifically for the 'dict' (result) case.
    """
    # 'contains' is a dict (result object), but NOT a logic dict (no and/or)
    rules = {
        "contains": {
            "result": {"command": "echo 'target'"}
        }
    }
    assert await validate_output("The target is here", rules, {}) is True

@pytest.mark.asyncio
async def test_damerau_levenshtein_full_matrix():
    """
    Force a complex Damerau-Levenshtein calculation to ensure every 
    assignment and comparison in the matrix loop is hit.
    """
    # Swapping 'ba' to 'ab' in the middle of a string while having 
    # other differences to ensure transposition is the chosen path in min().
    assert await validate_output("ab de", {"~=": "ba de"}, {}) is True
    assert await validate_output("abcde", {"~=": "axcde"}, {}) is True # Substitution winner

@pytest.mark.asyncio
async def test_contains_dict_result_failure():
    """
    Surgical strike on the final missing statement.
    Triggers 'return False' when 'contains' is a dict (result) 
    but the result is NOT in the output.
    """
    rules = {
        "contains": {
            "result": {"command": "echo 'SECRET_KEY'"}
        }
    }
    # The output "public_data" does NOT contain "SECRET_KEY"
    # This hits the 'if str(target) not in output: return False' line
    assert await validate_output("public_data", rules, {}) is False

@pytest.mark.asyncio
async def test_numerical_operators_all_branches():
    """Ensure every single numerical operator branch (>, <, >=, <=) is hit."""
    # Hit >= fail
    assert await validate_output("5", {">=": "10"}, {}) is False
    # Hit <= fail
    assert await validate_output("10", {"<=": "5"}, {}) is False
    # Hit < fail
    assert await validate_output("10", {"<": "5"}, {}) is False


@pytest.mark.asyncio
async def test_final_transposition_coverage():
    """
    Forces the final unvisited statement in Damerau-Levenshtein.
    A 2-character swap ('ba' vs 'ab') ensures transposition is the 
    winning calculation path for the matrix assignment.
    """
    # Distance is 1 via transposition. 
    # Substitution would be 2. Deletion/Insertion would be 2.
    # This forces the assignment: d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)
    assert await validate_output("ba", {"~=": "ab"}, {}) is True

@pytest.mark.asyncio
async def test_numerical_bad_comparison_data():
    """
    Target the 'except: return False' in numerical ops.
    Forces an error by comparing a number to a string that can't be resolved.
    """
    # This triggers the 'except' block because float() will fail inside the loop.
    assert await validate_output("10", {">": "not-a-number"}, {}) is False

@pytest.mark.asyncio
async def test_contains_logic_and_failure_path():
    """
    Target the specific 'return False' for the 'and' branch in contains.
    Requires hitting the list comprehension and the 'all()' check.
    """
    rules = {
        "contains": {
            "and": ["apple", "missing_fruit"]
        }
    }
    # "apple" is there, but "missing_fruit" is not. 
    # Hits: if not all(...): return False
    assert await validate_output("I have an apple", rules, {}) is False

@pytest.mark.asyncio
async def test_resolve_val_string_interpolation_only():
    """
    Target the branch in resolve_val that handles a plain string 
    with interpolation but NOT a result dictionary.
    """
    context = {"name": "world"}
    # This forces resolve_val(v) to enter the 'if isinstance(v, str)' branch
    # and execute 'v.format(**context)' directly.
    rules = {"==": "hello {name}"}
    assert await validate_output("hello world", rules, context) is True

@pytest.mark.asyncio
async def test_resolve_val_raw_types():
    """
    Targets the final 'return v' in resolve_val.
    By passing an integer (not a str or dict), we force the fallback return.
    """
    # Passing 10 as a raw integer. resolve_val(10) hits 'return v'
    # Then 'to_float' handles it, and the comparison (10 > 5) passes.
    assert await validate_output("10", {">": 5}, {}) is True

@pytest.mark.asyncio
async def test_contains_logic_or_failure():
    """Ensure we hit the 'False' branch of the 'or' logic inside contains."""
    rules = {
        "contains": {
            "or": ["missing1", "missing2"]
        }
    }
    # Hits: if not any(...): return False
    assert await validate_output("fixed_string", rules, {}) is False
