"""Tests for Helm executor wrapper."""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
from src.executor.helm_executor import HelmExecutor, DeploymentResult, ReleaseStatus


class TestHelmExecutor:
    """Test suite for HelmExecutor."""
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        executor = HelmExecutor()
        
        assert executor.namespace == "openstack"
        assert executor.timeout == 600
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        executor = HelmExecutor(namespace="custom", timeout=300)
        
        assert executor.namespace == "custom"
        assert executor.timeout == 300
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test running a successful command."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["test"],
            returncode=0,
            stdout="success",
            stderr=""
        )
        
        executor = HelmExecutor()
        result = executor._run_command(["test", "command"])
        
        assert result.returncode == 0
        assert result.stdout == "success"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test running a failed command."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["test"],
            output="",
            stderr="error"
        )
        
        executor = HelmExecutor()
        
        with pytest.raises(subprocess.CalledProcessError):
            executor._run_command(["test", "command"])
    
    @patch('subprocess.run')
    def test_run_command_timeout(self, mock_run):
        """Test command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["test"],
            timeout=10
        )
        
        executor = HelmExecutor()
        
        with pytest.raises(subprocess.TimeoutExpired):
            executor._run_command(["test", "command"], timeout=10)
    
    @patch.object(HelmExecutor, '_run_command')
    @patch.object(HelmExecutor, 'get_release_status')
    @patch.object(HelmExecutor, '_get_pod_status')
    def test_apply_chart_success(self, mock_pod_status, mock_get_status, mock_run):
        """Test successful chart application."""
        # Mock successful helm upgrade
        mock_run.return_value = subprocess.CompletedProcess(
            args=["helm"],
            returncode=0,
            stdout="Release deployed",
            stderr=""
        )
        
        # Mock release status
        mock_get_status.return_value = ReleaseStatus(
            name="test-release",
            namespace="openstack",
            revision=1,
            status="deployed",
            chart="test-chart",
            app_version="1.0.0",
            updated="2025-01-01"
        )
        
        # Mock pod status
        mock_pod_status.return_value = {"test-pod": "Running"}
        
        executor = HelmExecutor()
        result = executor.apply_chart(
            release_name="test-release",
            chart_path="/path/to/chart"
        )
        
        assert result.success is True
        assert result.release_name == "test-release"
        assert result.revision == 1
        assert len(result.errors) == 0
    
    @patch.object(HelmExecutor, '_run_command')
    def test_apply_chart_failure(self, mock_run):
        """Test failed chart application."""
        # Mock failed helm upgrade
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["helm"],
            output="",
            stderr="Deployment failed"
        )
        
        executor = HelmExecutor()
        result = executor.apply_chart(
            release_name="test-release",
            chart_path="/path/to/chart"
        )
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "failed" in result.errors[0].lower()
    
    @patch.object(HelmExecutor, '_run_command')
    def test_apply_chart_timeout(self, mock_run):
        """Test chart application timeout."""
        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["helm"],
            timeout=600
        )
        
        executor = HelmExecutor()
        result = executor.apply_chart(
            release_name="test-release",
            chart_path="/path/to/chart",
            timeout=10
        )
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "timed out" in result.errors[0].lower()
    
    @patch.object(HelmExecutor, '_run_command')
    def test_apply_chart_with_overrides(self, mock_run):
        """Test chart application with override files."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["helm"],
            returncode=0,
            stdout="",
            stderr=""
        )
        
        executor = HelmExecutor()
        
        with patch.object(executor, 'get_release_status') as mock_status:
            with patch.object(executor, '_get_pod_status') as mock_pods:
                mock_status.return_value = ReleaseStatus(
                    name="test", namespace="openstack", revision=1,
                    status="deployed", chart="test", app_version="1.0",
                    updated="2025-01-01"
                )
                mock_pods.return_value = {}
                
                result = executor.apply_chart(
                    release_name="test-release",
                    chart_path="/path/to/chart",
                    overrides=["/path/to/override1.yaml", "/path/to/override2.yaml"]
                )
        
        # Verify overrides were included in command
        call_args = mock_run.call_args[0][0]
        assert "--values" in call_args
        assert "/path/to/override1.yaml" in call_args
        assert "/path/to/override2.yaml" in call_args
    
    @patch.object(HelmExecutor, '_run_command')
    def test_get_release_status_success(self, mock_run):
        """Test getting release status successfully."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["helm"],
            returncode=0,
            stdout='{"name":"test","namespace":"openstack","version":1,"info":{"status":"deployed","last_deployed":"2025-01-01"},"chart":{"metadata":{"name":"test-chart","appVersion":"1.0.0"}}}',
            stderr=""
        )
        
        executor = HelmExecutor()
        status = executor.get_release_status("test-release")
        
        assert status.name == "test"
        assert status.namespace == "openstack"
        assert status.revision == 1
        assert status.status == "deployed"
    
    @patch.object(HelmExecutor, '_run_command')
    def test_get_release_status_not_found(self, mock_run):
        """Test getting status for non-existent release."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["helm"],
            output="",
            stderr="Error: release: not found"
        )
        
        executor = HelmExecutor()
        
        with pytest.raises(ValueError, match="not found"):
            executor.get_release_status("nonexistent")
    
    @patch.object(HelmExecutor, '_run_command')
    def test_rollback_release_success(self, mock_run):
        """Test successful release rollback."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["helm"],
            returncode=0,
            stdout="Rollback successful",
            stderr=""
        )
        
        executor = HelmExecutor()
        result = executor.rollback_release("test-release")
        
        assert result is True
    
    @patch.object(HelmExecutor, '_run_command')
    def test_rollback_release_failure(self, mock_run):
        """Test failed release rollback."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["helm"],
            output="",
            stderr="Rollback failed"
        )
        
        executor = HelmExecutor()
        result = executor.rollback_release("test-release")
        
        assert result is False
    
    @patch.object(HelmExecutor, '_run_command')
    def test_rollback_release_with_revision(self, mock_run):
        """Test rollback to specific revision."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["helm"],
            returncode=0,
            stdout="",
            stderr=""
        )
        
        executor = HelmExecutor()
        executor.rollback_release("test-release", revision=5)
        
        # Verify revision was included in command
        call_args = mock_run.call_args[0][0]
        assert "5" in call_args
    
    @patch.object(HelmExecutor, '_run_command')
    def test_get_pod_status_success(self, mock_run):
        """Test getting pod status successfully."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["kubectl"],
            returncode=0,
            stdout='{"items":[{"metadata":{"name":"pod1"},"status":{"phase":"Running"}},{"metadata":{"name":"pod2"},"status":{"phase":"Succeeded"}}]}',
            stderr=""
        )
        
        executor = HelmExecutor()
        pod_status = executor._get_pod_status("test-release")
        
        assert pod_status["pod1"] == "Running"
        assert pod_status["pod2"] == "Succeeded"
    
    @patch.object(HelmExecutor, '_run_command')
    def test_get_pod_status_failure(self, mock_run):
        """Test getting pod status when command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["kubectl"],
            output="",
            stderr="Error"
        )
        
        executor = HelmExecutor()
        pod_status = executor._get_pod_status("test-release")
        
        # Should return empty dict on failure
        assert pod_status == {}
    
    @patch.object(HelmExecutor, '_run_command')
    def test_delete_jobs_success(self, mock_run):
        """Test successful job deletion."""
        # Mock list jobs response
        list_response = subprocess.CompletedProcess(
            args=["kubectl"],
            returncode=0,
            stdout='{"items":[{"metadata":{"name":"nova-db-sync"}},{"metadata":{"name":"nova-cell-setup"}}]}',
            stderr=""
        )
        
        # Mock delete response
        delete_response = subprocess.CompletedProcess(
            args=["kubectl"],
            returncode=0,
            stdout="jobs deleted",
            stderr=""
        )
        
        mock_run.side_effect = [list_response, delete_response]
        
        executor = HelmExecutor()
        result = executor.delete_jobs("nova")
        
        assert result is True
        assert mock_run.call_count == 2
    
    @patch.object(HelmExecutor, '_run_command')
    def test_delete_jobs_no_jobs(self, mock_run):
        """Test job deletion when no jobs exist."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["kubectl"],
            returncode=0,
            stdout='{"items":[]}',
            stderr=""
        )
        
        executor = HelmExecutor()
        result = executor.delete_jobs("nova")
        
        assert result is True
        # Should only call list, not delete
        assert mock_run.call_count == 1
    
    @patch.object(HelmExecutor, '_run_command')
    def test_delete_jobs_failure(self, mock_run):
        """Test job deletion failure."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["kubectl"],
            output="",
            stderr="Error"
        )
        
        executor = HelmExecutor()
        result = executor.delete_jobs("nova")
        
        assert result is False
    
    @patch.object(HelmExecutor, 'get_release_status')
    @patch.object(HelmExecutor, '_get_pod_status')
    @patch('time.sleep')
    def test_wait_for_ready_success(self, mock_sleep, mock_pod_status, mock_get_status):
        """Test waiting for release to be ready."""
        mock_get_status.return_value = ReleaseStatus(
            name="test",
            namespace="openstack",
            revision=1,
            status="deployed",
            chart="test",
            app_version="1.0",
            updated="2025-01-01"
        )
        mock_pod_status.return_value = {"pod1": "Running"}
        
        executor = HelmExecutor()
        result = executor.wait_for_ready("test-release", timeout=60)
        
        assert result is True
    
    @patch.object(HelmExecutor, 'get_release_status')
    @patch('time.sleep')
    def test_wait_for_ready_failed_status(self, mock_sleep, mock_get_status):
        """Test waiting when release status is failed."""
        mock_get_status.return_value = ReleaseStatus(
            name="test",
            namespace="openstack",
            revision=1,
            status="failed",
            chart="test",
            app_version="1.0",
            updated="2025-01-01"
        )
        
        executor = HelmExecutor()
        result = executor.wait_for_ready("test-release", timeout=60)
        
        assert result is False
    
    @patch.object(HelmExecutor, 'get_release_status')
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_ready_timeout(self, mock_time, mock_sleep, mock_get_status):
        """Test waiting timeout."""
        # Simulate time passing
        mock_time.side_effect = [0, 100, 200, 300, 400, 500, 700]
        
        mock_get_status.return_value = ReleaseStatus(
            name="test",
            namespace="openstack",
            revision=1,
            status="pending-upgrade",
            chart="test",
            app_version="1.0",
            updated="2025-01-01"
        )
        
        executor = HelmExecutor()
        result = executor.wait_for_ready("test-release", timeout=600)
        
        assert result is False
