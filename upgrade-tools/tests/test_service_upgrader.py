"""Tests for service upgrader."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.executor.service_upgrader import ServiceUpgrader, ServiceUpgradeResult
from src.executor.helm_executor import DeploymentResult, HelmExecutor
from src.health.aggregator import HealthAggregator, HealthReport


class TestServiceUpgrader:
    """Test suite for ServiceUpgrader."""
    
    @pytest.fixture
    def mock_helm_executor(self):
        """Create mock helm executor."""
        return Mock(spec=HelmExecutor)
    
    @pytest.fixture
    def mock_health_aggregator(self):
        """Create mock health aggregator."""
        return Mock(spec=HealthAggregator)
    
    @pytest.fixture
    def service_upgrader(self, mock_helm_executor, mock_health_aggregator):
        """Create service upgrader instance."""
        return ServiceUpgrader(
            helm_executor=mock_helm_executor,
            health_aggregator=mock_health_aggregator,
            chart_versions_path="/path/to/versions.yaml",
            overrides_base_path="/path/to/overrides"
        )
    
    def test_init(self, mock_helm_executor, mock_health_aggregator):
        """Test initialization."""
        upgrader = ServiceUpgrader(
            helm_executor=mock_helm_executor,
            health_aggregator=mock_health_aggregator,
            chart_versions_path="/path/to/versions.yaml",
            overrides_base_path="/path/to/overrides"
        )
        
        assert upgrader.helm_executor == mock_helm_executor
        assert upgrader.health_aggregator == mock_health_aggregator
        assert upgrader.chart_versions_path == "/path/to/versions.yaml"
        assert upgrader.overrides_base_path == "/path/to/overrides"
    
    def test_upgrade_service_success(self, service_upgrader, mock_helm_executor, mock_health_aggregator):
        """Test successful service upgrade."""
        # Mock successful deployment
        mock_helm_executor.apply_chart.return_value = DeploymentResult(
            success=True,
            chart_name="keystone",
            release_name="keystone",
            revision=2,
            duration=120.0,
            pod_status={"keystone-api": "Running"},
            errors=[],
            warnings=[]
        )
        
        # Mock successful stabilization
        mock_helm_executor.wait_for_ready.return_value = True
        
        # Mock successful health check
        mock_health_aggregator.check_openstack_health.return_value = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        result = service_upgrader.upgrade_service(
            service_name="keystone",
            chart_path="/path/to/keystone"
        )
        
        assert result.success is True
        assert result.service_name == "keystone"
        assert result.health_check_passed is True
        assert len(result.errors) == 0
    
    def test_upgrade_service_deployment_failure(self, service_upgrader, mock_helm_executor):
        """Test service upgrade with deployment failure."""
        # Mock failed deployment
        mock_helm_executor.apply_chart.return_value = DeploymentResult(
            success=False,
            chart_name="keystone",
            release_name="keystone",
            revision=0,
            duration=60.0,
            pod_status={},
            errors=["Deployment failed"],
            warnings=[]
        )
        
        result = service_upgrader.upgrade_service(
            service_name="keystone",
            chart_path="/path/to/keystone"
        )
        
        assert result.success is False
        assert len(result.errors) > 0
        assert result.health_check_passed is False
    
    def test_upgrade_service_stabilization_failure(self, service_upgrader, mock_helm_executor, mock_health_aggregator):
        """Test service upgrade with stabilization failure."""
        # Mock successful deployment
        mock_helm_executor.apply_chart.return_value = DeploymentResult(
            success=True,
            chart_name="keystone",
            release_name="keystone",
            revision=2,
            duration=120.0,
            pod_status={"keystone-api": "Running"},
            errors=[],
            warnings=[]
        )
        
        # Mock failed stabilization
        mock_helm_executor.wait_for_ready.return_value = False
        
        result = service_upgrader.upgrade_service(
            service_name="keystone",
            chart_path="/path/to/keystone"
        )
        
        assert result.success is False
        assert "did not stabilize" in result.errors[0]
    
    def test_upgrade_service_health_check_failure(self, service_upgrader, mock_helm_executor, mock_health_aggregator):
        """Test service upgrade with health check failure."""
        # Mock successful deployment
        mock_helm_executor.apply_chart.return_value = DeploymentResult(
            success=True,
            chart_name="keystone",
            release_name="keystone",
            revision=2,
            duration=120.0,
            pod_status={"keystone-api": "Running"},
            errors=[],
            warnings=[]
        )
        
        # Mock successful stabilization
        mock_helm_executor.wait_for_ready.return_value = True
        
        # Mock failed health check
        mock_health_aggregator.check_openstack_health.return_value = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=False,
            services={}
        )
        
        result = service_upgrader.upgrade_service(
            service_name="keystone",
            chart_path="/path/to/keystone"
        )
        
        assert result.success is False
        assert result.health_check_passed is False
        assert "health check failed" in result.errors[0]
    
    def test_upgrade_service_with_job_cleanup(self, service_upgrader, mock_helm_executor, mock_health_aggregator):
        """Test service upgrade with job cleanup."""
        # Mock successful job cleanup
        mock_helm_executor.delete_jobs.return_value = True
        
        # Mock successful deployment
        mock_helm_executor.apply_chart.return_value = DeploymentResult(
            success=True,
            chart_name="nova",
            release_name="nova",
            revision=2,
            duration=120.0,
            pod_status={"nova-api": "Running"},
            errors=[],
            warnings=[]
        )
        
        # Mock successful stabilization
        mock_helm_executor.wait_for_ready.return_value = True
        
        # Mock successful health check
        mock_health_aggregator.check_openstack_health.return_value = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        result = service_upgrader.upgrade_service(
            service_name="nova",
            chart_path="/path/to/nova"
        )
        
        # Verify job cleanup was called
        mock_helm_executor.delete_jobs.assert_called_once_with("nova")
        assert result.success is True
    
    def test_upgrade_service_job_cleanup_failure(self, service_upgrader, mock_helm_executor, mock_health_aggregator):
        """Test service upgrade when job cleanup fails."""
        # Mock failed job cleanup
        mock_helm_executor.delete_jobs.return_value = False
        
        # Mock successful deployment
        mock_helm_executor.apply_chart.return_value = DeploymentResult(
            success=True,
            chart_name="nova",
            release_name="nova",
            revision=2,
            duration=120.0,
            pod_status={"nova-api": "Running"},
            errors=[],
            warnings=[]
        )
        
        # Mock successful stabilization
        mock_helm_executor.wait_for_ready.return_value = True
        
        # Mock successful health check
        mock_health_aggregator.check_openstack_health.return_value = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        result = service_upgrader.upgrade_service(
            service_name="nova",
            chart_path="/path/to/nova"
        )
        
        # Should have warning but still succeed
        assert result.success is True
        assert len(result.warnings) > 0
        assert "Failed to clean up jobs" in result.warnings[0]
    
    def test_upgrade_service_exception_handling(self, service_upgrader, mock_helm_executor):
        """Test service upgrade with unexpected exception."""
        # Mock exception during deployment
        mock_helm_executor.apply_chart.side_effect = Exception("Unexpected error")
        
        result = service_upgrader.upgrade_service(
            service_name="keystone",
            chart_path="/path/to/keystone"
        )
        
        assert result.success is False
        assert "Unexpected error" in result.errors[0]
    
    def test_cleanup_jobs(self, service_upgrader, mock_helm_executor):
        """Test job cleanup."""
        mock_helm_executor.delete_jobs.return_value = True
        
        result = service_upgrader._cleanup_jobs("nova")
        
        assert result is True
        mock_helm_executor.delete_jobs.assert_called_once_with("nova")
    
    def test_get_override_files(self, service_upgrader):
        """Test getting override files."""
        override_files = service_upgrader._get_override_files("keystone")
        
        assert len(override_files) == 1
        assert "keystone" in override_files[0]
        assert "helm-overrides.yaml" in override_files[0]
    
    def test_wait_for_stabilization(self, service_upgrader, mock_helm_executor):
        """Test waiting for stabilization."""
        mock_helm_executor.wait_for_ready.return_value = True
        
        result = service_upgrader._wait_for_stabilization("keystone")
        
        assert result is True
        mock_helm_executor.wait_for_ready.assert_called_once()
    
    def test_wait_for_stabilization_with_timeout(self, service_upgrader, mock_helm_executor):
        """Test waiting for stabilization with custom timeout."""
        mock_helm_executor.wait_for_ready.return_value = True
        
        result = service_upgrader._wait_for_stabilization("keystone", timeout=300)
        
        assert result is True
        # Verify timeout was passed
        call_args = mock_helm_executor.wait_for_ready.call_args
        assert call_args[1]["timeout"] == 300
    
    def test_verify_service_health(self, service_upgrader, mock_health_aggregator):
        """Test service health verification."""
        mock_health_aggregator.check_openstack_health.return_value = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services={}
        )
        
        result = service_upgrader._verify_service_health("keystone")
        
        assert result is True
    
    def test_verify_service_health_failure(self, service_upgrader, mock_health_aggregator):
        """Test service health verification failure."""
        mock_health_aggregator.check_openstack_health.return_value = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=False,
            services={}
        )
        
        result = service_upgrader._verify_service_health("keystone")
        
        assert result is False
    
    def test_verify_service_health_exception(self, service_upgrader, mock_health_aggregator):
        """Test service health verification with exception."""
        # Need to use the correct mock object
        mock_health_aggregator.check_openstack_health = Mock(side_effect=Exception("Health check error"))
        
        result = service_upgrader._verify_service_health("keystone")
        
        assert result is False
    
    def test_rollback_service_success(self, service_upgrader, mock_helm_executor):
        """Test successful service rollback."""
        mock_helm_executor.rollback_release.return_value = True
        mock_helm_executor.wait_for_ready.return_value = True
        
        result = service_upgrader.rollback_service("keystone")
        
        assert result is True
        mock_helm_executor.rollback_release.assert_called_once_with("keystone", None)
    
    def test_rollback_service_with_revision(self, service_upgrader, mock_helm_executor):
        """Test service rollback to specific revision."""
        mock_helm_executor.rollback_release.return_value = True
        mock_helm_executor.wait_for_ready.return_value = True
        
        result = service_upgrader.rollback_service("keystone", revision=5)
        
        assert result is True
        mock_helm_executor.rollback_release.assert_called_once_with("keystone", 5)
    
    def test_rollback_service_failure(self, service_upgrader, mock_helm_executor):
        """Test failed service rollback."""
        mock_helm_executor.rollback_release.return_value = False
        
        result = service_upgrader.rollback_service("keystone")
        
        assert result is False
    
    def test_rollback_service_stabilization_failure(self, service_upgrader, mock_helm_executor):
        """Test service rollback with stabilization failure."""
        mock_helm_executor.rollback_release.return_value = True
        mock_helm_executor.wait_for_ready.return_value = False
        
        result = service_upgrader.rollback_service("keystone")
        
        assert result is False
    
    def test_services_requiring_job_cleanup(self):
        """Test that expected services require job cleanup."""
        expected_services = ["nova", "neutron", "cinder", "heat"]
        
        for service in expected_services:
            assert service in ServiceUpgrader.SERVICES_REQUIRING_JOB_CLEANUP
