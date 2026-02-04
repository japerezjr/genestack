"""Tests for upgrade orchestrator."""

import pytest
from unittest.mock import Mock, patch
from src.executor.upgrade_orchestrator import UpgradeOrchestrator, UpgradeOrchestrationResult
from src.executor.service_upgrader import ServiceUpgrader, ServiceUpgradeResult
from src.executor.dependency_graph import DependencyGraph
from src.executor.helm_executor import DeploymentResult


class TestUpgradeOrchestrator:
    """Test suite for UpgradeOrchestrator."""
    
    @pytest.fixture
    def mock_service_upgrader(self):
        """Create mock service upgrader."""
        return Mock(spec=ServiceUpgrader)
    
    @pytest.fixture
    def orchestrator(self, mock_service_upgrader):
        """Create orchestrator instance."""
        return UpgradeOrchestrator(
            service_upgrader=mock_service_upgrader
        )
    
    def test_init(self, mock_service_upgrader):
        """Test initialization."""
        orchestrator = UpgradeOrchestrator(
            service_upgrader=mock_service_upgrader
        )
        
        assert orchestrator.service_upgrader == mock_service_upgrader
        assert orchestrator.dependency_graph is not None
        assert orchestrator.upgrade_log == []
    
    def test_init_with_custom_graph(self, mock_service_upgrader):
        """Test initialization with custom dependency graph."""
        custom_graph = DependencyGraph(["keystone", "glance"])
        
        orchestrator = UpgradeOrchestrator(
            service_upgrader=mock_service_upgrader,
            dependency_graph=custom_graph
        )
        
        assert orchestrator.dependency_graph == custom_graph
    
    def test_orchestrate_upgrade_success(self, orchestrator, mock_service_upgrader):
        """Test successful orchestration of multiple services."""
        # Mock successful upgrades
        def mock_upgrade(service_name, chart_path, timeout=None):
            return ServiceUpgradeResult(
                service_name=service_name,
                success=True,
                duration=60.0,
                deployment_result=None,
                health_check_passed=True,
                errors=[],
                warnings=[],
                timestamp="2025-01-01T00:00:00"
            )
        
        mock_service_upgrader.upgrade_service.side_effect = mock_upgrade
        
        result = orchestrator.orchestrate_upgrade(
            services=["memcached", "keystone", "glance"],
            chart_base_path="/path/to/charts"
        )
        
        assert result.success is True
        assert len(result.services_upgraded) == 3
        assert len(result.services_failed) == 0
        assert "memcached" in result.services_upgraded
        assert "keystone" in result.services_upgraded
        assert "glance" in result.services_upgraded
    
    def test_orchestrate_upgrade_with_failure(self, orchestrator, mock_service_upgrader):
        """Test orchestration with service failure."""
        # Mock upgrades with one failure
        def mock_upgrade(service_name, chart_path, timeout=None):
            if service_name == "keystone":
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=False,
                    duration=30.0,
                    deployment_result=None,
                    health_check_passed=False,
                    errors=["Deployment failed"],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                )
            else:
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=True,
                    duration=60.0,
                    deployment_result=None,
                    health_check_passed=True,
                    errors=[],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                )
        
        mock_service_upgrader.upgrade_service.side_effect = mock_upgrade
        
        result = orchestrator.orchestrate_upgrade(
            services=["memcached", "keystone", "glance"],
            chart_base_path="/path/to/charts",
            halt_on_failure=True
        )
        
        assert result.success is False
        assert "keystone" in result.services_failed
        assert len(result.errors) > 0
    
    def test_orchestrate_upgrade_halt_on_failure(self, orchestrator, mock_service_upgrader):
        """Test that orchestration halts on first failure."""
        # Mock upgrades with failure
        def mock_upgrade(service_name, chart_path, timeout=None):
            if service_name == "keystone":
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=False,
                    duration=30.0,
                    deployment_result=None,
                    health_check_passed=False,
                    errors=["Deployment failed"],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                )
            else:
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=True,
                    duration=60.0,
                    deployment_result=None,
                    health_check_passed=True,
                    errors=[],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                )
        
        mock_service_upgrader.upgrade_service.side_effect = mock_upgrade
        
        result = orchestrator.orchestrate_upgrade(
            services=["memcached", "keystone", "glance"],
            chart_base_path="/path/to/charts",
            halt_on_failure=True
        )
        
        # Should stop after keystone fails
        assert "memcached" in result.services_upgraded
        assert "keystone" in result.services_failed
        # glance should not be attempted
        assert "glance" not in result.services_upgraded
        assert "glance" not in result.services_failed
    
    def test_orchestrate_upgrade_continue_on_failure(self, orchestrator, mock_service_upgrader):
        """Test that orchestration continues on failure when configured."""
        # Mock upgrades with failure
        def mock_upgrade(service_name, chart_path, timeout=None):
            if service_name == "keystone":
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=False,
                    duration=30.0,
                    deployment_result=None,
                    health_check_passed=False,
                    errors=["Deployment failed"],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                )
            else:
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=True,
                    duration=60.0,
                    deployment_result=None,
                    health_check_passed=True,
                    errors=[],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                )
        
        mock_service_upgrader.upgrade_service.side_effect = mock_upgrade
        
        result = orchestrator.orchestrate_upgrade(
            services=["memcached", "keystone", "glance"],
            chart_base_path="/path/to/charts",
            halt_on_failure=False
        )
        
        # Should continue after keystone fails
        assert "memcached" in result.services_upgraded
        assert "keystone" in result.services_failed
        assert "glance" in result.services_upgraded
    
    def test_orchestrate_upgrade_respects_dependencies(self, orchestrator, mock_service_upgrader):
        """Test that orchestration respects service dependencies."""
        upgrade_order = []
        
        def mock_upgrade(service_name, chart_path, timeout=None):
            upgrade_order.append(service_name)
            return ServiceUpgradeResult(
                service_name=service_name,
                success=True,
                duration=60.0,
                deployment_result=None,
                health_check_passed=True,
                errors=[],
                warnings=[],
                timestamp="2025-01-01T00:00:00"
            )
        
        mock_service_upgrader.upgrade_service.side_effect = mock_upgrade
        
        result = orchestrator.orchestrate_upgrade(
            services=["glance", "keystone", "mariadb-operator"],
            chart_base_path="/path/to/charts"
        )
        
        # mariadb-operator should come before keystone
        # keystone should come before glance
        mariadb_idx = upgrade_order.index("mariadb-operator")
        keystone_idx = upgrade_order.index("keystone")
        glance_idx = upgrade_order.index("glance")
        
        assert mariadb_idx < keystone_idx
        assert keystone_idx < glance_idx
    
    def test_orchestrate_upgrade_with_warnings(self, orchestrator, mock_service_upgrader):
        """Test orchestration with service warnings."""
        def mock_upgrade(service_name, chart_path, timeout=None):
            return ServiceUpgradeResult(
                service_name=service_name,
                success=True,
                duration=60.0,
                deployment_result=None,
                health_check_passed=True,
                errors=[],
                warnings=["Job cleanup failed"],
                timestamp="2025-01-01T00:00:00"
            )
        
        mock_service_upgrader.upgrade_service.side_effect = mock_upgrade
        
        result = orchestrator.orchestrate_upgrade(
            services=["keystone"],
            chart_base_path="/path/to/charts"
        )
        
        assert result.success is True
        assert len(result.warnings) > 0
    
    def test_orchestrate_upgrade_exception_handling(self, orchestrator, mock_service_upgrader):
        """Test orchestration with unexpected exception."""
        mock_service_upgrader.upgrade_service.side_effect = Exception("Unexpected error")
        
        result = orchestrator.orchestrate_upgrade(
            services=["keystone"],
            chart_base_path="/path/to/charts"
        )
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "Orchestration error" in result.errors[0]
    
    def test_orchestrate_full_upgrade(self, orchestrator, mock_service_upgrader):
        """Test orchestrating full upgrade of all services."""
        def mock_upgrade(service_name, chart_path, timeout=None):
            return ServiceUpgradeResult(
                service_name=service_name,
                success=True,
                duration=60.0,
                deployment_result=None,
                health_check_passed=True,
                errors=[],
                warnings=[],
                timestamp="2025-01-01T00:00:00"
            )
        
        mock_service_upgrader.upgrade_service.side_effect = mock_upgrade
        
        result = orchestrator.orchestrate_full_upgrade(
            chart_base_path="/path/to/charts",
            skip_optional=True
        )
        
        # Should upgrade infrastructure and core services
        assert result.success is True
        assert len(result.services_upgraded) > 0
    
    def test_log_action(self, orchestrator):
        """Test logging actions."""
        orchestrator._log_action("Test message")
        
        assert len(orchestrator.upgrade_log) == 1
        assert "Test message" in orchestrator.upgrade_log[0]
    
    def test_get_upgrade_log(self, orchestrator):
        """Test getting upgrade log."""
        orchestrator._log_action("Message 1")
        orchestrator._log_action("Message 2")
        
        log = orchestrator.get_upgrade_log()
        
        assert len(log) == 2
        assert "Message 1" in log[0]
        assert "Message 2" in log[1]
    
    def test_generate_upgrade_report(self, orchestrator):
        """Test generating upgrade report."""
        result = UpgradeOrchestrationResult(
            success=True,
            total_duration=180.0,
            services_upgraded=["keystone", "glance"],
            services_failed=[],
            service_results={
                "keystone": ServiceUpgradeResult(
                    service_name="keystone",
                    success=True,
                    duration=90.0,
                    deployment_result=None,
                    health_check_passed=True,
                    errors=[],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                ),
                "glance": ServiceUpgradeResult(
                    service_name="glance",
                    success=True,
                    duration=90.0,
                    deployment_result=None,
                    health_check_passed=True,
                    errors=[],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                )
            },
            errors=[],
            warnings=[],
            timestamp="2025-01-01T00:00:00"
        )
        
        report = orchestrator.generate_upgrade_report(result)
        
        assert "OpenStack Upgrade Report" in report
        assert "SUCCESS" in report
        assert "keystone" in report
        assert "glance" in report
    
    def test_generate_upgrade_report_with_failures(self, orchestrator):
        """Test generating upgrade report with failures."""
        result = UpgradeOrchestrationResult(
            success=False,
            total_duration=120.0,
            services_upgraded=["keystone"],
            services_failed=["glance"],
            service_results={
                "keystone": ServiceUpgradeResult(
                    service_name="keystone",
                    success=True,
                    duration=60.0,
                    deployment_result=None,
                    health_check_passed=True,
                    errors=[],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                ),
                "glance": ServiceUpgradeResult(
                    service_name="glance",
                    success=False,
                    duration=60.0,
                    deployment_result=None,
                    health_check_passed=False,
                    errors=["Deployment failed"],
                    warnings=[],
                    timestamp="2025-01-01T00:00:00"
                )
            },
            errors=["Failed to upgrade glance: Deployment failed"],
            warnings=[],
            timestamp="2025-01-01T00:00:00"
        )
        
        report = orchestrator.generate_upgrade_report(result)
        
        assert "FAILED" in report
        assert "Failed Services:" in report
        assert "glance" in report
        assert "Deployment failed" in report
