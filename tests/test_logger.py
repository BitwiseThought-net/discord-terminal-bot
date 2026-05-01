import pytest
from lib.logger import log_action, log_text, log_warn, log_error

class MockUser:
    def __init__(self, user_id, name):
        self.id = user_id
        self.name = name
    def __str__(self):
        return self.name

def test_logger_info_level(caplog):
    """Verify standard info logging for actions."""
    user = MockUser(123, "TestUser")
    with caplog.at_level("INFO"):
        log_text(user, "456", "Test Message")
    assert "TestUser (123)" in caplog.text
    assert "Test Message" in caplog.text
    assert "INFO" in caplog.text

def test_logger_action_format(caplog):
    """Verify the structured action log format."""
    user = MockUser(99, "Tester")
    with caplog.at_level("INFO"):
        log_action(user, "666", "play", "Pig", "SUCCESS")
    assert "Tester (99)" in caplog.text
    assert "/play: Pig" in caplog.text
    assert "SUCCESS" in caplog.text

def test_logger_system_fallback(caplog):
    """Verify that using a string instead of an object doesn't crash the logger."""
    with caplog.at_level("INFO"):
        log_text("System", "0", "System Start")
    assert "System (System)" in caplog.text

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
