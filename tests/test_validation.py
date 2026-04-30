import pytest
import asyncio
from lib.validation import validate_output

@pytest.mark.asyncio
async def test_numeric_comparisons():
    """Verify that >, <, >=, <= work with stringified numbers."""
    context = {}
    
    # Greater Than
    assert await validate_output("10", {">": "5"}, context) is True
    assert await validate_output("3", {">": "5"}, context) is False
    
    # Less Than or Equal
    assert await validate_output("5", {"<=": "5"}, context) is True
    assert await validate_output("6", {"<=": "5"}, context) is False

@pytest.mark.asyncio
async def test_fuzzy_matching():
    """Verify ~= approximate comparison (threshold <= 2)."""
    context = {}
    
    # Distance 1 (Substitution: o -> 0)
    assert await validate_output("Hell0", {"~=": "Hello"}, context) is True
    
    # Distance 2 (Transposition + Substitution)
    assert await validate_output("Hlelo!", {"~=": "Hello"}, context) is True
    
    # Distance 3+ (Should fail)
    assert await validate_output("Goodbye", {"~=": "Hello"}, context) is False

@pytest.mark.asyncio
async def test_pig_game_logic():
    """Verify 'Pig' logic: unequal dice pass, equal dice fail."""
    # Simulation: die1 is the command result, die2 is the validation result
    rules = {"!=": "{die2}"}
    
    # Scenario 1: Die 1 is 5, Die 2 is 3 -> PASS
    ctx_pass = {"die2": "3"}
    assert await validate_output("5", rules, ctx_pass) is True
    
    # Scenario 2: Die 1 is 4, Die 2 is 4 -> FAIL (Doubles!)
    ctx_fail = {"die2": "4"}
    assert await validate_output("4", rules, ctx_fail) is False

@pytest.mark.asyncio
async def test_interpolation_resolution():
    """Verify that validation rules correctly resolve {keys} from context."""
    context = {"expected": "root"}
    rules = {"==": "{expected}"}
    
    assert await validate_output("root", rules, context) is True
    assert await validate_output("admin", rules, context) is False

@pytest.mark.asyncio
async def test_contains_logic():
    """Verify 'contains' with strings and nested and/or logic."""
    context = {}
    
    # Single string
    assert await validate_output("System is online", {"contains": "online"}, context) is True
    
    # AND logic (All must exist)
    rules_and = {"contains": {"and": ["System", "online"]}}
    assert await validate_output("System is online", rules_and, context) is True
    assert await validate_output("System is offline", rules_and, context) is False
