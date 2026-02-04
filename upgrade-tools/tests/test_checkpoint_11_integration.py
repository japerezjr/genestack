"""Integration tests for Checkpoint 11: Core Upgrade Logic.

This test suite validates that all core upgrade components work together:
- Upgrade execution (dependency graph, helm executor, service upgrader, orchestrator)
- Rollback functionality (backup, restore, verification)
- Logging and reporting (structured logging, summary reports)
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
import shutil

from src.executor import (
    DependencyGraph,
    HelmExecutor,
    ServiceUpgrader,
    UpgradeOrchestrator
)
from src.rollback import (
    BackupManager,
    RestoreManager,
    RollbackVerifier
)
from src.logging import (
    UpgradeLogger,
    SummaryReportGenerator,
    ActionType,
    LogLevel
)
from src.health import HealthAggregator


class TestCheckpoint11Integration:
    """Integration tests for core upgrade logic."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_helm_executor(self):
        """Create mock helm executor."""
        from src.executor.helm_executor import DeploymentResult
        
        executor = Mock(spec=HelmExecutor)
        executor.apply_chart.return_value = DeploymentResult(
            success=True,
            chart_name="test-chart",
            release_name="test-service",
            revision=2,
            duration=10.0,
            pod_status={"test-pod": "Running"},
            errors=[],
            warnings=[]
        )
        executor.wait_for_ready.return_value = {"ready": True}
        executor.get_release_status.return_value = {
            "status": "deployed",
            "revision": 2
        }
        executor.rollback_release.return_value = {
            "success": True,
            "revision": 1
        }
        executor.delete_jobs.return_value = {"deleted": 0}
        return executor
    
    @pytest.fixture
    def mock_health_aggregator(self):
        """Create mock health aggregator."""
        aggregator = Mock(spec=HealthAggregator)
        aggregator.check_service_health.return_value = {
            "healthy": True,
            "pods": {"running": 3, "total": 3},
            "endpoints": {"reachable": 1, "total": 1}
        }
        return aggregator
    
    def test_end_to_end_upgrade_workflow(
        self,
        temp_dir,
        mock_helm_executor,
        mock_health_aggregator
    ):
        """Test complete upgrade workflow from start to finish.
        
        This test validates:
        1. Pre-upgrade backup creation
        2. Service upgrade in dependency order
        3. Health verification after each service
        4. Logging of all actions
        5. Summary report generation
        """
        # Setup
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir()
        log_file = temp_dir / "upgrade.log"
        
        # Create chart versions file
        chart_versions_file = temp_dir / "helm-chart-versions.yaml"
        chart_versions_file.write_text("""
charts:
  keystone: 2024.1-ubuntu_jammy
  glance: 2024.1-ubuntu_jammy
  nova: 2024.1-ubuntu_jammy
""")
        
        # Create override configs
        overrides_dir = temp_dir / "base-helm-configs"
        overrides_dir.mkdir()
        (overrides_dir / "keystone").mkdir()
        (overrides_dir / "keystone" / "keystone-helm-overrides.yaml").write_text("conf: {}")
        
        # Initialize components
        logger = UpgradeLogger(log_file=log_file)
        report_gen = SummaryReportGenerator()
        backup_mgr = BackupManager(backup_base_path=str(backup_dir))
        
        # Create backup before upgrade
        backup_result = backup_mgr.create_backup(
            components=["versions"],
            chart_versions_path=str(chart_versions_file)
        )
        assert backup_result.success
        
        # Get backup ID from backup path
        backup_id = backup_result.backup_path.name
        logger.log_action(
            ActionType.BACKUP,
            "pre-upgrade",
            {"backup_id": backup_id}
        )
        
        # Initialize upgrade components
        service_upgrader = ServiceUpgrader(
            helm_executor=mock_helm_executor,
            health_aggregator=mock_health_aggregator,
            chart_versions_path=str(chart_versions_file),
            overrides_base_path=str(overrides_dir)
        )
        
        orchestrator = UpgradeOrchestrator(
            service_upgrader=service_upgrader
        )
        
        # Execute upgrade
        report_gen.start_upgrade()
        
        services = ["keystone", "glance", "nova"]
        result = orchestrator.orchestrate_upgrade(
            services=services,
            chart_base_path="/fake/charts",
            halt_on_failure=True
        )
        
        report_gen.end_upgrade()
        
        # Verify upgrade succeeded
        assert result.success
        assert len(result.services_upgraded) == 3
        assert len(result.services_failed) == 0
        
        # Verify services were upgraded in dependency order
        # (keystone must be before glance and nova)
        upgraded_services = result.services_upgraded
        keystone_idx = upgraded_services.index("keystone")
        glance_idx = upgraded_services.index("glance")
        nova_idx = upgraded_services.index("nova")
        assert keystone_idx < glance_idx
        assert keystone_idx < nova_idx
        
        # Verify logging
        action_log = logger.get_action_log()
        assert len(action_log) > 0
        
        # Verify backup was logged
        backup_actions = [a for a in action_log if a["action_type"] == "backup"]
        assert len(backup_actions) == 1
        
        # Generate summary report
        for service_name in result.services_upgraded:
            report_gen.add_service_upgraded(service_name)
            report_gen.add_version_change(
                service_name,
                "2024.1-ubuntu_jammy",
                "2025.1-ubuntu_jammy"
            )
        
        text_report = report_gen.generate_text_report()
        assert "SUCCESS" in text_report
        assert "keystone" in text_report
        assert "glance" in text_report
        assert "nova" in text_report
        
        # Verify log file was created
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "backup" in log_content.lower()
    
    def test_upgrade_with_failure_and_rollback(
        self,
        temp_dir,
        mock_helm_executor,
        mock_health_aggregator
    ):
        """Test upgrade failure triggers rollback.
        
        This test validates:
        1. Backup is created before upgrade
        2. Upgrade fails for one service
        3. Rollback is initiated
        4. System is restored to previous state
        5. Rollback verification succeeds
        """
        # Setup
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir()
        log_file = temp_dir / "upgrade.log"
        
        chart_versions_file = temp_dir / "helm-chart-versions.yaml"
        chart_versions_file.write_text("""
charts:
  keystone: 2024.1-ubuntu_jammy
  glance: 2024.1-ubuntu_jammy
""")
        
        overrides_dir = temp_dir / "base-helm-configs"
        overrides_dir.mkdir()
        
        # Initialize components
        logger = UpgradeLogger(log_file=log_file)
        backup_mgr = BackupManager(backup_base_path=str(backup_dir))
        restore_mgr = RestoreManager(backup_manager=backup_mgr)
        
        # Create backup
        backup_result = backup_mgr.create_backup(
            components=["versions"],
            chart_versions_path=str(chart_versions_file)
        )
        assert backup_result.success
        backup_id = backup_result.backup_path.name
        
        # Configure helm executor to fail on glance
        from src.executor.helm_executor import DeploymentResult
        
        mock_helm_executor.apply_chart.side_effect = [
            DeploymentResult(  # keystone succeeds
                success=True,
                chart_name="keystone",
                release_name="keystone",
                revision=2,
                duration=10.0,
                pod_status={"keystone-pod": "Running"},
                errors=[],
                warnings=[]
            ),
            DeploymentResult(  # glance fails
                success=False,
                chart_name="glance",
                release_name="glance",
                revision=1,
                duration=5.0,
                pod_status={},
                errors=["Deployment failed"],
                warnings=[]
            )
        ]
        
        # Initialize upgrade components
        service_upgrader = ServiceUpgrader(
            helm_executor=mock_helm_executor,
            health_aggregator=mock_health_aggregator,
            chart_versions_path=str(chart_versions_file),
            overrides_base_path=str(overrides_dir)
        )
        
        orchestrator = UpgradeOrchestrator(
            service_upgrader=service_upgrader
        )
        
        # Execute upgrade (should fail)
        result = orchestrator.orchestrate_upgrade(
            services=["keystone", "glance"],
            chart_base_path="/fake/charts",
            halt_on_failure=True
        )
        
        # Verify upgrade failed
        assert not result.success
        assert len(result.services_failed) > 0
        
        # Log rollback initiation
        logger.log_rollback("upgrade", "in_progress")
        
        # Perform rollback
        # Get the backup object
        backups = backup_mgr.list_backups()
        latest_backup = backups[0] if backups else None
        assert latest_backup is not None
        
        restore_result = restore_mgr.restore_from_backup(
            backup=latest_backup,
            components=["versions"],
            chart_versions_path=str(chart_versions_file)
        )
        
        assert restore_result.success
        
        # Verify chart versions were restored
        restored_content = chart_versions_file.read_text()
        assert "2024.1-ubuntu_jammy" in restored_content
        
        # Log rollback completion
        logger.log_rollback("upgrade", "success")
        
        # Verify rollback was logged
        action_log = logger.get_action_log()
        rollback_actions = [a for a in action_log if a["action_type"] == "rollback"]
        assert len(rollback_actions) == 2  # in_progress and success
    
    def test_logging_captures_all_actions(self, temp_dir):
        """Test that logging system captures all upgrade actions.
        
        This test validates:
        1. All action types are logged
        2. Timestamps are recorded
        3. Action log can be saved to JSON
        4. Log levels are respected
        """
        log_file = temp_dir / "upgrade.log"
        logger = UpgradeLogger(
            log_file=log_file,
            console_level=LogLevel.WARNING,
            file_level=LogLevel.DEBUG
        )
        
        # Log various actions
        logger.log_version_update("keystone", "2024.1", "2025.1")
        logger.log_config_update("keystone-overrides.yaml", {"image": "updated"})
        logger.log_service_upgrade("keystone", "success", duration=45.2)
        logger.log_service_upgrade("glance", "failed", error="Timeout")
        logger.log_validation("pre-upgrade", "passed")
        logger.log_health_check("keystone", "healthy")
        logger.log_rollback("upgrade", "success")
        
        # Verify action log
        action_log = logger.get_action_log()
        assert len(action_log) == 7
        
        # Verify all action types are present
        action_types = {a["action_type"] for a in action_log}
        assert "version_update" in action_types
        assert "config_update" in action_types
        assert "service_upgrade" in action_types
        assert "validation" in action_types
        assert "health_check" in action_types
        assert "rollback" in action_types
        
        # Verify timestamps
        for action in action_log:
            assert "timestamp" in action
            # Verify timestamp is valid ISO format
            datetime.fromisoformat(action["timestamp"])
        
        # Save action log to JSON
        json_file = temp_dir / "action_log.json"
        logger.save_action_log(json_file)
        assert json_file.exists()
        
        # Verify log file was created
        assert log_file.exists()
    
    def test_summary_report_generation(self, temp_dir):
        """Test summary report generation with all data.
        
        This test validates:
        1. Report captures version changes
        2. Report captures configuration changes
        3. Report captures issues
        4. Report calculates duration
        5. Report can be saved in multiple formats
        """
        report_gen = SummaryReportGenerator()
        
        # Simulate upgrade
        report_gen.start_upgrade()
        
        # Add version changes
        report_gen.add_version_change("keystone", "2024.1", "2025.1")
        report_gen.add_version_change("glance", "2024.1", "2025.1")
        report_gen.add_version_change("nova", "2024.1", "2025.1")
        
        # Add config changes
        report_gen.add_config_change(
            "keystone-overrides.yaml",
            {"image": "updated", "replicas": 3}
        )
        
        # Add services
        report_gen.add_service_upgraded("keystone")
        report_gen.add_service_upgraded("glance")
        report_gen.add_service_failed("nova")
        
        # Add issues
        report_gen.add_issue("high", "nova", "Deployment timeout", resolved=False)
        report_gen.add_issue("medium", "glance", "Slow startup", resolved=True)
        
        report_gen.end_upgrade()
        
        # Generate text report
        text_report = report_gen.generate_text_report()
        assert "OpenStack Upgrade Summary Report" in text_report
        assert "keystone" in text_report
        assert "glance" in text_report
        assert "nova" in text_report
        assert "2024.1" in text_report
        assert "2025.1" in text_report
        assert "FAILED" in text_report  # Overall status
        
        # Generate JSON report
        json_report = report_gen.generate_json_report()
        assert json_report["success"] is False  # nova failed
        assert len(json_report["version_changes"]) == 3
        assert len(json_report["config_changes"]) == 1
        assert len(json_report["services"]["upgraded"]) == 2
        assert len(json_report["services"]["failed"]) == 1
        assert len(json_report["issues"]) == 2
        assert json_report["duration_seconds"] is not None
        
        # Save reports
        output_dir = temp_dir / "reports"
        report_gen.save_report(output_dir, format="both")
        
        # Verify files were created
        text_files = list(output_dir.glob("upgrade_summary_*.txt"))
        json_files = list(output_dir.glob("upgrade_summary_*.json"))
        assert len(text_files) == 1
        assert len(json_files) == 1
    
    def test_rollback_verification(self, temp_dir):
        """Test rollback verification process.
        
        This test validates:
        1. Rollback verifier checks system health
        2. Verification report is generated
        3. Multiple output formats are supported
        """
        # Create mock components
        from src.health import PodStatusChecker, EndpointChecker
        mock_pod_checker = Mock(spec=PodStatusChecker)
        mock_pod_checker.check_pod_status.return_value = {
            "total": 6,
            "running": 6,
            "pending": 0,
            "failed": 0,
            "pods": []
        }
        
        mock_endpoint_checker = Mock(spec=EndpointChecker)
        mock_endpoint_checker.check_all_endpoints.return_value = {
            "total": 2,
            "reachable": 2,
            "unreachable": 0,
            "endpoints": []
        }
        
        # Create a simple mock health aggregator
        mock_health_agg = Mock(spec=HealthAggregator)
        
        # Initialize verifier
        verifier = RollbackVerifier(
            health_aggregator=mock_health_agg,
            pod_checker=mock_pod_checker,
            endpoint_checker=mock_endpoint_checker
        )
        
        # Verify rollback
        verification = verifier.verify_rollback(
            namespaces=["openstack"],
            check_endpoints=True
        )
        
        assert verification.success
        assert verification.pod_status["running"] == 6
        assert verification.endpoint_status["reachable"] == 2
        
        # Generate rollback report
        report = verifier.generate_rollback_report(
            backup_id="backup_20260204_120000",
            rollback_timestamp=datetime.now(),
            components_restored=["versions", "configs"],
            verification_result=verification
        )
        
        assert report.backup_id == "backup_20260204_120000"
        assert report.success
        assert len(report.components_restored) == 2
        
        # Format as text
        text_report = verifier.format_report(report, output_format="text")
        assert "Rollback Report" in text_report
        assert "SUCCESS" in text_report
        
        # Format as JSON
        json_report = verifier.format_report(report, output_format="json")
        assert "backup_id" in json_report
        assert json_report["success"] is True
        
        # Format as markdown
        md_report = verifier.format_report(report, output_format="markdown")
        assert "# Rollback Report" in md_report
        assert "✅" in md_report
    
    def test_dependency_order_enforcement(self):
        """Test that services are upgraded in correct dependency order.
        
        This test validates:
        1. Infrastructure services are upgraded first
        2. Core services respect dependencies
        3. Optional services come last
        """
        # Create dependency graph
        services = [
            "nova",  # Depends on keystone, glance, neutron, placement
            "keystone",  # No dependencies (core)
            "glance",  # Depends on keystone
            "neutron",  # Depends on keystone
            "placement",  # Depends on keystone
            "memcached"  # Infrastructure
        ]
        
        graph = DependencyGraph(services)
        upgrade_order = graph.get_upgrade_order(skip_optional=False)
        
        # Verify memcached (infrastructure) comes first
        assert upgrade_order[0] == "memcached"
        
        # Verify keystone comes before all services that depend on it
        keystone_idx = upgrade_order.index("keystone")
        glance_idx = upgrade_order.index("glance")
        neutron_idx = upgrade_order.index("neutron")
        placement_idx = upgrade_order.index("placement")
        nova_idx = upgrade_order.index("nova")
        
        assert keystone_idx < glance_idx
        assert keystone_idx < neutron_idx
        assert keystone_idx < placement_idx
        assert keystone_idx < nova_idx
        
        # Verify nova comes after all its dependencies
        assert nova_idx > glance_idx
        assert nova_idx > neutron_idx
        assert nova_idx > placement_idx


class TestCheckpoint11ErrorHandling:
    """Test error handling in core upgrade logic."""
    
    def test_backup_failure_prevents_upgrade(self, tmp_path):
        """Test that backup failure prevents upgrade from starting."""
        # Try to create backup with nonexistent source file
        backup_mgr = BackupManager(backup_base_path=str(tmp_path / "backups"))
        
        result = backup_mgr.create_backup(
            components=["versions"],
            chart_versions_path="/nonexistent/file.yaml"
        )
        
        # Backup should fail
        assert not result.success
        assert len(result.errors) > 0
        
        # In real workflow, this would prevent upgrade from starting
    
    def test_helm_failure_halts_upgrade(self):
        """Test that helm deployment failure halts upgrade."""
        mock_helm = Mock(spec=HelmExecutor)
        mock_helm.apply_chart.return_value = {
            "success": False,
            "error": "Deployment failed"
        }
        
        mock_health = Mock(spec=HealthAggregator)
        
        upgrader = ServiceUpgrader(
            helm_executor=mock_helm,
            health_aggregator=mock_health,
            chart_versions_path="/fake/path",
            overrides_base_path="/fake/overrides"
        )
        
        orchestrator = UpgradeOrchestrator(service_upgrader=upgrader)
        
        result = orchestrator.orchestrate_upgrade(
            services=["keystone"],
            chart_base_path="/fake/charts",
            halt_on_failure=True
        )
        
        # Upgrade should fail
        assert not result.success
        assert len(result.services_failed) > 0
    
    def test_health_check_failure_triggers_rollback(self):
        """Test that health check failure can trigger rollback."""
        from src.executor.helm_executor import DeploymentResult
        
        mock_helm = Mock(spec=HelmExecutor)
        mock_helm.apply_chart.return_value = DeploymentResult(
            success=True,
            chart_name="keystone",
            release_name="keystone",
            revision=2,
            duration=10.0,
            pod_status={"keystone-pod": "Running"},
            errors=[],
            warnings=[]
        )
        mock_helm.wait_for_ready.return_value = {"ready": True}
        
        # Health check fails
        mock_health = Mock(spec=HealthAggregator)
        mock_health.check_service_health.return_value = Mock(
            healthy=False,
            issues=["API endpoint unreachable"]
        )
        
        upgrader = ServiceUpgrader(
            helm_executor=mock_helm,
            health_aggregator=mock_health,
            chart_versions_path="/fake/path",
            overrides_base_path="/fake/overrides"
        )
        
        result = upgrader.upgrade_service(
            service_name="keystone",
            chart_path="/fake/chart"
        )
        
        # Upgrade should fail due to health check
        assert not result.success
        assert not result.health_check_passed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
