"""Helm executor wrapper for managing helm chart deployments.

This module provides a wrapper around helm CLI commands with timeout,
retry logic, and deployment monitoring.
"""

import subprocess
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DeploymentResult:
    """Result of a helm deployment operation."""
    success: bool
    chart_name: str
    release_name: str
    revision: int
    duration: float  # seconds
    pod_status: Dict[str, str]  # pod_name -> status
    errors: List[str]
    warnings: List[str]


@dataclass
class ReleaseStatus:
    """Status of a helm release."""
    name: str
    namespace: str
    revision: int
    status: str  # deployed, failed, pending-install, pending-upgrade, etc.
    chart: str
    app_version: str
    updated: str


class HelmExecutor:
    """Wrapper for helm CLI operations with monitoring and retry logic."""
    
    def __init__(self, namespace: str = "openstack", timeout: int = 600):
        """Initialize Helm executor.
        
        Args:
            namespace: Kubernetes namespace for deployments
            timeout: Default timeout in seconds for helm operations
        """
        self.namespace = namespace
        self.timeout = timeout
    
    def _run_command(self, command: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Run a shell command with timeout.
        
        Args:
            command: Command and arguments as list
            timeout: Timeout in seconds (uses default if None)
            
        Returns:
            CompletedProcess with stdout, stderr, and returncode
            
        Raises:
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If command fails
        """
        if timeout is None:
            timeout = self.timeout
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            # Re-raise with more context
            raise subprocess.CalledProcessError(
                e.returncode,
                e.cmd,
                output=e.stdout,
                stderr=e.stderr
            )
    
    def apply_chart(
        self,
        release_name: str,
        chart_path: str,
        version: Optional[str] = None,
        overrides: List[str] = None,
        timeout: Optional[int] = None,
        wait: bool = True
    ) -> DeploymentResult:
        """Apply a helm chart with overrides.
        
        Args:
            release_name: Name for the helm release
            chart_path: Path to the helm chart or repository reference
            version: Chart version to install (optional)
            overrides: List of paths to values files
            timeout: Timeout in seconds (uses default if None)
            wait: Whether to wait for deployment to complete
            
        Returns:
            DeploymentResult with deployment status and details
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        # Build helm command
        command = [
            "helm", "upgrade", "--install",
            release_name, chart_path,
            "--namespace", self.namespace,
        ]
        
        # Add version if specified
        if version:
            command.extend(["--version", version])
        
        # Add override files
        if overrides:
            for override_file in overrides:
                command.extend(["--values", override_file])
        
        # Add timeout
        if timeout is None:
            timeout = self.timeout
        command.extend(["--timeout", f"{timeout}s"])
        
        # Add wait flag
        if wait:
            command.append("--wait")
        
        try:
            # Execute helm upgrade
            result = self._run_command(command, timeout=timeout + 10)  # Add buffer for helm timeout
            
            # Get release status
            status = self.get_release_status(release_name)
            
            # Get pod status
            pod_status = self._get_pod_status(release_name)
            
            duration = time.time() - start_time
            
            return DeploymentResult(
                success=True,
                chart_name=chart_path,
                release_name=release_name,
                revision=status.revision,
                duration=duration,
                pod_status=pod_status,
                errors=errors,
                warnings=warnings
            )
            
        except subprocess.CalledProcessError as e:
            errors.append(f"Helm command failed: {e.stderr}")
            duration = time.time() - start_time
            
            # Try to get status even if deployment failed
            try:
                status = self.get_release_status(release_name)
                revision = status.revision
            except:
                revision = 0
            
            return DeploymentResult(
                success=False,
                chart_name=chart_path,
                release_name=release_name,
                revision=revision,
                duration=duration,
                pod_status={},
                errors=errors,
                warnings=warnings
            )
        
        except subprocess.TimeoutExpired:
            errors.append(f"Helm deployment timed out after {timeout} seconds")
            duration = time.time() - start_time
            
            return DeploymentResult(
                success=False,
                chart_name=chart_path,
                release_name=release_name,
                revision=0,
                duration=duration,
                pod_status={},
                errors=errors,
                warnings=warnings
            )
    
    def wait_for_ready(self, release_name: str, timeout: int = 600, check_interval: int = 10) -> bool:
        """Wait for a helm release to be ready.
        
        Args:
            release_name: Name of the helm release
            timeout: Maximum time to wait in seconds
            check_interval: Time between checks in seconds
            
        Returns:
            True if release becomes ready, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = self.get_release_status(release_name)
                
                if status.status == "deployed":
                    # Check pod status
                    pod_status = self._get_pod_status(release_name)
                    
                    # All pods should be running or succeeded
                    if all(s in ["Running", "Succeeded"] for s in pod_status.values()):
                        return True
                
                elif status.status == "failed":
                    return False
                
            except Exception:
                # Continue waiting if we can't get status
                pass
            
            time.sleep(check_interval)
        
        return False
    
    def get_release_status(self, release_name: str) -> ReleaseStatus:
        """Get status of a helm release.
        
        Args:
            release_name: Name of the helm release
            
        Returns:
            ReleaseStatus with release details
            
        Raises:
            ValueError: If release not found
            subprocess.CalledProcessError: If helm command fails
        """
        command = [
            "helm", "status", release_name,
            "--namespace", self.namespace,
            "--output", "json"
        ]
        
        try:
            result = self._run_command(command, timeout=30)
            data = json.loads(result.stdout)
            
            # Extract chart info safely (might not exist for failed/pending releases)
            chart_name = ""
            app_version = ""
            if "chart" in data and "metadata" in data["chart"]:
                chart_name = data["chart"]["metadata"].get("name", "")
                app_version = data["chart"]["metadata"].get("appVersion", "")
            
            return ReleaseStatus(
                name=data["name"],
                namespace=data["namespace"],
                revision=data["version"],
                status=data["info"]["status"],
                chart=chart_name,
                app_version=app_version,
                updated=data["info"]["last_deployed"]
            )
            
        except subprocess.CalledProcessError as e:
            if "not found" in e.stderr.lower():
                raise ValueError(f"Release {release_name} not found")
            raise
    
    def rollback_release(self, release_name: str, revision: Optional[int] = None) -> bool:
        """Rollback a helm release to a previous revision.
        
        Args:
            release_name: Name of the helm release
            revision: Revision to rollback to (0 for previous, None for previous)
            
        Returns:
            True if rollback successful, False otherwise
        """
        command = [
            "helm", "rollback", release_name,
            "--namespace", self.namespace,
            "--wait"
        ]
        
        if revision is not None:
            command.append(str(revision))
        
        try:
            self._run_command(command)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def _get_pod_status(self, release_name: str) -> Dict[str, str]:
        """Get status of pods for a helm release.
        
        Args:
            release_name: Name of the helm release
            
        Returns:
            Dictionary mapping pod names to their status
        """
        command = [
            "kubectl", "get", "pods",
            "--namespace", self.namespace,
            "--selector", f"release={release_name}",
            "--output", "json"
        ]
        
        try:
            result = self._run_command(command, timeout=30)
            data = json.loads(result.stdout)
            
            pod_status = {}
            for item in data.get("items", []):
                pod_name = item["metadata"]["name"]
                status = item["status"]["phase"]
                pod_status[pod_name] = status
            
            return pod_status
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            return {}
    
    def delete_jobs(self, service_name: str) -> bool:
        """Delete all jobs for a service (used for Nova cleanup).
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if deletion successful, False otherwise
        """
        # First, get list of jobs
        list_command = [
            "kubectl", "get", "jobs",
            "--namespace", self.namespace,
            "--output", "json"
        ]
        
        try:
            result = self._run_command(list_command, timeout=30)
            data = json.loads(result.stdout)
            
            # Filter jobs by service name
            jobs_to_delete = []
            for item in data.get("items", []):
                job_name = item["metadata"]["name"]
                if service_name in job_name:
                    jobs_to_delete.append(job_name)
            
            # Delete each job
            if jobs_to_delete:
                delete_command = [
                    "kubectl", "delete", "jobs",
                    "--namespace", self.namespace,
                ] + jobs_to_delete
                
                self._run_command(delete_command, timeout=60)
            
            return True
            
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return False
