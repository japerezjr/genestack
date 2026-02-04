"""Tests for OpenStack API endpoint checker."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from health.endpoint_checker import (
    EndpointChecker,
    EndpointStatus,
    EndpointReport
)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for OpenStack credentials."""
    monkeypatch.setenv("OS_AUTH_URL", "http://keystone:5000")
    monkeypatch.setenv("OS_USERNAME", "admin")
    monkeypatch.setenv("OS_PASSWORD", "secret")
    monkeypatch.setenv("OS_PROJECT_NAME", "admin")


@pytest.fixture
def sample_catalog():
    """Sample service catalog."""
    return [
        {
            "name": "keystone",
            "type": "identity",
            "endpoints": [
                {
                    "interface": "public",
                    "url": "http://keystone:5000/v3"
                },
                {
                    "interface": "internal",
                    "url": "http://keystone-internal:5000/v3"
                }
            ]
        },
        {
            "name": "nova",
            "type": "compute",
            "endpoints": [
                {
                    "interface": "public",
                    "url": "http://nova:8774/v2.1"
                }
            ]
        }
    ]


class TestEndpointChecker:
    """Tests for EndpointChecker class."""
    
    def test_init_with_credentials(self):
        """Test initialization with explicit credentials."""
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        
        assert checker.auth_url == "http://keystone:5000"
        assert checker.username == "admin"
        assert checker.password == "secret"
        assert checker.project_name == "admin"
    
    def test_init_with_env_vars(self, mock_env_vars):
        """Test initialization with environment variables."""
        checker = EndpointChecker()
        
        assert checker.auth_url == "http://keystone:5000"
        assert checker.username == "admin"
        assert checker.password == "secret"
        assert checker.project_name == "admin"
    
    @patch('health.endpoint_checker.requests.post')
    def test_authenticate_success(self, mock_post):
        """Test successful authentication."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"X-Subject-Token": "test-token"}
        mock_response.json.return_value = {
            "token": {
                "catalog": [
                    {
                        "name": "keystone",
                        "endpoints": []
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        # Execute
        result = checker.authenticate()
        
        # Verify
        assert result is True
        assert checker.token == "test-token"
        assert checker.catalog is not None
    
    @patch('health.endpoint_checker.requests.post')
    def test_authenticate_failure(self, mock_post):
        """Test authentication failure."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="wrong",
            project_name="admin"
        )
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        # Execute
        result = checker.authenticate()
        
        # Verify
        assert result is False
        assert checker.token is None
    
    def test_authenticate_missing_credentials(self):
        """Test authentication with missing credentials."""
        checker = EndpointChecker()
        
        with pytest.raises(ValueError, match="Missing required credentials"):
            checker.authenticate()
    
    @patch('health.endpoint_checker.requests.post')
    def test_authenticate_connection_error(self, mock_post):
        """Test authentication with connection error."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Execute and verify
        with pytest.raises(RuntimeError, match="Authentication failed"):
            checker.authenticate()
    
    @patch('health.endpoint_checker.requests.get')
    def test_check_endpoint_success(self, mock_get):
        """Test checking a reachable endpoint."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        checker.token = "test-token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Execute
        status = checker.check_endpoint(
            "http://keystone:5000/v3",
            "keystone",
            "public"
        )
        
        # Verify
        assert status.service == "keystone"
        assert status.endpoint_type == "public"
        assert status.url == "http://keystone:5000/v3"
        assert status.reachable is True
        assert status.status_code == 200
        assert status.response_time is not None
        assert status.error is None
    
    @patch('health.endpoint_checker.requests.get')
    def test_check_endpoint_timeout(self, mock_get):
        """Test checking an endpoint that times out."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        
        mock_get.side_effect = requests.exceptions.Timeout()
        
        # Execute
        status = checker.check_endpoint(
            "http://slow-service:8080",
            "slow",
            "public"
        )
        
        # Verify
        assert status.reachable is False
        assert status.error == "Timeout"
    
    @patch('health.endpoint_checker.requests.get')
    def test_check_endpoint_connection_error(self, mock_get):
        """Test checking an unreachable endpoint."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Execute
        status = checker.check_endpoint(
            "http://unreachable:8080",
            "unreachable",
            "public"
        )
        
        # Verify
        assert status.reachable is False
        assert "Connection error" in status.error
    
    @patch('health.endpoint_checker.requests.get')
    def test_check_endpoint_http_error(self, mock_get):
        """Test checking an endpoint that returns an error."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        # Execute
        status = checker.check_endpoint(
            "http://broken:8080",
            "broken",
            "public"
        )
        
        # Verify
        assert status.reachable is False
        assert status.status_code == 500
        assert "HTTP 500" in status.error
    
    @patch('health.endpoint_checker.requests.get')
    def test_check_all_endpoints(self, mock_get, sample_catalog):
        """Test checking all endpoints in catalog."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        checker.token = "test-token"
        checker.catalog = sample_catalog
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Execute
        report = checker.check_all_endpoints()
        
        # Verify
        assert report.total_endpoints == 3  # 2 keystone + 1 nova
        assert report.reachable == 3
        assert report.unreachable == 0
        assert report.healthy is True
    
    @patch('health.endpoint_checker.requests.get')
    def test_check_all_endpoints_with_failures(self, mock_get, sample_catalog):
        """Test checking endpoints with some failures."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        checker.token = "test-token"
        checker.catalog = sample_catalog
        
        # First two succeed, third fails
        mock_response_ok = Mock()
        mock_response_ok.status_code = 200
        
        mock_get.side_effect = [
            mock_response_ok,
            mock_response_ok,
            requests.exceptions.Timeout()
        ]
        
        # Execute
        report = checker.check_all_endpoints()
        
        # Verify
        assert report.total_endpoints == 3
        assert report.reachable == 2
        assert report.unreachable == 1
        assert report.healthy is False
    
    def test_check_all_endpoints_not_authenticated(self):
        """Test checking endpoints without authentication."""
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        
        with pytest.raises(RuntimeError, match="Not authenticated"):
            checker.check_all_endpoints()
    
    @patch('health.endpoint_checker.requests.get')
    def test_check_service_endpoints(self, mock_get, sample_catalog):
        """Test checking endpoints for a specific service."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        checker.token = "test-token"
        checker.catalog = sample_catalog
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Execute
        report = checker.check_service_endpoints("keystone")
        
        # Verify
        assert report.total_endpoints == 2  # public and internal
        assert report.reachable == 2
        assert report.healthy is True
    
    @patch('health.endpoint_checker.requests.get')
    def test_check_endpoints_filter_by_type(self, mock_get, sample_catalog):
        """Test checking only specific endpoint types."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        checker.token = "test-token"
        checker.catalog = sample_catalog
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Execute - only check public endpoints
        report = checker.check_all_endpoints(endpoint_types=["public"])
        
        # Verify
        assert report.total_endpoints == 2  # keystone public + nova public
        assert all(e.endpoint_type == "public" for e in report.endpoints)
    
    @patch('health.endpoint_checker.requests.get')
    def test_get_unreachable_endpoints(self, mock_get, sample_catalog):
        """Test getting unreachable endpoints from report."""
        # Setup
        checker = EndpointChecker(
            auth_url="http://keystone:5000",
            username="admin",
            password="secret",
            project_name="admin"
        )
        checker.token = "test-token"
        checker.catalog = sample_catalog
        
        # First endpoint succeeds, others fail
        mock_response_ok = Mock()
        mock_response_ok.status_code = 200
        
        mock_get.side_effect = [
            mock_response_ok,
            requests.exceptions.Timeout(),
            requests.exceptions.ConnectionError()
        ]
        
        # Execute
        report = checker.check_all_endpoints()
        unreachable = checker.get_unreachable_endpoints(report)
        
        # Verify
        assert len(unreachable) == 2
        assert all(not e.reachable for e in unreachable)
    
    def test_endpoint_report_summary(self):
        """Test EndpointReport summary property."""
        report = EndpointReport(
            total_endpoints=10,
            reachable=8,
            unreachable=2,
            endpoints=[],
            healthy=False
        )
        
        summary = report.summary
        assert "Total: 10" in summary
        assert "Reachable: 8" in summary
        assert "Unreachable: 2" in summary
