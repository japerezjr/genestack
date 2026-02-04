"""Tests for rollback verifier."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from src.rollback.rollback_verifier import (
    RollbackVerifier,
    RollbackVerificationResult,
    RollbackReport
)
from src.health.aggregator import HealthReport, ServiceHealth, HealthAggregator
from src.health.pod_checker import PodStatusReport
from src.health.endpoint_checker import EndpointReport


@pytest.fixture
def mock_health_aggregator():
    """Create a mock health aggregator."""
    aggregator = Mock(spec=HealthAggregator)
    return aggregator


@pytest.fixture
def mock_pod_checker():
    """Create a mock pod checker."""
    checker = Mock()
    return checker


@pytest.fixture
def mock_endpoint_checker():
    """Create a mock endpoint checker."""
    checker = Mock()
    checker.catalog = {}
    return checker


@pytest.fixture
def rollback_verifier(mock_health_aggregator, mock_pod_checker, mock_endpoint_checker):
    """Create a rollback verifier with mocks."""
    return RollbackVerifier(
        health_aggregator=mock_health_aggregator,
        pod_checker=mock_pod_checker,
        endpoint_checker=mock_endpoint_checker
    )


@pytest.fixture
def healthy_pod_report():
    """Create a healthy pod status report."""
    return PodStatusReport(
        total_pods=10,
        running=10,
        pending=0,
        failed=0,
        succeeded=0,
        unknown=0,
        pods=[],
        healthy=True
    )


@pytest.fixture
def unhealthy_pod_report():
    """Create an unhealthy pod status report."""
    return PodStatusReport(
        total_pods=10,
        running=8,
        pending=1,
        failed=1,
        succeeded=0,
        unknown=0,
        pods=[],
        healthy=False
    )


@pytest.fixture
def healthy_endpoint_report():
    """Create a healthy endpoint report."""
    return EndpointReport(
        total_endpoints=5,
        reachable=5,
        unreachable=0,
        endpoints=[],
        healthy=True
    )


@pytest.fixture
def unhealthy_endpoint_report():
    """Create an unhealthy endpoint report."""
    return EndpointReport(
        total_endpoints=5,
        reachable=3,
        unreachable=2,
        endpoints=[],
        healthy=False
    )


class TestRollbackVerifier:
    """Test cases for RollbackVerifier."""
    
    def test_initialization(self):
        """Test rollback verifier initialization."""
        verifier = RollbackVerifier()
        
        assert verifier.pod_checker is not None
        assert verifier.health_aggregator is not None
    
    def test_verify_rollback_success(
        self,
        rollback_verifier,
        mock_health_aggregator,
        mock_pod_checker,
        healthy_pod_report,
        healthy_endpoint_report
    ):
        """Test successful rollback verification."""
        # Setup mocks
        service_health = ServiceHealth(
            service_name="openstack",
            pod_status=healthy_pod_report,
            endpoint_status=healthy_endpoint_report,
            healthy=True
        )
        
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={"openstack": service_health}
        )
        
        mock_health_aggregator.check_all_services.return_value = health_report
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        # Verify rollback
        result = rollback_verifier.verify_rollback()
        
        assert result.success
        assert result.pod_status_ok
        assert result.endpoints_ok
        assert len(result.issues) == 0
    
    def test_verify_rollback_unhealthy_pods(
        self,
        rollback_verifier,
        mock_health_aggregator,
        mock_pod_checker,
        unhealthy_pod_report
    ):
        """Test rollback verification with unhealthy pods."""
        # Setup mocks
        service_health = ServiceHealth(
            service_name="openstack",
            pod_status=unhealthy_pod_report,
            healthy=False
        )
        
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=False,
            services={"openstack": service_health}
        )
        
        mock_health_aggregator.check_all_services.return_value = health_report
        mock_pod_checker.check_namespace.return_value = unhealthy_pod_report
        
        # Verify rollback
        result = rollback_verifier.verify_rollback()
        
        assert not result.success
        assert not result.pod_status_ok
        assert len(result.issues) > 0
        assert "unhealthy pods" in result.issues[0].lower()
    
    def test_verify_rollback_unreachable_endpoints(
        self,
        rollback_verifier,
        mock_health_aggregator,
        mock_pod_checker,
        mock_endpoint_checker,
        healthy_pod_report,
        unhealthy_endpoint_report
    ):
        """Test rollback verification with unreachable endpoints."""
        # Setup mocks
        service_health = ServiceHealth(
            service_name="openstack",
            pod_status=healthy_pod_report,
            endpoint_status=unhealthy_endpoint_report,
            healthy=False
        )
        
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=False,
            services={"openstack": service_health}
        )
        
        mock_health_aggregator.check_all_services.return_value = health_report
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        mock_endpoint_checker.authenticate.return_value = None
        mock_endpoint_checker.check_all_endpoints.return_value = unhealthy_endpoint_report
        
        # Verify rollback
        result = rollback_verifier.verify_rollback(check_endpoints=True)
        
        assert not result.success
        assert result.pod_status_ok
        assert not result.endpoints_ok
        assert len(result.issues) > 0
        assert "unreachable endpoints" in result.issues[0].lower()
    
    def test_verify_rollback_without_endpoints(
        self,
        rollback_verifier,
        mock_health_aggregator,
        mock_pod_checker,
        healthy_pod_report
    ):
        """Test rollback verification without checking endpoints."""
        # Setup mocks
        service_health = ServiceHealth(
            service_name="openstack",
            pod_status=healthy_pod_report,
            healthy=True
        )
        
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={"openstack": service_health}
        )
        
        mock_health_aggregator.check_all_services.return_value = health_report
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        # Verify rollback without endpoints
        result = rollback_verifier.verify_rollback(check_endpoints=False)
        
        assert result.success
        assert result.pod_status_ok
        # endpoints_ok should be True when not checking
        assert result.endpoints_ok
    
    def test_verify_service_health(
        self,
        rollback_verifier,
        mock_health_aggregator,
        healthy_pod_report,
        healthy_endpoint_report
    ):
        """Test verifying health of a specific service."""
        # Setup mocks
        service_health = ServiceHealth(
            service_name="keystone",
            pod_status=healthy_pod_report,
            endpoint_status=healthy_endpoint_report,
            healthy=True
        )
        
        mock_health_aggregator.check_service_health.return_value = service_health
        
        # Verify service
        result = rollback_verifier.verify_service_health("keystone")
        
        assert result.success
        assert result.pod_status_ok
        assert result.endpoints_ok
        assert "keystone" in result.health_report.services
    
    def test_generate_rollback_report(self, rollback_verifier):
        """Test generating a rollback report."""
        # Create verification result
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        verification_result = RollbackVerificationResult(
            success=True,
            timestamp=datetime.now(),
            health_report=health_report,
            pod_status_ok=True,
            endpoints_ok=True
        )
        
        # Generate report
        report = rollback_verifier.generate_rollback_report(
            backup_id="test_backup",
            rollback_timestamp=datetime.now(),
            components_restored=["versions", "configs"],
            verification_result=verification_result
        )
        
        assert report.backup_id == "test_backup"
        assert "versions" in report.components_restored
        assert "configs" in report.components_restored
        assert report.verification_result.success
    
    def test_rollback_report_summary(self):
        """Test rollback report summary generation."""
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        verification_result = RollbackVerificationResult(
            success=True,
            timestamp=datetime.now(),
            health_report=health_report,
            pod_status_ok=True,
            endpoints_ok=True
        )
        
        report = RollbackReport(
            backup_id="test_backup",
            rollback_timestamp=datetime.now(),
            verification_result=verification_result,
            components_restored=["versions", "configs"],
            services_verified=["keystone", "nova"]
        )
        
        assert "test_backup" in report.summary
        assert "SUCCESSFUL" in report.summary
        assert "versions" in report.summary
        assert "configs" in report.summary
    
    def test_format_text_report(self, rollback_verifier):
        """Test formatting report as text."""
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        verification_result = RollbackVerificationResult(
            success=True,
            timestamp=datetime.now(),
            health_report=health_report,
            pod_status_ok=True,
            endpoints_ok=True
        )
        
        report = RollbackReport(
            backup_id="test_backup",
            rollback_timestamp=datetime.now(),
            verification_result=verification_result,
            components_restored=["versions"],
            services_verified=[]
        )
        
        text = rollback_verifier.format_report(report, output_format="text")
        
        assert "ROLLBACK REPORT" in text
        assert "test_backup" in text
        assert "SUCCESSFUL" in text
    
    def test_format_json_report(self, rollback_verifier):
        """Test formatting report as JSON."""
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        verification_result = RollbackVerificationResult(
            success=True,
            timestamp=datetime.now(),
            health_report=health_report,
            pod_status_ok=True,
            endpoints_ok=True
        )
        
        report = RollbackReport(
            backup_id="test_backup",
            rollback_timestamp=datetime.now(),
            verification_result=verification_result,
            components_restored=["versions"],
            services_verified=[]
        )
        
        json_text = rollback_verifier.format_report(report, output_format="json")
        
        import json
        data = json.loads(json_text)
        
        assert data["backup_id"] == "test_backup"
        assert data["success"] is True
        assert "versions" in data["components_restored"]
    
    def test_format_markdown_report(self, rollback_verifier):
        """Test formatting report as Markdown."""
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        verification_result = RollbackVerificationResult(
            success=True,
            timestamp=datetime.now(),
            health_report=health_report,
            pod_status_ok=True,
            endpoints_ok=True
        )
        
        report = RollbackReport(
            backup_id="test_backup",
            rollback_timestamp=datetime.now(),
            verification_result=verification_result,
            components_restored=["versions"],
            services_verified=[]
        )
        
        markdown = rollback_verifier.format_report(report, output_format="markdown")
        
        assert "# Rollback Report" in markdown
        assert "test_backup" in markdown
        assert "✅" in markdown
    
    def test_format_invalid_format(self, rollback_verifier):
        """Test formatting with invalid format."""
        health_report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        verification_result = RollbackVerificationResult(
            success=True,
            timestamp=datetime.now(),
            health_report=health_report,
            pod_status_ok=True,
            endpoints_ok=True
        )
        
        report = RollbackReport(
            backup_id="test_backup",
            rollback_timestamp=datetime.now(),
            verification_result=verification_result,
            components_restored=["versions"],
            services_verified=[]
        )
        
        with pytest.raises(ValueError, match="Unsupported output format"):
            rollback_verifier.format_report(report, output_format="invalid")
