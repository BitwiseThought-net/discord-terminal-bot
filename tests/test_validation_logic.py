import pytest
from lib.validation import validate_output

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
async def test_validation_float_error_handling(caplog):
    """Ensure numerical operators don't crash on non-numeric strings."""
    context = {}
    rules = {">": "5"}
    # Comparing "abc" > 5 should return False gracefully, not crash
    assert await validate_output("abc", rules, context) is False
