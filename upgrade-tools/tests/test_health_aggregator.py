"""Tests for service health aggregator."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from health.aggregator import (
    HealthAggregator,
    ServiceHealth,
    HealthReport
)
from health.pod_checker import PodStatusReport, PodStatus
from health.endpoint_checker import EndpointReport, EndpointStatus


@pytest.fixture
def healthy_pod_report():
    """Create a healthy pod status report."""
    return PodStatusReport(
        total_pods=3,
        running=3,
        pending=0,
        failed=0,
        succeeded=0,
        unknown=0,
        pods=[
            PodStatus("pod1", "openstack", "Running", True, 0),
            PodStatus("pod2", "openstack", "Running", True, 0),
            PodStatus("pod3", "openstack", "Running", True, 0),
        ],
        healthy=True
    )


@pytest.fixture
def unhealthy_pod_report():
    """Create an unhealthy pod status report."""
    return PodStatusReport(
        total_pods=3,
        running=1,
        pending=1,
        failed=1,
        succeeded=0,
        unknown=0,
        pods=[
            PodStatus("pod1", "openstack", "Running", True, 0),
            PodStatus("pod2", "openstack", "Pending", False, 0),
            PodStatus("pod3", "openstack", "Failed", False, 0),
        ],
        healthy=False
    )


@pytest.fixture
def healthy_endpoint_report():
    """Create a healthy endpoint report."""
    return EndpointReport(
        total_endpoints=2,
        reachable=2,
        unreachable=0,
        endpoints=[
            EndpointStatus("keystone", "public", "http://keystone:5000", True, 200, 0.1),
            EndpointStatus("nova", "public", "http://nova:8774", True, 200, 0.2),
        ],
        healthy=True
    )


@pytest.fixture
def unhealthy_endpoint_report():
    """Create an unhealthy endpoint report."""
    return EndpointReport(
        total_endpoints=2,
        reachable=1,
        unreachable=1,
        endpoints=[
            EndpointStatus("keystone", "public", "http://keystone:5000", True, 200, 0.1),
            EndpointStatus("nova", "public", "http://nova:8774", False, None, None, "Timeout"),
        ],
        healthy=False
    )


class TestServiceHealth:
    """Tests for ServiceHealth class."""
    
    def test_healthy_service_with_pods_only(self, healthy_pod_report):
        """Test service health with only pod status."""
        service = ServiceHealth(
            service_name="test-service",
            pod_status=healthy_pod_report
        )
        
        assert service.healthy is True
        assert len(service.issues) == 0
    
    def test_unhealthy_service_with_pods(self, unhealthy_pod_report):
        """Test service health with unhealthy pods."""
        service = ServiceHealth(
            service_name="test-service",
            pod_status=unhealthy_pod_report
        )
        
        assert service.healthy is False
        assert len(service.issues) > 0
        assert "Unhealthy pods" in service.issues[0]
    
    def test_healthy_service_with_endpoints_only(self, healthy_endpoint_report):
        """Test service health with only endpoint status."""
        service = ServiceHealth(
            service_name="test-service",
            endpoint_status=healthy_endpoint_report
        )
        
        assert service.healthy is True
        assert len(service.issues) == 0
    
    def test_unhealthy_service_with_endpoints(self, unhealthy_endpoint_report):
        """Test service health with unhealthy endpoints."""
        service = ServiceHealth(
            service_name="test-service",
            endpoint_status=unhealthy_endpoint_report
        )
        
        assert service.healthy is False
        assert len(service.issues) > 0
        assert "Unreachable endpoints" in service.issues[0]
    
    def test_healthy_service_with_both(self, healthy_pod_report, healthy_endpoint_report):
        """Test service health with both pod and endpoint status."""
        service = ServiceHealth(
            service_name="test-service",
            pod_status=healthy_pod_report,
            endpoint_status=healthy_endpoint_report
        )
        
        assert service.healthy is True
        assert len(service.issues) == 0
    
    def test_unhealthy_service_with_both(self, unhealthy_pod_report, unhealthy_endpoint_report):
        """Test service health with both unhealthy."""
        service = ServiceHealth(
            service_name="test-service",
            pod_status=unhealthy_pod_report,
            endpoint_status=unhealthy_endpoint_report
        )
        
        assert service.healthy is False
        assert len(service.issues) == 2


class TestHealthReport:
    """Tests for HealthReport class."""
    
    def test_healthy_report(self, healthy_pod_report):
        """Test health report with all services healthy."""
        services = {
            "service1": ServiceHealth("service1", pod_status=healthy_pod_report),
            "service2": ServiceHealth("service2", pod_status=healthy_pod_report),
        }
        
        report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services=services
        )
        
        assert report.overall_healthy is True
        assert "HEALTHY" in report.summary
        assert len(report.get_unhealthy_services()) == 0
    
    def test_unhealthy_report(self, healthy_pod_report, unhealthy_pod_report):
        """Test health report with some services unhealthy."""
        services = {
            "service1": ServiceHealth("service1", pod_status=healthy_pod_report),
            "service2": ServiceHealth("service2", pod_status=unhealthy_pod_report),
        }
        
        report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=False,
            services=services
        )
        
        assert report.overall_healthy is False
        assert "UNHEALTHY" in report.summary
        assert len(report.get_unhealthy_services()) == 1
        assert "service2" in report.get_unhealthy_services()
    
    def test_get_service_health(self, healthy_pod_report):
        """Test getting health for a specific service."""
        services = {
            "service1": ServiceHealth("service1", pod_status=healthy_pod_report),
        }
        
        report = HealthReport(
            timestamp=datetime.now(),
            overall_healthy=True,
            services=services
        )
        
        service_health = report.get_service_health("service1")
        assert service_health is not None
        assert service_health.service_name == "service1"
        
        missing_service = report.get_service_health("nonexistent")
        assert missing_service is None


class TestHealthAggregator:
    """Tests for HealthAggregator class."""
    
    @patch('health.aggregator.PodStatusChecker')
    def test_init_with_default_checkers(self, mock_pod_checker):
        """Test initialization with default checkers."""
        aggregator = HealthAggregator()
        
        assert aggregator.pod_checker is not None
        assert aggregator.endpoint_checker is None
    
    @patch('health.aggregator.PodStatusChecker')
    @patch('health.aggregator.EndpointChecker')
    def test_init_with_custom_checkers(self, mock_endpoint_checker, mock_pod_checker):
        """Test initialization with custom checkers."""
        pod_checker = Mock()
        endpoint_checker = Mock()
        
        aggregator = HealthAggregator(
            pod_checker=pod_checker,
            endpoint_checker=endpoint_checker
        )
        
        assert aggregator.pod_checker == pod_checker
        assert aggregator.endpoint_checker == endpoint_checker
    
    def test_check_service_health_pods_only(self, healthy_pod_report):
        """Test checking service health with pods only."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        aggregator = HealthAggregator(pod_checker=mock_pod_checker)
        
        service_health = aggregator.check_service_health(
            "test-service",
            check_endpoints=False
        )
        
        assert service_health.service_name == "test-service"
        assert service_health.pod_status is not None
        assert service_health.endpoint_status is None
        assert service_health.healthy is True
    
    def test_check_service_health_with_endpoints(
        self,
        healthy_pod_report,
        healthy_endpoint_report
    ):
        """Test checking service health with endpoints."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        mock_endpoint_checker = Mock()
        mock_endpoint_checker.catalog = {"test": "catalog"}
        mock_endpoint_checker.check_service_endpoints.return_value = healthy_endpoint_report
        
        aggregator = HealthAggregator(
            pod_checker=mock_pod_checker,
            endpoint_checker=mock_endpoint_checker
        )
        
        service_health = aggregator.check_service_health(
            "test-service",
            check_endpoints=True
        )
        
        assert service_health.pod_status is not None
        assert service_health.endpoint_status is not None
        assert service_health.healthy is True
    
    def test_check_all_services(self, healthy_pod_report):
        """Test checking all services."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        aggregator = HealthAggregator(pod_checker=mock_pod_checker)
        
        report = aggregator.check_all_services(
            namespaces=["openstack"],
            check_endpoints=False
        )
        
        assert report.overall_healthy is True
        assert "openstack" in report.services
        assert report.services["openstack"].healthy is True
    
    def test_check_all_services_with_failure(self, unhealthy_pod_report):
        """Test checking all services with failures."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = unhealthy_pod_report
        
        aggregator = HealthAggregator(pod_checker=mock_pod_checker)
        
        report = aggregator.check_all_services(
            namespaces=["openstack"],
            check_endpoints=False
        )
        
        assert report.overall_healthy is False
        assert "openstack" in report.services
        assert report.services["openstack"].healthy is False
    
    def test_check_all_services_with_endpoints(
        self,
        healthy_pod_report,
        healthy_endpoint_report
    ):
        """Test checking all services with endpoint checks."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        mock_endpoint_checker = Mock()
        mock_endpoint_checker.catalog = None
        mock_endpoint_checker.authenticate.return_value = True
        mock_endpoint_checker.check_all_endpoints.return_value = healthy_endpoint_report
        
        aggregator = HealthAggregator(
            pod_checker=mock_pod_checker,
            endpoint_checker=mock_endpoint_checker
        )
        
        report = aggregator.check_all_services(
            namespaces=["openstack"],
            check_endpoints=True
        )
        
        assert "endpoints" in report.services
        assert report.services["endpoints"].endpoint_status is not None
    
    def test_check_openstack_health(self, healthy_pod_report):
        """Test convenience method for checking OpenStack health."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        aggregator = HealthAggregator(pod_checker=mock_pod_checker)
        
        report = aggregator.check_openstack_health(check_endpoints=False)
        
        assert report.overall_healthy is True
        assert "openstack" in report.services
    
    def test_generate_health_report_text(self, healthy_pod_report):
        """Test generating text format health report."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        aggregator = HealthAggregator(pod_checker=mock_pod_checker)
        
        report_text = aggregator.generate_health_report(
            namespaces=["openstack"],
            check_endpoints=False,
            output_format="text"
        )
        
        assert "OpenStack Health Report" in report_text
        assert "HEALTHY" in report_text
    
    def test_generate_health_report_json(self, healthy_pod_report):
        """Test generating JSON format health report."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        aggregator = HealthAggregator(pod_checker=mock_pod_checker)
        
        report_json = aggregator.generate_health_report(
            namespaces=["openstack"],
            check_endpoints=False,
            output_format="json"
        )
        
        import json
        data = json.loads(report_json)
        
        assert "timestamp" in data
        assert "overall_healthy" in data
        assert data["overall_healthy"] is True
    
    def test_generate_health_report_markdown(self, healthy_pod_report):
        """Test generating Markdown format health report."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        aggregator = HealthAggregator(pod_checker=mock_pod_checker)
        
        report_md = aggregator.generate_health_report(
            namespaces=["openstack"],
            check_endpoints=False,
            output_format="markdown"
        )
        
        assert "# OpenStack Health Report" in report_md
        assert "✅ HEALTHY" in report_md
    
    def test_generate_health_report_invalid_format(self, healthy_pod_report):
        """Test generating health report with invalid format."""
        mock_pod_checker = Mock()
        mock_pod_checker.check_namespace.return_value = healthy_pod_report
        
        aggregator = HealthAggregator(pod_checker=mock_pod_checker)
        
        with pytest.raises(ValueError, match="Unsupported output format"):
            aggregator.generate_health_report(
                namespaces=["openstack"],
                check_endpoints=False,
                output_format="invalid"
            )
