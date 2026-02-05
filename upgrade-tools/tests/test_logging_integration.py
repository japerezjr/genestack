"""Integration tests for logging, reporting, and documentation components."""

import pytest
from pathlib import Path
from datetime import datetime

from upgrade_logging import (
    UpgradeLogger,
    LogLevel,
    ActionType,
    SummaryReportGenerator,
    UpgradeDocGenerator
)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    return tmp_path


class TestLoggingIntegration:
    """Integration tests for the complete logging system."""
    
    def test_complete_upgrade_workflow(self, temp_dir):
        """Test complete workflow: logging -> reporting -> documentation."""
        # Initialize logger
        log_file = temp_dir / "upgrade.log"
        logger = UpgradeLogger(
            log_file=log_file,
            console_level=LogLevel.WARNING,
            file_level=LogLevel.DEBUG
        )
        
        # Initialize report generator
        report_gen = SummaryReportGenerator()
        report_gen.start_upgrade()
        
        # Initialize doc generator
        doc_gen = UpgradeDocGenerator()
        
        # Simulate upgrade actions
        # 1. Version updates
        version_updates = [
            ("keystone", "2024.1", "2025.1"),
            ("nova", "2024.2", "2025.1"),
            ("neutron", "2024.1", "2025.1")
        ]
        
        for chart, old_ver, new_ver in version_updates:
            logger.log_version_update(chart, old_ver, new_ver)
            report_gen.add_version_change(chart, old_ver, new_ver)
            doc_gen.add_version_change(chart, old_ver, new_ver)
        
        # 2. Configuration changes
        config_changes = [
            ("base-helm-configs/keystone/values.yaml", {"image_tag": "2025.1"}),
            ("base-helm-configs/nova/values.yaml", {"replicas": 3})
        ]
        
        for file_path, changes in config_changes:
            logger.log_config_update(file_path, changes)
            report_gen.add_config_change(file_path, changes)
            for key, value in changes.items():
                doc_gen.add_config_change(
                    file_path,
                    "modified",
                    f"Updated {key}",
                    new_value=str(value)
                )
        
        # 3. Service upgrades
        services = ["keystone", "nova", "neutron"]
        for service in services:
            logger.log_service_upgrade(service, "success", duration=45.5)
            report_gen.add_service_upgraded(service)
        
        # 4. Breaking changes
        breaking_change = {
            "component": "oslo.messaging",
            "description": "heartbeat_in_pthread deprecated",
            "mitigation": "Removed deprecated option from all configs"
        }
        doc_gen.add_breaking_change(
            breaking_change["component"],
            breaking_change["description"],
            breaking_change["mitigation"]
        )
        
        # 5. Manual steps
        doc_gen.add_manual_step(
            "Verify Nova compute agents are running",
            "nova",
            "Required after database migration",
            commands=["openstack compute service list"]
        )
        
        # End upgrade
        report_gen.end_upgrade()
        
        # Verify logger captured all actions
        action_log = logger.get_action_log()
        assert len(action_log) > 0
        
        # Count action types
        version_updates_logged = sum(
            1 for entry in action_log
            if entry["action_type"] == "version_update"
        )
        config_updates_logged = sum(
            1 for entry in action_log
            if entry["action_type"] == "config_update"
        )
        service_upgrades_logged = sum(
            1 for entry in action_log
            if entry["action_type"] == "service_upgrade"
        )
        
        assert version_updates_logged == 3
        assert config_updates_logged == 2
        assert service_upgrades_logged == 3
        
        # Verify report generator has correct data
        assert report_gen.summary.total_version_changes == 3
        assert report_gen.summary.total_config_changes == 2
        assert len(report_gen.summary.services_upgraded) == 3
        assert report_gen.summary.success is True
        
        # Generate reports
        text_report = report_gen.generate_text_report()
        json_report = report_gen.generate_json_report()
        
        assert "OpenStack Upgrade Summary Report" in text_report
        assert "keystone" in text_report
        assert "nova" in text_report
        assert "neutron" in text_report
        
        assert json_report["success"] is True
        assert json_report["statistics"]["total_version_changes"] == 3
        
        # Verify doc generator has correct data
        assert len(doc_gen.version_changes) == 3
        assert len(doc_gen.config_changes) == 2
        assert len(doc_gen.breaking_changes) == 1
        assert len(doc_gen.manual_steps) == 1
        
        # Generate documentation
        markdown = doc_gen.generate_markdown()
        
        assert "# OpenStack Caracal to Epoxy Upgrade Documentation" in markdown
        assert "## Version Changes" in markdown
        assert "## Configuration Changes" in markdown
        assert "## Breaking Changes" in markdown
        assert "## Manual Steps Required" in markdown
        assert "keystone" in markdown
        assert "oslo.messaging" in markdown
        
        # Save all outputs
        logger.save_action_log(temp_dir / "action_log.json")
        report_gen.save_report(temp_dir, format="both")
        doc_gen.save_documentation(temp_dir / "upgrade_doc.md", update_docs_dir=False)
        
        # Verify files were created
        assert (temp_dir / "action_log.json").exists()
        assert len(list(temp_dir.glob("upgrade_summary_*.txt"))) == 1
        assert len(list(temp_dir.glob("upgrade_summary_*.json"))) == 1
        assert (temp_dir / "upgrade_doc.md").exists()
    
    def test_report_from_action_log(self, temp_dir):
        """Test generating report from action log."""
        # Create logger and log some actions
        log_file = temp_dir / "upgrade.log"
        logger = UpgradeLogger(log_file=log_file)
        
        logger.log_version_update("keystone", "2024.1", "2025.1")
        logger.log_config_update("test.yaml", {"key": "value"})
        logger.log_service_upgrade("keystone", "success", duration=30.0)
        logger.log_service_upgrade("nova", "failed", error="Timeout")
        
        # Get action log
        action_log = logger.get_action_log()
        
        # Create report from action log
        report_gen = SummaryReportGenerator()
        report_gen.from_action_log(action_log)
        
        # Verify report was populated correctly
        assert report_gen.summary.total_version_changes == 1
        assert report_gen.summary.total_config_changes == 1
        assert "keystone" in report_gen.summary.services_upgraded
        assert "nova" in report_gen.summary.services_failed
        assert report_gen.summary.success is False  # Because nova failed
    
    def test_upgrade_with_issues(self, temp_dir):
        """Test upgrade workflow with issues and rollback."""
        logger = UpgradeLogger(log_file=temp_dir / "upgrade.log")
        report_gen = SummaryReportGenerator()
        doc_gen = UpgradeDocGenerator()
        
        report_gen.start_upgrade()
        
        # Start upgrade
        logger.log_version_update("keystone", "2024.1", "2025.1")
        report_gen.add_version_change("keystone", "2024.1", "2025.1")
        
        # Service upgrade fails
        logger.log_service_upgrade("keystone", "failed", error="Pod startup timeout")
        report_gen.add_service_failed("keystone")
        report_gen.add_issue(
            "critical",
            "keystone",
            "Service upgrade failed: Pod startup timeout"
        )
        
        # Rollback initiated
        logger.log_rollback("keystone", "success")
        report_gen.mark_rollback()
        
        doc_gen.add_warning("Upgrade failed and was rolled back")
        doc_gen.add_note("Investigate pod startup timeout before retrying")
        
        report_gen.end_upgrade()
        
        # Verify failure is captured
        assert report_gen.summary.success is False
        assert report_gen.summary.rollback_performed is True
        assert len(report_gen.summary.services_failed) == 1
        assert len(report_gen.summary.critical_issues) == 1
        
        # Generate report
        text_report = report_gen.generate_text_report()
        assert "FAILED" in text_report
        assert "Rollback: PERFORMED" in text_report
        
        # Generate documentation
        markdown = doc_gen.generate_markdown()
        assert "⚠️ Upgrade failed and was rolled back" in markdown
        assert "ℹ️ Investigate pod startup timeout before retrying" in markdown
    
    def test_changelog_generation(self, temp_dir):
        """Test changelog entry generation."""
        doc_gen = UpgradeDocGenerator()
        
        doc_gen.add_version_change("keystone", "2024.1", "2025.1")
        doc_gen.add_version_change("nova", "2024.2", "2025.1")
        doc_gen.add_breaking_change(
            "oslo.messaging",
            "heartbeat_in_pthread deprecated",
            "Removed from configs"
        )
        doc_gen.add_manual_step(
            "Restart compute agents",
            "nova",
            "Required after upgrade"
        )
        
        # Generate changelog entry
        changelog_entry = doc_gen.generate_changelog_entry()
        
        assert "Epoxy Upgrade" in changelog_entry
        assert "### Changed" in changelog_entry
        assert "keystone" in changelog_entry
        assert "nova" in changelog_entry
        assert "### Breaking Changes" in changelog_entry
        assert "oslo.messaging" in changelog_entry
        assert "### Manual Steps Required" in changelog_entry
        
        # Append to changelog file
        changelog_path = temp_dir / "CHANGELOG.md"
        doc_gen.append_to_changelog(changelog_path)
        
        assert changelog_path.exists()
        content = changelog_path.read_text()
        assert "# Changelog" in content
        assert "Epoxy Upgrade" in content
