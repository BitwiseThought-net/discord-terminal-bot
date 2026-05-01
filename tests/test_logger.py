import pytest
from lib.logger import log_action, log_text, log_warn, log_error

def test_logger_info_level(caplog):
    """Verify standard info logging for actions."""
    with caplog.at_level("INFO"):
        log_text("UserObj", "123", "Test Message")
    assert "Test Message" in caplog.text
    assert "INFO" in caplog.text

def test_logger_action_format(caplog):
    """Verify the structured action log format."""
    class MockUser:
        def __init__(self): self.id = 99; self.display_name = "Tester"
        def __str__(self): return "Tester"

    with caplog.at_level("INFO"):
        log_action(MockUser(), "666", "play", "Pig", "SUCCESS")
    assert "Tester (99)" in caplog.text
    assert "/play: Pig" in caplog.text
    assert "SUCCESS" in caplog.text

def test_logger_warning_error(caplog):
    """Verify warning and error levels."""
    with caplog.at_level("WARNING"):
        log_warn("Careful now")
    assert "WARNING" in caplog.text
    assert "Careful now" in caplog.text

    with caplog.at_level("ERROR"):
        log_error("Boom")
    assert "ERROR" in caplog.text
    assert "Boom" in caplog.text
