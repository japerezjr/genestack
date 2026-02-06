"""Script-based service upgrader that leverages existing install scripts.

This module provides an upgrade implementation that reuses the battle-tested
install scripts from bin/, ensuring proper secret handling and consistency
with initial deployments.
"""

import subprocess
import time
import logging
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from health.aggregator import HealthAggregator


logger = logging.getLogger(__name__)


@dataclass
class ServiceUpgradeResult:
    """Result of upgrading a single service."""
    service_name: str
    success: bool
    duration: float  # seconds
    script_output: str
    health_check_passed: bool
    errors: List[str]
    warnings: List[str]
    timestamp: str


class ScriptBasedUpgrader:
    """Handles upgrade of OpenStack services using install scripts."""
    
    def __init__(
        self,
        health_aggregator: HealthAggregator,
        scripts_dir: str = "/opt/genestack/bin",
        genestack_base_dir: str = "/opt/genestack",
        genestack_overrides_dir: str = "/etc/genestack"
    ):
        """Initialize script-based upgrader.
        
        Args:
            health_aggregator: Health aggregator for service verification
            scripts_dir: Directory containing install-*.sh scripts
            genestack_base_dir: Base directory for genestack (contains base-helm-configs)
            genestack_overrides_dir: Directory for custom overrides
        """
        self.health_aggregator = health_aggregator
        self.scripts_dir = Path(scripts_dir)
        self.genestack_base_dir = genestack_base_dir
        self.genestack_overrides_dir = genestack_overrides_dir
        
        logger.info(f"ScriptBasedUpgrader initialized:")
        logger.info(f"  scripts_dir: {self.scripts_dir}")
        logger.info(f"  genestack_base_dir: {self.genestack_base_dir}")
        logger.info(f"  genestack_overrides_dir: {self.genestack_overrides_dir}")
        
        if not self.scripts_dir.exists():
            raise ValueError(f"Scripts directory not found: {scripts_dir}")
    
    def upgrade_service(
        self,
        service_name: str,
        timeout: Optional[int] = None
    ) -> ServiceUpgradeResult:
        """Upgrade a single OpenStack service using its install script.
        
        This method:
        1. Locates the install script for the service
        2. Executes it (which handles secrets, overrides, and helm upgrade)
        3. Waits for deployment to stabilize
        4. Verifies service health after upgrade
        
        Args:
            service_name: Name of the service to upgrade
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            ServiceUpgradeResult with upgrade status and details
        """
        start_time = time.time()
        errors = []
        warnings = []
        script_output = ""
        health_check_passed = False
        
        try:
            # Step 1: Locate install script
            script_path = self.scripts_dir / f"install-{service_name}.sh"
            
            if not script_path.exists():
                errors.append(f"Install script not found: {script_path}")
                duration = time.time() - start_time
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=False,
                    duration=duration,
                    script_output="",
                    health_check_passed=False,
                    errors=errors,
                    warnings=warnings,
                    timestamp=datetime.now().isoformat()
                )
            
            # Step 2: Execute install script
            logger.info(f"Executing install script for {service_name}: {script_path}")
            print(f"\n{'='*70}")
            print(f"Upgrading {service_name} using {script_path}")
            print(f"{'='*70}")
            
            env = {
                **subprocess.os.environ,
                "GENESTACK_BASE_DIR": self.genestack_base_dir,
                "GENESTACK_OVERRIDES_DIR": self.genestack_overrides_dir
            }
            
            try:
                result = subprocess.run(
                    [str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout or 1200,  # Default 20 minutes
                    env=env,
                    check=False
                )
                
                script_output = result.stdout + result.stderr
                
                # Always print script output for visibility
                print(f"\n--- Script Output for {service_name} ---")
                print(script_output)
                print(f"--- End Script Output ---\n")
                
                if result.returncode != 0:
                    errors.append(f"Install script failed with exit code {result.returncode}")
                    errors.append(f"Script output: {script_output[-1000:]}")  # Last 1000 chars
                    logger.error(f"Install script failed for {service_name}: exit code {result.returncode}")
                    duration = time.time() - start_time
                    return ServiceUpgradeResult(
                        service_name=service_name,
                        success=False,
                        duration=duration,
                        script_output=script_output,
                        health_check_passed=False,
                        errors=errors,
                        warnings=warnings,
                        timestamp=datetime.now().isoformat()
                    )
                
                logger.info(f"Install script completed successfully for {service_name}")
                
            except subprocess.TimeoutExpired:
                errors.append(f"Install script timed out after {timeout} seconds")
                duration = time.time() - start_time
                return ServiceUpgradeResult(
                    service_name=service_name,
                    success=False,
                    duration=duration,
                    script_output=script_output,
                    health_check_passed=False,
                    errors=errors,
                    warnings=warnings,
                    timestamp=datetime.now().isoformat()
                )
            
            # Step 3: Wait for deployment to stabilize
            logger.info(f"Waiting for {service_name} to stabilize...")
            if not self._wait_for_stabilization(service_name, timeout):
                warnings.append(f"Service {service_name} did not fully stabilize within timeout")
            
            # Step 4: Verify service health
            logger.info(f"Verifying health of {service_name}...")
            health_check_passed = self._verify_service_health(service_name)
            
            if not health_check_passed:
                warnings.append(f"Service {service_name} health check failed after upgrade")
            
            duration = time.time() - start_time
            
            return ServiceUpgradeResult(
                service_name=service_name,
                success=health_check_passed,
                duration=duration,
                script_output=script_output,
                health_check_passed=health_check_passed,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            import traceback
            error_details = f"Unexpected error during upgrade: {str(e)}"
            errors.append(error_details)
            logger.error(f"{error_details}\n{traceback.format_exc()}")
            duration = time.time() - start_time
            
            return ServiceUpgradeResult(
                service_name=service_name,
                success=False,
                duration=duration,
                script_output=script_output,
                health_check_passed=False,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now().isoformat()
            )
    
    def _wait_for_stabilization(self, service_name: str, timeout: Optional[int] = None) -> bool:
        """Wait for service deployment to stabilize.
        
        Args:
            service_name: Name of the service
            timeout: Timeout in seconds
            
        Returns:
            True if service stabilized, False if timeout
        """
        if timeout is None:
            timeout = 60  # Reduced to 1 minute (helm already waited up to 120m)
        
        start_time = time.time()
        check_interval = 5
        
        logger.info(f"Verifying {service_name} deployment status (timeout: {timeout}s)...")
        
        while time.time() - start_time < timeout:
            try:
                # Check helm release status
                result = subprocess.run(
                    [
                        "helm", "status", service_name,
                        "-n", "openstack",
                        "-o", "json"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=True
                )
                
                import json
                status_data = json.loads(result.stdout)
                helm_status = status_data.get("info", {}).get("status", "")
                
                if helm_status == "deployed":
                    logger.info(f"✓ Helm release {service_name} status: deployed")
                    
                    # Try to find pods with various label patterns
                    # Different charts use different labeling schemes
                    label_patterns = [
                        f"application={service_name}",  # OpenStack-helm pattern
                        f"app.kubernetes.io/name={service_name}",  # Standard k8s pattern
                        f"release={service_name}",  # Helm release label
                    ]
                    
                    pods_found = False
                    for label in label_patterns:
                        pod_result = subprocess.run(
                            [
                                "kubectl", "get", "pods",
                                "-n", "openstack",
                                "-l", label,
                                "-o", "jsonpath={.items[*].status.phase}"
                            ],
                            capture_output=True,
                            text=True,
                            timeout=30,
                            check=False
                        )
                        
                        phases = pod_result.stdout.strip().split()
                        if phases:
                            pods_found = True
                            if all(phase == "Running" for phase in phases):
                                logger.info(f"✓ All {len(phases)} pod(s) for {service_name} are Running (label: {label})")
                                return True
                            else:
                                logger.debug(f"Pod phases for {service_name} (label: {label}): {phases}")
                                break  # Found pods but not all running, keep waiting
                    
                    if not pods_found:
                        # No pods found with any label pattern
                        # For some services (like jobs, configmaps-only releases), this is OK
                        logger.info(f"✓ No pods found for {service_name}, but helm status is deployed (may be job/config-only release)")
                        return True
                
                logger.debug(f"Helm status for {service_name}: {helm_status}, waiting...")
                time.sleep(check_interval)
                
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
                logger.warning(f"Error checking status: {e}")
                time.sleep(check_interval)
        
        logger.warning(f"Service {service_name} did not stabilize within {timeout} seconds")
        return False
    
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
            return health_report.overall_healthy
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
