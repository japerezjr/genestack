"""Per-service upgrade logic for OpenStack services.

This module handles the upgrade of individual OpenStack services,
including cleanup, deployment, and health verification.
"""

import time
from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime

from .helm_executor import HelmExecutor, DeploymentResult
from health.aggregator import HealthAggregator


@dataclass
class ServiceUpgradeResult:
    """Result of upgrading a single service."""
    service_name: str
    success: bool
    duration: float  # seconds
    deployment_result: Optional[DeploymentResult]
    health_check_passed: bool
    errors: List[str]
    warnings: List[str]
    timestamp: str


class ServiceUpgrader:
    """Handles upgrade of individual OpenStack services."""
    
    # Services that require job cleanup before upgrade
    SERVICES_REQUIRING_JOB_CLEANUP = ["nova", "neutron", "cinder", "heat"]
    
    def __init__(
        self,
        helm_executor: HelmExecutor,
        health_aggregator: HealthAggregator,
        chart_versions_path: str,
        overrides_base_path: str
    ):
        """Initialize service upgrader.
        
        Args:
            helm_executor: Helm executor for deployments
            health_aggregator: Health aggregator for service verification
            chart_versions_path: Path to helm-chart-versions.yaml
            overrides_base_path: Base path for helm override files
        """
        self.helm_executor = helm_executor
        self.health_aggregator = health_aggregator
        self.chart_versions_path = chart_versions_path
        self.overrides_base_path = overrides_base_path
    
    def upgrade_service(
        self,
        service_name: str,
        chart_path: str,
        timeout: Optional[int] = None
    ) -> ServiceUpgradeResult:
        """Upgrade a single OpenStack service.
        
        This method performs the complete upgrade workflow:
        1. Clean up existing jobs (if needed)
        2. Apply helm chart with updated version
        3. Wait for deployment to stabilize
        4. Verify service health after upgrade
        
        Args:
            service_name: Name of the service to upgrade
            chart_path: Path to the helm chart
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            ServiceUpgradeResult with upgrade status and details
        """
        start_time = time.time()
        errors = []
        warnings = []
        deployment_result = None
        health_check_passed = False
        
        try:
            # Step 1: Clean up existing jobs if needed
            if service_name in self.SERVICES_REQUIRING_JOB_CLEANUP:
                if not self._cleanup_jobs(service_name):
                    warnings.append(f"Failed to clean up jobs for {service_name}, continuing anyway")
            
            # Step 2: Apply helm chart with updated version
            override_files = self._get_override_files(service_name)
            
            deployment_result = self.helm_executor.apply_chart(
                release_name=service_name,
                chart_path=chart_path,
                overrides=override_files,
                timeout=timeout,
                wait=True
            )
            
            if not deployment_result.success:
                errors.extend(deployment_result.errors)
                duration = time.time() - start_time
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=False,
                    duration=duration,
                    deployment_result=deployment_result,
                    health_check_passed=False,
                    errors=errors,
                    warnings=warnings,
                    timestamp=datetime.now().isoformat()
                )
            
            # Step 3: Wait for deployment to stabilize
            if not self._wait_for_stabilization(service_name, timeout):
                errors.append(f"Service {service_name} did not stabilize within timeout")
                duration = time.time() - start_time
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=False,
                    duration=duration,
                    deployment_result=deployment_result,
                    health_check_passed=False,
                    errors=errors,
                    warnings=warnings,
                    timestamp=datetime.now().isoformat()
                )
            
            # Step 4: Verify service health after upgrade
            health_check_passed = self._verify_service_health(service_name)
            
            if not health_check_passed:
                errors.append(f"Service {service_name} health check failed after upgrade")
            
            duration = time.time() - start_time
            
            return ServiceUpgradeResult(
                service_name=service_name,
                success=health_check_passed,
                duration=duration,
                deployment_result=deployment_result,
                health_check_passed=health_check_passed,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            errors.append(f"Unexpected error during upgrade: {str(e)}")
            duration = time.time() - start_time
            
            return ServiceUpgradeResult(
                service_name=service_name,
                success=False,
                duration=duration,
                deployment_result=deployment_result,
                health_check_passed=False,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now().isoformat()
            )
    
    def _cleanup_jobs(self, service_name: str) -> bool:
        """Clean up existing jobs for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if cleanup successful, False otherwise
        """
        return self.helm_executor.delete_jobs(service_name)
    
    def _get_override_files(self, service_name: str) -> List[str]:
        """Get list of override files for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of paths to override files
        """
        # Standard override file location
        override_file = f"{self.overrides_base_path}/{service_name}/{service_name}-helm-overrides.yaml"
        
        # Could be extended to support multiple override files
        return [override_file]
    
    def _wait_for_stabilization(self, service_name: str, timeout: Optional[int] = None) -> bool:
        """Wait for service deployment to stabilize.
        
        Args:
            service_name: Name of the service
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            True if service stabilized, False if timeout
        """
        if timeout is None:
            timeout = 600  # Default 10 minutes
        
        return self.helm_executor.wait_for_ready(
            release_name=service_name,
            timeout=timeout,
            check_interval=10
        )
    
    def _verify_service_health(self, service_name: str) -> bool:
        """Verify service health after upgrade.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Get overall health status
            health_report = self.health_aggregator.check_openstack_health()
            
            # Check if service is in the healthy services list
            # This is a simplified check - could be more sophisticated
            return health_report.overall_healthy
            
        except Exception:
            return False
    
    def rollback_service(self, service_name: str, revision: Optional[int] = None) -> bool:
        """Rollback a service to a previous revision.
        
        Args:
            service_name: Name of the service
            revision: Revision to rollback to (None for previous)
            
        Returns:
            True if rollback successful, False otherwise
        """
        success = self.helm_executor.rollback_release(service_name, revision)
        
        if success:
            # Wait for rollback to stabilize
            success = self._wait_for_stabilization(service_name)
        
        return success
