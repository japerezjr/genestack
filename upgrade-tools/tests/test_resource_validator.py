"""Tests for resource and backup validator."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from health.resource_validator import (
    ResourceValidator,
    ResourceStatus,
    BackupStatus,
    JobStatus,
    ValidationReport
)


def create_mock_node(cpu: str, memory: str, allocatable_cpu: str, allocatable_memory: str):
    """Create a mock Kubernetes node."""
    node = Mock()
    node.status = Mock()
    node.status.capacity = {"cpu": cpu, "memory": memory}
    node.status.allocatable = {"cpu": allocatable_cpu, "memory": allocatable_memory}
    return node


def create_mock_pod(cpu_request: str = "0", memory_request: str = "0"):
    """Create a mock Kubernetes pod."""
    pod = Mock()
    pod.spec = Mock()
    
    container = Mock()
    container.resources = Mock()
    container.resources.requests = {"cpu": cpu_request, "memory": memory_request}
    
    pod.spec.containers = [container]
    return pod


def create_mock_job(name: str, active: int = 0):
    """Create a mock Kubernetes job."""
    job = Mock()
    job.metadata = Mock()
    job.metadata.name = name
    job.status = Mock()
    job.status.active = active
    return job


class TestResourceValidator:
    """Tests for ResourceValidator class."""
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_init_with_kubeconfig(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test initialization with kubeconfig."""
        validator = ResourceValidator(in_cluster=False)
        assert validator.v1 is not None
        assert validator.batch_v1 is not None
        mock_load_config.assert_called_once()
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_check_cluster_resources_sufficient(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test checking cluster resources with sufficient capacity."""
        validator = ResourceValidator(in_cluster=False)
        
        # Mock nodes with good capacity
        nodes = Mock()
        nodes.items = [
            create_mock_node("4", "8Gi", "4", "8Gi"),
            create_mock_node("4", "8Gi", "4", "8Gi"),
        ]
        validator.v1.list_node.return_value = nodes
        
        # Mock pods with low usage
        pods = Mock()
        pods.items = [
            create_mock_pod("500m", "1Gi"),
            create_mock_pod("500m", "1Gi"),
        ]
        validator.v1.list_pod_for_all_namespaces.return_value = pods
        
        # Execute
        status = validator.check_cluster_resources()
        
        # Verify
        assert status.total_cpu == 8.0
        assert status.used_cpu == 1.0
        assert status.cpu_utilization < 80.0
        assert status.sufficient is True
        assert len(status.issues) == 0
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_check_cluster_resources_insufficient(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test checking cluster resources with insufficient capacity."""
        validator = ResourceValidator(in_cluster=False, cpu_threshold=50.0)
        
        # Mock nodes
        nodes = Mock()
        nodes.items = [
            create_mock_node("4", "8Gi", "4", "8Gi"),
        ]
        validator.v1.list_node.return_value = nodes
        
        # Mock pods with high usage
        pods = Mock()
        pods.items = [
            create_mock_pod("3", "6Gi"),  # 75% CPU, 75% memory
        ]
        validator.v1.list_pod_for_all_namespaces.return_value = pods
        
        # Execute
        status = validator.check_cluster_resources()
        
        # Verify
        assert status.cpu_utilization > 50.0
        assert status.sufficient is False
        assert len(status.issues) > 0
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_check_backups_valid(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test checking backups with valid recent backup."""
        validator = ResourceValidator(in_cluster=False)
        
        # Create temporary backup directory with a recent backup
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_file = Path(tmpdir) / "backup.sql"
            backup_file.write_text("test backup")
            
            # Execute
            status = validator.check_backups(tmpdir)
            
            # Verify
            assert status.backup_valid is True
            assert status.latest_backup is not None
            assert len(status.backups_found) == 1
            assert len(status.issues) == 0
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_check_backups_old(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test checking backups with old backup."""
        validator = ResourceValidator(in_cluster=False, backup_max_age_hours=1)
        
        # Create temporary backup directory with an old backup
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_file = Path(tmpdir) / "backup.sql"
            backup_file.write_text("test backup")
            
            # Set file modification time to 2 hours ago
            old_time = (datetime.now() - timedelta(hours=2)).timestamp()
            os.utime(backup_file, (old_time, old_time))
            
            # Execute
            status = validator.check_backups(tmpdir)
            
            # Verify
            assert status.backup_valid is False
            assert status.latest_backup is not None
            assert len(status.issues) > 0
            assert "too old" in status.issues[0]
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_check_backups_missing(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test checking backups with no backups found."""
        validator = ResourceValidator(in_cluster=False)
        
        # Create empty temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Execute
            status = validator.check_backups(tmpdir)
            
            # Verify
            assert status.backup_valid is False
            assert status.latest_backup is None
            assert len(status.backups_found) == 0
            assert len(status.issues) > 0
            assert "No backup files found" in status.issues[0]
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_check_backups_directory_not_exists(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test checking backups with non-existent directory."""
        validator = ResourceValidator(in_cluster=False)
        
        # Execute
        status = validator.check_backups("/nonexistent/path")
        
        # Verify
        assert status.backup_valid is False
        assert len(status.issues) > 0
        assert "does not exist" in status.issues[0]
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_check_active_jobs_none(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test checking active jobs with no active jobs."""
        validator = ResourceValidator(in_cluster=False)
        
        # Mock no active jobs
        jobs = Mock()
        jobs.items = [
            create_mock_job("completed-job", active=0),
        ]
        validator.batch_v1.list_namespaced_job.return_value = jobs
        
        # Execute
        status = validator.check_active_jobs()
        
        # Verify
        assert status.safe_to_upgrade is True
        assert len(status.active_jobs) == 0
        assert len(status.issues) == 0
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_check_active_jobs_with_active(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test checking active jobs with active jobs."""
        validator = ResourceValidator(in_cluster=False)
        
        # Mock active jobs
        jobs = Mock()
        jobs.items = [
            create_mock_job("active-job", active=1),
            create_mock_job("nova-db-sync", active=1),
        ]
        validator.batch_v1.list_namespaced_job.return_value = jobs
        
        # Execute
        status = validator.check_active_jobs()
        
        # Verify
        assert status.safe_to_upgrade is False
        assert len(status.active_jobs) == 2
        assert len(status.active_migrations) == 1
        assert "nova-db-sync" in status.active_migrations
        assert len(status.issues) > 0
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_validate_all_passed(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test complete validation that passes."""
        validator = ResourceValidator(in_cluster=False)
        
        # Mock sufficient resources
        nodes = Mock()
        nodes.items = [create_mock_node("4", "8Gi", "4", "8Gi")]
        validator.v1.list_node.return_value = nodes
        
        pods = Mock()
        pods.items = [create_mock_pod("500m", "1Gi")]
        validator.v1.list_pod_for_all_namespaces.return_value = pods
        
        # Mock no active jobs
        jobs = Mock()
        jobs.items = []
        validator.batch_v1.list_namespaced_job.return_value = jobs
        
        # Create temporary backup
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_file = Path(tmpdir) / "backup.sql"
            backup_file.write_text("test backup")
            
            # Execute
            report = validator.validate_all(tmpdir)
            
            # Verify
            assert report.passed is True
            assert report.resource_status.sufficient is True
            assert report.backup_status.backup_valid is True
            assert report.job_status.safe_to_upgrade is True
    
    @patch('kubernetes.config.load_kube_config')
    @patch('health.resource_validator.client.CoreV1Api')
    @patch('health.resource_validator.client.BatchV1Api')
    def test_validate_all_failed(self, mock_batch_api, mock_core_api, mock_load_config):
        """Test complete validation that fails."""
        validator = ResourceValidator(in_cluster=False, cpu_threshold=10.0)
        
        # Mock insufficient resources
        nodes = Mock()
        nodes.items = [create_mock_node("4", "8Gi", "4", "8Gi")]
        validator.v1.list_node.return_value = nodes
        
        pods = Mock()
        pods.items = [create_mock_pod("3", "6Gi")]  # High usage
        validator.v1.list_pod_for_all_namespaces.return_value = pods
        
        # Mock active jobs
        jobs = Mock()
        jobs.items = [create_mock_job("active-job", active=1)]
        validator.batch_v1.list_namespaced_job.return_value = jobs
        
        # Execute with non-existent backup path
        report = validator.validate_all("/nonexistent")
        
        # Verify
        assert report.passed is False
        assert report.resource_status.sufficient is False
        assert report.backup_status.backup_valid is False
        assert report.job_status.safe_to_upgrade is False
    
    def test_parse_cpu(self):
        """Test CPU parsing."""
        assert ResourceValidator._parse_cpu("2") == 2.0
        assert ResourceValidator._parse_cpu("500m") == 0.5
        assert ResourceValidator._parse_cpu("1000m") == 1.0
        assert ResourceValidator._parse_cpu("0") == 0.0
    
    def test_parse_memory(self):
        """Test memory parsing."""
        # Test Gi
        assert ResourceValidator._parse_memory("1Gi") == 1.0
        assert ResourceValidator._parse_memory("2Gi") == 2.0
        
        # Test Mi
        assert ResourceValidator._parse_memory("1024Mi") == 1.0
        
        # Test Ki
        assert abs(ResourceValidator._parse_memory("1048576Ki") - 1.0) < 0.01
    
    def test_validation_report_summary(self):
        """Test validation report summary generation."""
        resource_status = ResourceStatus(
            total_cpu=8.0,
            used_cpu=4.0,
            available_cpu=4.0,
            cpu_utilization=50.0,
            total_memory=16.0,
            used_memory=8.0,
            available_memory=8.0,
            memory_utilization=50.0,
            sufficient=True
        )
        
        backup_status = BackupStatus(
            backup_path="/backups",
            backups_found=["backup.sql"],
            latest_backup="backup.sql",
            latest_backup_age=timedelta(hours=1),
            backup_valid=True
        )
        
        job_status = JobStatus(
            safe_to_upgrade=True
        )
        
        report = ValidationReport(
            timestamp=datetime.now(),
            resource_status=resource_status,
            backup_status=backup_status,
            job_status=job_status,
            passed=True
        )
        
        summary = report.summary
        assert "PASSED" in summary
        assert "50.0% used" in summary
