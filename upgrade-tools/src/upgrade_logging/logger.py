"""Structured logging system for upgrade operations."""

import logging
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
import json


class LogLevel(Enum):
    """Log levels for upgrade operations."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ActionType(Enum):
    """Types of upgrade actions."""
    VERSION_UPDATE = "version_update"
    CONFIG_UPDATE = "config_update"
    SERVICE_UPGRADE = "service_upgrade"
    VALIDATION = "validation"
    HEALTH_CHECK = "health_check"
    ROLLBACK = "rollback"
    BACKUP = "backup"
    RESTORE = "restore"


class UpgradeLogger:
    """Structured logger for upgrade operations.
    
    Logs all upgrade actions with timestamps, action types, components,
    and details. Supports different log levels and writes to both file
    and console.
    """
    
    def __init__(
        self,
        log_file: Optional[Path] = None,
        console_level: LogLevel = LogLevel.INFO,
        file_level: LogLevel = LogLevel.DEBUG
    ):
        """Initialize the upgrade logger.
        
        Args:
            log_file: Path to log file. If None, uses default location.
            console_level: Minimum level for console output
            file_level: Minimum level for file output
        """
        self.log_file = log_file or Path("upgrade.log")
        self.console_level = console_level
        self.file_level = file_level
        
        # Create logger
        self.logger = logging.getLogger("openstack_upgrade")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(getattr(logging, file_level.value))
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level.value))
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Action log for structured tracking
        self.action_log: list[Dict[str, Any]] = []
    
    def log_action(
        self,
        action_type: ActionType,
        component: str,
        details: Dict[str, Any],
        level: LogLevel = LogLevel.INFO
    ) -> None:
        """Log an upgrade action with structured data.
        
        Args:
            action_type: Type of action being performed
            component: Component being acted upon
            details: Additional details about the action
            level: Log level for this action
        """
        timestamp = datetime.now()
        
        # Create structured log entry
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "action_type": action_type.value,
            "component": component,
            "details": details,
            "level": level.value
        }
        
        # Add to action log
        self.action_log.append(log_entry)
        
        # Format message for logging
        message = self._format_action_message(action_type, component, details)
        
        # Log to appropriate level
        log_method = getattr(self.logger, level.value.lower())
        log_method(message)
    
    def _format_action_message(
        self,
        action_type: ActionType,
        component: str,
        details: Dict[str, Any]
    ) -> str:
        """Format action message for human-readable logging.
        
        Args:
            action_type: Type of action
            component: Component name
            details: Action details
            
        Returns:
            Formatted message string
        """
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        return f"[{action_type.value}] {component}: {detail_str}"
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)
    
    def get_action_log(self) -> list[Dict[str, Any]]:
        """Get the structured action log.
        
        Returns:
            List of all logged actions
        """
        return self.action_log.copy()
    
    def save_action_log(self, output_file: Path) -> None:
        """Save action log to JSON file.
        
        Args:
            output_file: Path to output JSON file
        """
        with open(output_file, 'w') as f:
            json.dump(self.action_log, f, indent=2)
        
        self.info(f"Action log saved to {output_file}")
    
    def log_version_update(
        self,
        chart_name: str,
        old_version: str,
        new_version: str
    ) -> None:
        """Log a chart version update.
        
        Args:
            chart_name: Name of the chart
            old_version: Previous version
            new_version: New version
        """
        self.log_action(
            ActionType.VERSION_UPDATE,
            chart_name,
            {
                "old_version": old_version,
                "new_version": new_version
            },
            LogLevel.INFO
        )
    
    def log_config_update(
        self,
        file_path: str,
        changes: Dict[str, Any]
    ) -> None:
        """Log a configuration file update.
        
        Args:
            file_path: Path to configuration file
            changes: Dictionary of changes made
        """
        self.log_action(
            ActionType.CONFIG_UPDATE,
            file_path,
            changes,
            LogLevel.INFO
        )
    
    def log_service_upgrade(
        self,
        service_name: str,
        status: str,
        duration: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """Log a service upgrade operation.
        
        Args:
            service_name: Name of the service
            status: Status of the upgrade (success, failed, in_progress)
            duration: Duration in seconds (if completed)
            error: Error message (if failed)
        """
        details = {"status": status}
        if duration is not None:
            details["duration_seconds"] = duration
        if error:
            details["error"] = error
        
        level = LogLevel.ERROR if status == "failed" else LogLevel.INFO
        
        self.log_action(
            ActionType.SERVICE_UPGRADE,
            service_name,
            details,
            level
        )
    
    def log_validation(
        self,
        validation_type: str,
        result: str,
        issues: Optional[list] = None
    ) -> None:
        """Log a validation operation.
        
        Args:
            validation_type: Type of validation performed
            result: Result (passed, failed, warning)
            issues: List of issues found (if any)
        """
        details = {"result": result}
        if issues:
            details["issue_count"] = len(issues)
            details["issues"] = issues
        
        level = LogLevel.ERROR if result == "failed" else LogLevel.INFO
        
        self.log_action(
            ActionType.VALIDATION,
            validation_type,
            details,
            level
        )
    
    def log_health_check(
        self,
        component: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a health check operation.
        
        Args:
            component: Component being checked
            status: Health status (healthy, unhealthy, degraded)
            details: Additional health check details
        """
        check_details = {"status": status}
        if details:
            check_details.update(details)
        
        level = LogLevel.ERROR if status == "unhealthy" else LogLevel.INFO
        
        self.log_action(
            ActionType.HEALTH_CHECK,
            component,
            check_details,
            level
        )
    
    def log_rollback(
        self,
        component: str,
        status: str,
        error: Optional[str] = None
    ) -> None:
        """Log a rollback operation.
        
        Args:
            component: Component being rolled back
            status: Rollback status (success, failed, in_progress)
            error: Error message (if failed)
        """
        details = {"status": status}
        if error:
            details["error"] = error
        
        level = LogLevel.ERROR if status == "failed" else LogLevel.WARNING
        
        self.log_action(
            ActionType.ROLLBACK,
            component,
            details,
            level
        )


# Global logger instance
_global_logger: Optional[UpgradeLogger] = None


def get_logger() -> UpgradeLogger:
    """Get the global logger instance.
    
    Returns:
        Global UpgradeLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = UpgradeLogger()
    return _global_logger


def initialize_logger(
    log_file: Optional[Path] = None,
    console_level: LogLevel = LogLevel.INFO,
    file_level: LogLevel = LogLevel.DEBUG
) -> UpgradeLogger:
    """Initialize the global logger.
    
    Args:
        log_file: Path to log file
        console_level: Console log level
        file_level: File log level
        
    Returns:
        Initialized UpgradeLogger instance
    """
    global _global_logger
    _global_logger = UpgradeLogger(log_file, console_level, file_level)
    return _global_logger
