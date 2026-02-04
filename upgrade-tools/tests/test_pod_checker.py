"""Tests for Kubernetes pod status checker."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from kubernetes import client
from kubernetes.client.rest import ApiException

from health.pod_checker import (
    PodStatusChecker,
    PodStatus,
    PodStatusReport
)


@pytest.fixture
def mock_k8s_config():
    """Mock Kubernetes configuration."""
    with patch('health.pod_checker.config') as mock_config:
        yield mock_config


@pytest.fixture
def mock_v1_api():
    """Mock Kubernetes CoreV1Api."""
    with patch('health.pod_checker.client.CoreV1Api') as mock_api:
        yield mock_api


def create_mock_pod(
    name: str,
    namespace: str,
    phase: str,
    ready: bool = True,
    restarts: int = 0
) -> client.V1Pod:
    """Create a mock V1Pod object."""
    pod = Mock(spec=client.V1Pod)
    
    # Metadata
    pod.metadata = Mock()
    pod.metadata.name = name
    pod.metadata.namespace = namespace
    
    # Spec
    pod.spec = Mock()
    pod.spec.node_name = "test-node"
    
    # Status
    pod.status = Mock()
    pod.status.phase = phase
    
    # Container statuses
    container_status = Mock()
    container_status.ready = ready
    container_status.restart_count = restarts
    pod.status.container_statuses = [container_status]
    
    # Conditions
    pod.status.conditions = []
    if phase != "Running":
        condition = Mock()
        condition.status = "False"
        condition.reason = f"{phase}Reason"
        condition.message = f"Pod is {phase}"
        pod.status.conditions = [condition]
    
    return pod


class TestPodStatusChecker:
    """Tests for PodStatusChecker class."""
    
    def test_init_with_kubeconfig(self, mock_k8s_config, mock_v1_api):
        """Test initialization with kubeconfig."""
        checker = PodStatusChecker(in_cluster=False)
        
        mock_k8s_config.load_kube_config.assert_called_once()
        mock_v1_api.assert_called_once()
    
    def test_init_with_incluster_config(self, mock_k8s_config, mock_v1_api):
        """Test initialization with in-cluster config."""
        checker = PodStatusChecker(in_cluster=True)
        
        mock_k8s_config.load_incluster_config.assert_called_once()
        mock_v1_api.assert_called_once()
    
    def test_init_failure(self, mock_k8s_config):
        """Test initialization failure."""
        mock_k8s_config.load_kube_config.side_effect = Exception("Config error")
        
        with pytest.raises(RuntimeError, match="Failed to initialize Kubernetes client"):
            PodStatusChecker(in_cluster=False)
    
    def test_check_namespace_all_running(self, mock_k8s_config, mock_v1_api):
        """Test checking namespace with all pods running."""
        # Setup
        checker = PodStatusChecker(in_cluster=False)
        mock_api_instance = mock_v1_api.return_value
        
        # Create mock pods
        pods = [
            create_mock_pod("pod1", "openstack", "Running"),
            create_mock_pod("pod2", "openstack", "Running"),
            create_mock_pod("pod3", "openstack", "Running"),
        ]
        
        mock_response = Mock()
        mock_response.items = pods
        mock_api_instance.list_namespaced_pod.return_value = mock_response
        
        # Execute
        report = checker.check_namespace("openstack")
        
        # Verify
        assert report.total_pods == 3
        assert report.running == 3
        assert report.pending == 0
        assert report.failed == 0
        assert report.healthy is True
        assert len(report.pods) == 3
    
    def test_check_namespace_with_failures(self, mock_k8s_config, mock_v1_api):
        """Test checking namespace with failed pods."""
        # Setup
        checker = PodStatusChecker(in_cluster=False)
        mock_api_instance = mock_v1_api.return_value
        
        # Create mock pods with different states
        pods = [
            create_mock_pod("pod1", "openstack", "Running"),
            create_mock_pod("pod2", "openstack", "Failed"),
            create_mock_pod("pod3", "openstack", "Pending"),
        ]
        
        mock_response = Mock()
        mock_response.items = pods
        mock_api_instance.list_namespaced_pod.return_value = mock_response
        
        # Execute
        report = checker.check_namespace("openstack")
        
        # Verify
        assert report.total_pods == 3
        assert report.running == 1
        assert report.pending == 1
        assert report.failed == 1
        assert report.healthy is False
    
    def test_check_namespace_api_error(self, mock_k8s_config, mock_v1_api):
        """Test handling of API errors."""
        # Setup
        checker = PodStatusChecker(in_cluster=False)
        mock_api_instance = mock_v1_api.return_value
        mock_api_instance.list_namespaced_pod.side_effect = ApiException("API error")
        
        # Execute and verify
        with pytest.raises(RuntimeError, match="Failed to list pods"):
            checker.check_namespace("openstack")
    
    def test_check_all_namespaces(self, mock_k8s_config, mock_v1_api):
        """Test checking all namespaces."""
        # Setup
        checker = PodStatusChecker(in_cluster=False)
        mock_api_instance = mock_v1_api.return_value
        
        pods = [
            create_mock_pod("pod1", "openstack", "Running"),
            create_mock_pod("pod2", "kube-system", "Running"),
        ]
        
        mock_response = Mock()
        mock_response.items = pods
        mock_api_instance.list_pod_for_all_namespaces.return_value = mock_response
        
        # Execute
        report = checker.check_all_namespaces()
        
        # Verify
        assert report.total_pods == 2
        assert report.running == 2
        assert report.healthy is True
    
    def test_check_multiple_namespaces(self, mock_k8s_config, mock_v1_api):
        """Test checking multiple specific namespaces."""
        # Setup
        checker = PodStatusChecker(in_cluster=False)
        mock_api_instance = mock_v1_api.return_value
        
        def mock_list_pods(namespace):
            mock_response = Mock()
            if namespace == "openstack":
                mock_response.items = [
                    create_mock_pod("pod1", "openstack", "Running"),
                ]
            else:
                mock_response.items = [
                    create_mock_pod("pod2", "kube-system", "Running"),
                ]
            return mock_response
        
        mock_api_instance.list_namespaced_pod.side_effect = mock_list_pods
        
        # Execute
        reports = checker.check_namespaces(["openstack", "kube-system"])
        
        # Verify
        assert len(reports) == 2
        assert "openstack" in reports
        assert "kube-system" in reports
        assert reports["openstack"].total_pods == 1
        assert reports["kube-system"].total_pods == 1
    
    def test_get_unhealthy_pods(self, mock_k8s_config, mock_v1_api):
        """Test getting unhealthy pods from a report."""
        # Setup
        checker = PodStatusChecker(in_cluster=False)
        mock_api_instance = mock_v1_api.return_value
        
        pods = [
            create_mock_pod("pod1", "openstack", "Running"),
            create_mock_pod("pod2", "openstack", "Failed"),
            create_mock_pod("pod3", "openstack", "Pending"),
            create_mock_pod("pod4", "openstack", "Running", ready=False),
        ]
        
        mock_response = Mock()
        mock_response.items = pods
        mock_api_instance.list_namespaced_pod.return_value = mock_response
        
        # Execute
        report = checker.check_namespace("openstack")
        unhealthy = checker.get_unhealthy_pods(report)
        
        # Verify
        assert len(unhealthy) == 3
        assert unhealthy[0].name == "pod2"
        assert unhealthy[1].name == "pod3"
        assert unhealthy[2].name == "pod4"
    
    def test_pod_status_report_summary(self):
        """Test PodStatusReport summary property."""
        report = PodStatusReport(
            total_pods=10,
            running=8,
            pending=1,
            failed=1,
            succeeded=0,
            unknown=0,
            pods=[],
            healthy=False
        )
        
        summary = report.summary
        assert "Total: 10" in summary
        assert "Running: 8" in summary
        assert "Pending: 1" in summary
        assert "Failed: 1" in summary
