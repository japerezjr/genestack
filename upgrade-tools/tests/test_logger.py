"""Tests for UpgradeLogger."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from upgrade_logging import (
    UpgradeLogger,
    LogLevel,
    ActionType,
    initialize_logger,
    get_logger
)


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file."""
    return tmp_path / "test_upgrade.log"


@pytest.fixture
def logger(temp_log_file):
    """Create a test logger instance."""
    return UpgradeLogger(
        log_file=temp_log_file,
        console_level=LogLevel.WARNING,
        file_level=LogLevel.DEBUG
    )


class TestUpgradeLogger:
    """Tests for UpgradeLogger class."""
    
    def test_logger_initialization(self, logger, temp_log_file):
        """Test logger is properly initialized."""
        assert logger.log_file == temp_log_file
        assert logger.console_level == LogLevel.WARNING
        assert logger.file_level == LogLevel.DEBUG
        assert len(logger.action_log) == 0
    
    def test_log_action(self, logger):
        """Test logging an action."""
        logger.log_action(
            ActionType.VERSION_UPDATE,
            "keystone",
            {"old_version": "2024.1", "new_version": "2025.1"},
            LogLevel.INFO
        )
        
        assert len(logger.action_log) == 1
        entry = logger.action_log[0]
        assert entry["action_type"] == "version_update"
        assert entry["component"] == "keystone"
        assert entry["details"]["old_version"] == "2024.1"
        assert entry["details"]["new_version"] == "2025.1"
        assert "timestamp" in entry
    
    def test_log_version_update(self, logger):
        """Test logging a version update."""
        logger.log_version_update("nova", "2024.2", "2025.1")
        
        assert len(logger.action_log) == 1
        entry = logger.action_log[0]
        assert entry["action_type"] == "version_update"
        assert entry["component"] == "nova"
        assert entry["details"]["old_version"] == "2024.2"
        assert entry["details"]["new_version"] == "2025.1"
    
    def test_log_config_update(self, logger):
        """Test logging a configuration update."""
        changes = {
            "image_tag": "2025.1",
            "replicas": 3
        }
        logger.log_config_update("base-helm-configs/keystone/values.yaml", changes)
        
        assert len(logger.action_log) == 1
        entry = logger.action_log[0]
        assert entry["action_type"] == "config_update"
        assert entry["details"]["image_tag"] == "2025.1"
    
    def test_log_service_upgrade_success(self, logger):
        """Test logging a successful service upgrade."""
        logger.log_service_upgrade("keystone", "success", duration=45.5)
        
        assert len(logger.action_log) == 1
        entry = logger.action_log[0]
        assert entry["action_type"] == "service_upgrade"
        assert entry["component"] == "keystone"
        assert entry["details"]["status"] == "success"
        assert entry["details"]["duration_seconds"] == 45.5
        assert entry["level"] == "INFO"
    
    def test_log_service_upgrade_failure(self, logger):
        """Test logging a failed service upgrade."""
        logger.log_service_upgrade(
            "nova",
            "failed",
            error="Timeout waiting for pods"
        )
        
        assert len(logger.action_log) == 1
        entry = logger.action_log[0]
        assert entry["action_type"] == "service_upgrade"
        assert entry["details"]["status"] == "failed"
        assert entry["details"]["error"] == "Timeout waiting for pods"
        assert entry["level"] == "ERROR"
    
    def test_log_validation(self, logger):
        """Test logging a validation operation."""
        issues = ["Deprecated option found", "Invalid image tag"]
        logger.log_validation("config_validation", "failed", issues)
        
        assert len(logger.action_log) == 1
        entry = logger.action_log[0]
        assert entry["action_type"] == "validation"
        assert entry["details"]["result"] == "failed"
        assert entry["details"]["issue_count"] == 2
        assert entry["level"] == "ERROR"
    
    def test_log_health_check(self, logger):
        """Test logging a health check."""
        details = {"pod_count": 3, "ready_count": 3}
        logger.log_health_check("keystone", "healthy", details)
        
        assert len(logger.action_log) == 1
        entry = logger.action_log[0]
        assert entry["action_type"] == "health_check"
        assert entry["details"]["status"] == "healthy"
        assert entry["details"]["pod_count"] == 3
        assert entry["level"] == "INFO"
    
    def test_log_rollback(self, logger):
        """Test logging a rollback operation."""
        logger.log_rollback("nova", "success")
        
        assert len(logger.action_log) == 1
        entry = logger.action_log[0]
        assert entry["action_type"] == "rollback"
        assert entry["details"]["status"] == "success"
        assert entry["level"] == "WARNING"
    
    def test_get_action_log(self, logger):
        """Test getting the action log."""
        logger.log_version_update("keystone", "2024.1", "2025.1")
        logger.log_version_update("nova", "2024.2", "2025.1")
        
        log = logger.get_action_log()
        assert len(log) == 2
        assert isinstance(log, list)
        # Verify it's a copy
        log.append({"test": "data"})
        assert len(logger.action_log) == 2
    
    def test_save_action_log(self, logger, tmp_path):
        """Test saving action log to JSON file."""
        logger.log_version_update("keystone", "2024.1", "2025.1")
        logger.log_config_update("test.yaml", {"key": "value"})
        
        output_file = tmp_path / "action_log.json"
        logger.save_action_log(output_file)
        
        assert output_file.exists()
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert data[0]["action_type"] == "version_update"
        assert data[1]["action_type"] == "config_update"
    
    def test_log_file_created(self, logger, temp_log_file):
        """Test that log file is created."""
        logger.info("Test message")
        assert temp_log_file.exists()
    
    def test_multiple_log_levels(self, logger):
        """Test logging at different levels."""
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # All should be written to file
        assert logger.log_file.exists()
        content = logger.log_file.read_text()
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content
        assert "Critical message" in content


class TestGlobalLogger:
    """Tests for global logger functions."""
    
    def test_get_logger_creates_instance(self):
        """Test that get_logger creates a global instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2
    
    def test_initialize_logger(self, tmp_path):
        """Test initializing the global logger."""
        log_file = tmp_path / "global.log"
        logger = initialize_logger(
            log_file=log_file,
            console_level=LogLevel.ERROR,
            file_level=LogLevel.INFO
        )
        
        assert logger.log_file == log_file
        assert logger.console_level == LogLevel.ERROR
        assert logger.file_level == LogLevel.INFO
        
        # Verify it's the global instance
        assert get_logger() is logger
