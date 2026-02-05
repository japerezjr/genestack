"""Tests for SummaryReportGenerator."""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta

from upgrade_logging import (
    SummaryReportGenerator,
    UpgradeSummary,
    VersionChange,
    ConfigChange,
    Issue
)


@pytest.fixture
def generator():
    """Create a test report generator."""
    return SummaryReportGenerator()


class TestUpgradeSummary:
    """Tests for UpgradeSummary dataclass."""
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        start = datetime(2025, 1, 1, 10, 0, 0)
        end = datetime(2025, 1, 1, 11, 30, 0)
        
        summary = UpgradeSummary(start_time=start, end_time=end)
        assert summary.duration == timedelta(hours=1, minutes=30)
    
    def test_duration_none_when_not_ended(self):
        """Test duration is None when upgrade hasn't ended."""
        summary = UpgradeSummary(start_time=datetime.now())
        assert summary.duration is None
    
    def test_total_counts(self):
        """Test count properties."""
        summary = UpgradeSummary(start_time=datetime.now())
        
        summary.version_changes.append(
            VersionChange("keystone", "2024.1", "2025.1", datetime.now().isoformat())
        )
        summary.config_changes.append(
            ConfigChange("test.yaml", {"key": "value"}, datetime.now().isoformat())
        )
        summary.issues.append(
            Issue("high", "nova", "Test issue", datetime.now().isoformat())
        )
        
        assert summary.total_version_changes == 1
        assert summary.total_config_changes == 1
        assert summary.total_issues == 1
    
    def test_critical_issues_filter(self):
        """Test filtering critical issues."""
        summary = UpgradeSummary(start_time=datetime.now())
        
        summary.issues.append(
            Issue("critical", "nova", "Critical issue", datetime.now().isoformat())
        )
        summary.issues.append(
            Issue("high", "keystone", "High issue", datetime.now().isoformat())
        )
        summary.issues.append(
            Issue("critical", "neutron", "Another critical", datetime.now().isoformat())
        )
        
        critical = summary.critical_issues
        assert len(critical) == 2
        assert all(i.severity == "critical" for i in critical)
    
    def test_success_determination(self):
        """Test success property."""
        summary = UpgradeSummary(start_time=datetime.now())
        
        # Initially successful
        assert summary.success is True
        
        # Failed service makes it unsuccessful
        summary.services_failed.append("nova")
        assert summary.success is False
        
        # Reset
        summary = UpgradeSummary(start_time=datetime.now())
        
        # Critical issue makes it unsuccessful
        summary.issues.append(
            Issue("critical", "test", "Critical", datetime.now().isoformat())
        )
        assert summary.success is False
        
        # Reset
        summary = UpgradeSummary(start_time=datetime.now())
        
        # Rollback makes it unsuccessful
        summary.rollback_performed = True
        assert summary.success is False


class TestSummaryReportGenerator:
    """Tests for SummaryReportGenerator class."""
    
    def test_initialization(self, generator):
        """Test generator initialization."""
        assert generator.summary is not None
        assert generator.summary.start_time is not None
        assert generator.summary.end_time is None
    
    def test_start_upgrade(self, generator):
        """Test marking upgrade start."""
        old_start = generator.summary.start_time
        generator.start_upgrade()
        assert generator.summary.start_time != old_start
    
    def test_end_upgrade(self, generator):
        """Test marking upgrade end."""
        assert generator.summary.end_time is None
        generator.end_upgrade()
        assert generator.summary.end_time is not None
    
    def test_add_version_change(self, generator):
        """Test adding version changes."""
        generator.add_version_change("keystone", "2024.1", "2025.1")
        generator.add_version_change("nova", "2024.2", "2025.1")
        
        assert len(generator.summary.version_changes) == 2
        assert generator.summary.version_changes[0].chart_name == "keystone"
        assert generator.summary.version_changes[1].chart_name == "nova"
    
    def test_add_config_change(self, generator):
        """Test adding configuration changes."""
        changes = {"image_tag": "2025.1", "replicas": 3}
        generator.add_config_change("test.yaml", changes)
        
        assert len(generator.summary.config_changes) == 1
        change = generator.summary.config_changes[0]
        assert change.file_path == "test.yaml"
        assert change.changes == changes
    
    def test_add_issue(self, generator):
        """Test adding issues."""
        generator.add_issue("high", "nova", "Test issue", resolved=False)
        generator.add_issue("critical", "keystone", "Critical issue", resolved=True)
        
        assert len(generator.summary.issues) == 2
        assert generator.summary.issues[0].severity == "high"
        assert generator.summary.issues[0].resolved is False
        assert generator.summary.issues[1].severity == "critical"
        assert generator.summary.issues[1].resolved is True
    
    def test_add_service_upgraded(self, generator):
        """Test marking services as upgraded."""
        generator.add_service_upgraded("keystone")
        generator.add_service_upgraded("nova")
        generator.add_service_upgraded("keystone")  # Duplicate
        
        assert len(generator.summary.services_upgraded) == 2
        assert "keystone" in generator.summary.services_upgraded
        assert "nova" in generator.summary.services_upgraded
    
    def test_add_service_failed(self, generator):
        """Test marking services as failed."""
        generator.add_service_failed("nova")
        generator.add_service_failed("neutron")
        generator.add_service_failed("nova")  # Duplicate
        
        assert len(generator.summary.services_failed) == 2
        assert "nova" in generator.summary.services_failed
        assert "neutron" in generator.summary.services_failed
    
    def test_mark_rollback(self, generator):
        """Test marking rollback."""
        assert generator.summary.rollback_performed is False
        generator.mark_rollback()
        assert generator.summary.rollback_performed is True
    
    def test_generate_text_report(self, generator):
        """Test generating text report."""
        generator.add_version_change("keystone", "2024.1", "2025.1")
        generator.add_config_change("test.yaml", {"key": "value"})
        generator.add_service_upgraded("keystone")
        generator.add_issue("high", "nova", "Test issue")
        generator.end_upgrade()
        
        report = generator.generate_text_report()
        
        assert "OpenStack Upgrade Summary Report" in report
        assert "VERSION CHANGES" in report
        assert "keystone" in report
        assert "2024.1" in report
        assert "2025.1" in report
        assert "CONFIGURATION CHANGES" in report
        assert "test.yaml" in report
        assert "SERVICES" in report
        assert "ISSUES ENCOUNTERED" in report
    
    def test_generate_json_report(self, generator):
        """Test generating JSON report."""
        generator.add_version_change("keystone", "2024.1", "2025.1")
        generator.add_config_change("test.yaml", {"key": "value"})
        generator.add_service_upgraded("keystone")
        generator.add_issue("high", "nova", "Test issue")
        generator.end_upgrade()
        
        report = generator.generate_json_report()
        
        assert "start_time" in report
        assert "end_time" in report
        assert "duration_seconds" in report
        assert "success" in report
        assert len(report["version_changes"]) == 1
        assert len(report["config_changes"]) == 1
        assert len(report["services"]["upgraded"]) == 1
        assert len(report["issues"]) == 1
        assert report["statistics"]["total_version_changes"] == 1
    
    def test_save_report_text(self, generator, tmp_path):
        """Test saving text report."""
        generator.add_version_change("keystone", "2024.1", "2025.1")
        generator.end_upgrade()
        
        generator.save_report(tmp_path, format="text")
        
        # Check that a file was created
        files = list(tmp_path.glob("upgrade_summary_*.txt"))
        assert len(files) == 1
        
        content = files[0].read_text()
        assert "OpenStack Upgrade Summary Report" in content
    
    def test_save_report_json(self, generator, tmp_path):
        """Test saving JSON report."""
        generator.add_version_change("keystone", "2024.1", "2025.1")
        generator.end_upgrade()
        
        generator.save_report(tmp_path, format="json")
        
        # Check that a file was created
        files = list(tmp_path.glob("upgrade_summary_*.json"))
        assert len(files) == 1
        
        with open(files[0]) as f:
            data = json.load(f)
        
        assert "start_time" in data
        assert len(data["version_changes"]) == 1
    
    def test_save_report_both(self, generator, tmp_path):
        """Test saving both text and JSON reports."""
        generator.add_version_change("keystone", "2024.1", "2025.1")
        generator.end_upgrade()
        
        generator.save_report(tmp_path, format="both")
        
        # Check that both files were created
        txt_files = list(tmp_path.glob("upgrade_summary_*.txt"))
        json_files = list(tmp_path.glob("upgrade_summary_*.json"))
        
        assert len(txt_files) == 1
        assert len(json_files) == 1
    
    def test_from_action_log(self, generator):
        """Test populating summary from action log."""
        action_log = [
            {
                "action_type": "version_update",
                "component": "keystone",
                "details": {"old_version": "2024.1", "new_version": "2025.1"}
            },
            {
                "action_type": "config_update",
                "component": "test.yaml",
                "details": {"key": "value"}
            },
            {
                "action_type": "service_upgrade",
                "component": "keystone",
                "details": {"status": "success"}
            },
            {
                "action_type": "service_upgrade",
                "component": "nova",
                "details": {"status": "failed", "error": "Timeout"}
            },
            {
                "action_type": "validation",
                "component": "config",
                "details": {"result": "failed", "issues": ["Issue 1", "Issue 2"]}
            },
            {
                "action_type": "rollback",
                "component": "nova",
                "details": {"status": "success"}
            }
        ]
        
        generator.from_action_log(action_log)
        
        assert len(generator.summary.version_changes) == 1
        assert len(generator.summary.config_changes) == 1
        assert "keystone" in generator.summary.services_upgraded
        assert "nova" in generator.summary.services_failed
        assert len(generator.summary.issues) == 3  # 1 from failed service + 2 from validation
        assert generator.summary.rollback_performed is True
