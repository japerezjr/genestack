"""Tests for pre-upgrade validator."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from health.validator import (
    PreUpgradeValidator,
    PreUpgradeValidationReport,
    ValidationFailure,
    ValidationError
)
from health.aggregator import HealthReport, ServiceHealth
from health.resource_validator import (
    ValidationReport,
    ResourceStatus,
    BackupStatus,
    JobStatus
)


@pytest.fixture
def healthy_health_report():
    """Create a healthy health report."""
    services = {
        "openstack": ServiceHealth("openstack", healthy=True)
    }
    return HealthReport(
        timestamp=datetime.now(),
        overall_healthy=True,
        services=services
    )


@pytest.fixture
def unhealthy_health_report():
    """Create an unhealthy health report."""
    from health.pod_checker import PodStatusReport, PodStatus
    
    # Create an unhealthy pod report
    unhealthy_pods = PodStatusReport(
        total_pods=2,
        running=1,
        pending=0,
        failed=1,
        succeeded=0,
        unknown=0,
        pods=[
            PodStatus("pod1", "openstack", "Running", True, 0),
            PodStatus("pod2", "openstack", "Failed", False, 0),
        ],
        healthy=False
    )
    
    service = ServiceHealth("openstack", pod_status=unhealthy_pods)
    services = {"openstack": service}
    return HealthReport(
        timestamp=datetime.now(),
        overall_healthy=False,
        services=services
    )


@pytest.fixture
def passed_resource_report():
    """Create a passed resource validation report."""
    return ValidationReport(
        timestamp=datetime.now(),
        resource_status=ResourceStatus(
            total_cpu=8.0,
            used_cpu=4.0,
            available_cpu=4.0,
            cpu_utilization=50.0,
            total_memory=16.0,
            used_memory=8.0,
            available_memory=8.0,
            memory_utilization=50.0,
            sufficient=True
        ),
        backup_status=BackupStatus(
            backup_path="/backups",
            backup_valid=True
        ),
        job_status=JobStatus(
            safe_to_upgrade=True
        ),
        passed=True
    )


@pytest.fixture
def failed_resource_report():
    """Create a failed resource validation report."""
    resource_status = ResourceStatus(
        total_cpu=8.0,
        used_cpu=7.0,
        available_cpu=1.0,
        cpu_utilization=87.5,
        total_memory=16.0,
        used_memory=14.0,
        available_memory=2.0,
        memory_utilization=87.5,
        sufficient=False
    )
    resource_status.issues = ["CPU utilization too high"]
    
    backup_status = BackupStatus(
        backup_path="/backups",
        backup_valid=False
    )
    backup_status.issues = ["No backups found"]
    
    job_status = JobStatus(
        safe_to_upgrade=False
    )
    job_status.issues = ["Active jobs running"]
    
    return ValidationReport(
        timestamp=datetime.now(),
        resource_status=resource_status,
        backup_status=backup_status,
        job_status=job_status,
        passed=False
    )


class TestPreUpgradeValidator:
    """Tests for PreUpgradeValidator class."""
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_init(self, mock_pod_checker, mock_aggregator, mock_resource_validator):
        """Test initialization."""
        validator = PreUpgradeValidator(
            in_cluster=False,
            check_endpoints=True,
            backup_path="/test/backups",
            namespace="test-namespace"
        )
        
        assert validator.namespace == "test-namespace"
        assert validator.backup_path == "/test/backups"
        assert validator.check_endpoints is True
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_validate_all_passed(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator,
        healthy_health_report,
        passed_resource_report
    ):
        """Test validation when all checks pass."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Mock successful checks
        validator.health_aggregator.check_all_services.return_value = healthy_health_report
        validator.resource_validator.validate_all.return_value = passed_resource_report
        
        # Execute
        report = validator.validate()
        
        # Verify
        assert report.passed is True
        assert len(report.failures) == 0
        assert report.health_report is not None
        assert report.resource_report is not None
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_validate_health_failure(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator,
        unhealthy_health_report,
        passed_resource_report
    ):
        """Test validation when health check fails."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Mock health failure
        validator.health_aggregator.check_all_services.return_value = unhealthy_health_report
        validator.resource_validator.validate_all.return_value = passed_resource_report
        
        # Execute
        report = validator.validate()
        
        # Verify
        assert report.passed is False
        assert len(report.failures) > 0
        assert any(f.category == "health" for f in report.failures)
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_validate_resource_failure(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator,
        healthy_health_report,
        failed_resource_report
    ):
        """Test validation when resource check fails."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Mock resource failure
        validator.health_aggregator.check_all_services.return_value = healthy_health_report
        validator.resource_validator.validate_all.return_value = failed_resource_report
        
        # Execute
        report = validator.validate()
        
        # Verify
        assert report.passed is False
        assert len(report.failures) > 0
        assert any(f.category == "resources" for f in report.failures)
        assert any(f.category == "backups" for f in report.failures)
        assert any(f.category == "jobs" for f in report.failures)
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_validate_exception_handling(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator
    ):
        """Test validation handles exceptions gracefully."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Mock exceptions
        validator.health_aggregator.check_all_services.side_effect = Exception("Health check failed")
        validator.resource_validator.validate_all.side_effect = Exception("Resource check failed")
        
        # Execute
        report = validator.validate()
        
        # Verify
        assert report.passed is False
        assert len(report.failures) >= 2
        assert any("Failed to check service health" in f.description for f in report.failures)
        assert any("Failed to validate resources" in f.description for f in report.failures)
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_validate_and_halt_on_failure_success(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator,
        healthy_health_report,
        passed_resource_report
    ):
        """Test validate_and_halt_on_failure when validation passes."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Mock successful checks
        validator.health_aggregator.check_all_services.return_value = healthy_health_report
        validator.resource_validator.validate_all.return_value = passed_resource_report
        
        # Execute - should not raise
        report = validator.validate_and_halt_on_failure()
        
        # Verify
        assert report.passed is True
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_validate_and_halt_on_failure_raises(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator,
        unhealthy_health_report,
        passed_resource_report
    ):
        """Test validate_and_halt_on_failure raises on failure."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Mock health failure
        validator.health_aggregator.check_all_services.return_value = unhealthy_health_report
        validator.resource_validator.validate_all.return_value = passed_resource_report
        
        # Execute and verify exception is raised
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_and_halt_on_failure()
        
        assert exc_info.value.report is not None
        assert not exc_info.value.report.passed
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_generate_detailed_report_text(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator,
        healthy_health_report,
        passed_resource_report
    ):
        """Test generating text format report."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Mock successful checks
        validator.health_aggregator.check_all_services.return_value = healthy_health_report
        validator.resource_validator.validate_all.return_value = passed_resource_report
        
        # Execute
        report_text = validator.generate_detailed_report(output_format="text")
        
        # Verify
        assert "PRE-UPGRADE VALIDATION REPORT" in report_text
        assert "PASSED" in report_text
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_generate_detailed_report_json(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator,
        healthy_health_report,
        passed_resource_report
    ):
        """Test generating JSON format report."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Mock successful checks
        validator.health_aggregator.check_all_services.return_value = healthy_health_report
        validator.resource_validator.validate_all.return_value = passed_resource_report
        
        # Execute
        report_json = validator.generate_detailed_report(output_format="json")
        
        # Verify
        import json
        data = json.loads(report_json)
        assert "timestamp" in data
        assert "passed" in data
        assert data["passed"] is True
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_generate_detailed_report_markdown(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator,
        healthy_health_report,
        passed_resource_report
    ):
        """Test generating Markdown format report."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Mock successful checks
        validator.health_aggregator.check_all_services.return_value = healthy_health_report
        validator.resource_validator.validate_all.return_value = passed_resource_report
        
        # Execute
        report_md = validator.generate_detailed_report(output_format="markdown")
        
        # Verify
        assert "# Pre-Upgrade Validation Report" in report_md
        assert "✅ PASSED" in report_md
    
    @patch('health.validator.ResourceValidator')
    @patch('health.validator.HealthAggregator')
    @patch('health.validator.PodStatusChecker')
    def test_generate_detailed_report_invalid_format(
        self,
        mock_pod_checker,
        mock_aggregator,
        mock_resource_validator
    ):
        """Test generating report with invalid format."""
        validator = PreUpgradeValidator(in_cluster=False)
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="Unsupported output format"):
            validator.generate_detailed_report(output_format="invalid")


class TestValidationFailure:
    """Tests for ValidationFailure class."""
    
    def test_validation_failure_creation(self):
        """Test creating a validation failure."""
        failure = ValidationFailure(
            category="health",
            severity="critical",
            description="Service is down",
            remediation="Restart the service"
        )
        
        assert failure.category == "health"
        assert failure.severity == "critical"
        assert failure.description == "Service is down"
        assert failure.remediation == "Restart the service"
        assert failure.details is None


class TestPreUpgradeValidationReport:
    """Tests for PreUpgradeValidationReport class."""
    
    def test_report_summary_passed(self):
        """Test report summary when validation passes."""
        report = PreUpgradeValidationReport(
            timestamp=datetime.now(),
            passed=True,
            failures=[],
            warnings=[]
        )
        
        summary = report.summary
        assert "PASSED" in summary
        assert "ready for upgrade" in summary
    
    def test_report_summary_failed(self):
        """Test report summary when validation fails."""
        failures = [
            ValidationFailure(
                category="health",
                severity="critical",
                description="Service down",
                remediation="Restart service"
            )
        ]
        
        report = PreUpgradeValidationReport(
            timestamp=datetime.now(),
            passed=False,
            failures=failures,
            warnings=[]
        )
        
        summary = report.summary
        assert "FAILED" in summary
        assert "CANNOT PROCEED" in summary
        assert "Service down" in summary
