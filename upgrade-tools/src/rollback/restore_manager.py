"""Restore manager for restoring from backups during rollback.

This module handles restoring helm chart versions, override configurations,
and databases from backups.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .backup_manager import Backup, BackupManager
from executor.helm_executor import HelmExecutor


@dataclass
class RestoreResult:
    """Result of a restore operation."""
    success: bool
    backup_id: str
    timestamp: datetime
    components: List[str]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class RestoreManager:
    """Manages restoration from backups."""
    
    def __init__(
        self,
        backup_manager: Optional[BackupManager] = None,
        helm_executor: Optional[HelmExecutor] = None
    ):
        """Initialize restore manager.
        
        Args:
            backup_manager: BackupManager instance (created if not provided)
            helm_executor: HelmExecutor instance (created if not provided)
        """
        self.backup_manager = backup_manager or BackupManager()
        self.helm_executor = helm_executor or HelmExecutor()
    
    def restore_from_backup(
        self,
        backup: Backup,
        components: List[str],
        chart_versions_path: Optional[str] = None,
        overrides_base_path: Optional[str] = None,
        apply_helm_charts: bool = False,
        restore_databases: bool = False,
        namespace: str = "openstack"
    ) -> RestoreResult:
        """Restore from a backup.
        
        Args:
            backup: Backup object to restore from
            components: List of components to restore (e.g., ["versions", "configs", "databases"])
            chart_versions_path: Destination path for helm-chart-versions.yaml
            overrides_base_path: Destination path for base-helm-configs directory
            apply_helm_charts: Whether to apply previous helm chart versions
            restore_databases: Whether to restore databases
            namespace: Kubernetes namespace
            
        Returns:
            RestoreResult with restore details and status
        """
        timestamp = datetime.now()
        errors = []
        warnings = []
        restored_components = []
        
        # Restore helm chart versions
        if "versions" in components and "versions" in backup.components:
            try:
                if not chart_versions_path:
                    raise ValueError("chart_versions_path required for restoring versions")
                
                self._restore_chart_versions(
                    backup.components["versions"],
                    chart_versions_path
                )
                restored_components.append("versions")
                
                # Apply helm charts if requested
                if apply_helm_charts:
                    try:
                        self._apply_previous_versions(chart_versions_path, namespace)
                        restored_components.append("helm_charts")
                    except Exception as e:
                        warnings.append(f"Failed to apply some helm charts: {e}")
                
            except Exception as e:
                errors.append(f"Failed to restore chart versions: {e}")
        
        # Restore override configurations
        if "configs" in components and "configs" in backup.components:
            try:
                if not overrides_base_path:
                    raise ValueError("overrides_base_path required for restoring configs")
                
                self._restore_override_configs(
                    backup.components["configs"],
                    overrides_base_path
                )
                restored_components.append("configs")
            except Exception as e:
                errors.append(f"Failed to restore override configs: {e}")
        
        # Restore databases
        if "databases" in components and "databases" in backup.components:
            try:
                if restore_databases:
                    self._restore_databases(
                        backup.components["databases"],
                        namespace
                    )
                    restored_components.append("databases")
                else:
                    warnings.append("Database restore requested but restore_databases=False")
            except Exception as e:
                errors.append(f"Failed to restore databases: {e}")
        
        success = len(errors) == 0 and len(restored_components) > 0
        
        return RestoreResult(
            success=success,
            backup_id=backup.backup_id,
            timestamp=timestamp,
            components=restored_components,
            errors=errors,
            warnings=warnings
        )
    
    def restore_latest(
        self,
        components: List[str],
        chart_versions_path: Optional[str] = None,
        overrides_base_path: Optional[str] = None,
        apply_helm_charts: bool = False,
        restore_databases: bool = False,
        namespace: str = "openstack"
    ) -> RestoreResult:
        """Restore from the latest backup.
        
        Args:
            components: List of components to restore
            chart_versions_path: Destination path for helm-chart-versions.yaml
            overrides_base_path: Destination path for base-helm-configs directory
            apply_helm_charts: Whether to apply previous helm chart versions
            restore_databases: Whether to restore databases
            namespace: Kubernetes namespace
            
        Returns:
            RestoreResult with restore details and status
            
        Raises:
            ValueError: If no backups exist
        """
        backup = self.backup_manager.get_latest_backup()
        if not backup:
            raise ValueError("No backups available to restore from")
        
        return self.restore_from_backup(
            backup=backup,
            components=components,
            chart_versions_path=chart_versions_path,
            overrides_base_path=overrides_base_path,
            apply_helm_charts=apply_helm_charts,
            restore_databases=restore_databases,
            namespace=namespace
        )
    
    def _restore_chart_versions(
        self,
        backup_file: Path,
        destination_path: str
    ) -> None:
        """Restore helm-chart-versions.yaml from backup.
        
        Args:
            backup_file: Path to backed up helm-chart-versions.yaml
            destination_path: Destination path for restored file
            
        Raises:
            FileNotFoundError: If backup file doesn't exist
            IOError: If restore fails
        """
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        destination = Path(destination_path)
        
        # Create backup of current file if it exists
        if destination.exists():
            backup_current = destination.parent / f"{destination.name}.pre-restore"
            shutil.copy2(destination, backup_current)
        
        # Restore from backup
        shutil.copy2(backup_file, destination)
    
    def _restore_override_configs(
        self,
        backup_dir: Path,
        destination_path: str
    ) -> None:
        """Restore override configuration files from backup.
        
        Args:
            backup_dir: Path to backed up base-helm-configs directory
            destination_path: Destination path for restored configs
            
        Raises:
            FileNotFoundError: If backup directory doesn't exist
            IOError: If restore fails
        """
        if not backup_dir.exists():
            raise FileNotFoundError(f"Backup directory not found: {backup_dir}")
        
        destination = Path(destination_path)
        
        # Create backup of current directory if it exists
        if destination.exists():
            backup_current = destination.parent / f"{destination.name}.pre-restore"
            if backup_current.exists():
                shutil.rmtree(backup_current)
            shutil.copytree(destination, backup_current)
            
            # Remove current directory
            shutil.rmtree(destination)
        
        # Restore from backup
        shutil.copytree(backup_dir, destination)
    
    def _restore_databases(
        self,
        backup_dir: Path,
        namespace: str
    ) -> None:
        """Restore databases from backup.
        
        Args:
            backup_dir: Path to database backup directory
            namespace: Kubernetes namespace
            
        Raises:
            FileNotFoundError: If backup directory doesn't exist
            RuntimeError: If restore fails
        """
        if not backup_dir.exists():
            raise FileNotFoundError(f"Database backup directory not found: {backup_dir}")
        
        # Find backup files
        backup_files = list(backup_dir.glob("*.sql"))
        if not backup_files:
            raise FileNotFoundError("No database backup files found")
        
        # Get MariaDB pod
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "pods",
                    "--namespace", namespace,
                    "--selector", "app.kubernetes.io/name=mariadb",
                    "--output", "jsonpath={.items[0].metadata.name}"
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            pod_name = result.stdout.strip()
            if not pod_name:
                raise RuntimeError("No MariaDB pod found")
            
            # Note: This is a placeholder for actual database restore
            # Production implementation would need proper credentials and restore logic
            # Similar to the backup, this would use scripts/backup-mariadb.sh or similar
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to restore databases: {e.stderr}")
    
    def _apply_previous_versions(
        self,
        chart_versions_path: str,
        namespace: str
    ) -> None:
        """Apply previous helm chart versions.
        
        This method reads the restored helm-chart-versions.yaml and applies
        the charts in reverse dependency order.
        
        Args:
            chart_versions_path: Path to helm-chart-versions.yaml
            namespace: Kubernetes namespace
            
        Raises:
            FileNotFoundError: If chart versions file doesn't exist
            RuntimeError: If helm operations fail
        """
        from utils.yaml_utils import read_yaml_file
        
        chart_versions_file = Path(chart_versions_path)
        if not chart_versions_file.exists():
            raise FileNotFoundError(f"Chart versions file not found: {chart_versions_path}")
        
        # Read chart versions
        data = read_yaml_file(chart_versions_file)
        charts = data.get("charts", {})
        
        # Define reverse dependency order (infrastructure last)
        # This is a simplified version - production would use dependency graph
        service_order = [
            # Optional services first
            "zaqar", "trove", "octavia", "masakari", "manila", "magnum",
            "ironic", "heat", "gnocchi", "freezer", "cloudkitty", "ceilometer",
            "blazar", "barbican",
            # Core services
            "horizon", "nova", "neutron", "cinder", "placement", "glance", "keystone",
            # Infrastructure last
            "rabbitmq", "postgres-operator", "mariadb-operator", "memcached"
        ]
        
        errors = []
        
        for service_name in service_order:
            if service_name not in charts:
                continue
            
            try:
                # Use helm rollback to revert to previous version
                # This assumes the release exists and has history
                self.helm_executor.rollback_release(service_name)
            except Exception as e:
                errors.append(f"Failed to rollback {service_name}: {e}")
        
        if errors:
            raise RuntimeError(f"Failed to apply some helm charts: {'; '.join(errors)}")
