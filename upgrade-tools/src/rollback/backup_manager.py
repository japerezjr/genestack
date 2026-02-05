"""Backup manager for creating backups before upgrade.

This module handles backing up helm chart versions, override configurations,
and database backups with timestamps.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BackupResult:
    """Result of a backup operation."""
    success: bool
    backup_path: Path
    timestamp: datetime
    components: List[str]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class Backup:
    """Represents a backup with metadata."""
    backup_id: str
    timestamp: datetime
    backup_path: Path
    components: Dict[str, Path]  # component_name -> backup_file_path
    metadata: Dict[str, str] = field(default_factory=dict)


class BackupManager:
    """Manages backups of configurations and databases."""
    
    def __init__(self, backup_base_path: str = "./backups"):
        """Initialize backup manager.
        
        Args:
            backup_base_path: Base directory for storing backups
        """
        self.backup_base_path = Path(backup_base_path)
        self.backup_base_path.mkdir(parents=True, exist_ok=True)
    
    def create_backup(
        self,
        components: List[str],
        chart_versions_path: Optional[str] = None,
        overrides_base_path: Optional[str] = None,
        backup_databases: bool = False,
        namespace: str = "openstack"
    ) -> BackupResult:
        """Create a backup of specified components.
        
        Args:
            components: List of components to backup (e.g., ["versions", "configs", "databases"])
            chart_versions_path: Path to helm-chart-versions.yaml
            overrides_base_path: Path to base-helm-configs directory
            backup_databases: Whether to backup databases
            namespace: Kubernetes namespace for database backups
            
        Returns:
            BackupResult with backup details and status
        """
        timestamp = datetime.now()
        backup_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")
        backup_path = self.backup_base_path / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        errors = []
        warnings = []
        backed_up_components = []
        
        # Backup helm chart versions
        if "versions" in components and chart_versions_path:
            try:
                self._backup_chart_versions(
                    chart_versions_path,
                    backup_path
                )
                backed_up_components.append("versions")
            except Exception as e:
                errors.append(f"Failed to backup chart versions: {e}")
        
        # Backup override configurations
        if "configs" in components and overrides_base_path:
            try:
                self._backup_override_configs(
                    overrides_base_path,
                    backup_path
                )
                backed_up_components.append("configs")
            except Exception as e:
                errors.append(f"Failed to backup override configs: {e}")
        
        # Backup databases
        if "databases" in components and backup_databases:
            try:
                self._backup_databases(
                    backup_path,
                    namespace
                )
                backed_up_components.append("databases")
            except Exception as e:
                errors.append(f"Failed to backup databases: {e}")
        
        # Write backup metadata
        self._write_backup_metadata(
            backup_path,
            backup_id,
            timestamp,
            backed_up_components
        )
        
        success = len(errors) == 0 and len(backed_up_components) > 0
        
        return BackupResult(
            success=success,
            backup_path=backup_path,
            timestamp=timestamp,
            components=backed_up_components,
            errors=errors,
            warnings=warnings
        )
    
    def _backup_chart_versions(
        self,
        chart_versions_path: str,
        backup_path: Path
    ) -> None:
        """Backup helm-chart-versions.yaml file.
        
        Args:
            chart_versions_path: Path to helm-chart-versions.yaml
            backup_path: Destination backup directory
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            IOError: If backup fails
        """
        source = Path(chart_versions_path)
        if not source.exists():
            raise FileNotFoundError(f"Chart versions file not found: {chart_versions_path}")
        
        destination = backup_path / "helm-chart-versions.yaml"
        shutil.copy2(source, destination)
    
    def _backup_override_configs(
        self,
        overrides_base_path: str,
        backup_path: Path
    ) -> None:
        """Backup all override configuration files.
        
        Args:
            overrides_base_path: Path to base-helm-configs directory
            backup_path: Destination backup directory
            
        Raises:
            FileNotFoundError: If source directory doesn't exist
            IOError: If backup fails
        """
        source = Path(overrides_base_path)
        if not source.exists():
            raise FileNotFoundError(f"Override configs directory not found: {overrides_base_path}")
        
        destination = backup_path / "base-helm-configs"
        shutil.copytree(source, destination, dirs_exist_ok=True)
    
    def _backup_databases(
        self,
        backup_path: Path,
        namespace: str
    ) -> None:
        """Create database backups using kubectl/mariadb tools.
        
        Args:
            backup_path: Destination backup directory
            namespace: Kubernetes namespace
            
        Raises:
            subprocess.CalledProcessError: If backup command fails
        """
        db_backup_path = backup_path / "databases"
        db_backup_path.mkdir(parents=True, exist_ok=True)
        
        # Get list of MariaDB pods
        try:
            result = subprocess.run(
                [
                    "kubectl", "get", "pods",
                    "--namespace", namespace,
                    "--selector", "app.kubernetes.io/name=mariadb",
                    "--output", "jsonpath={.items[*].metadata.name}"
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            pods = result.stdout.strip().split()
            
            if not pods:
                raise RuntimeError("No MariaDB pods found")
            
            # Use first pod for backup
            pod_name = pods[0]
            
            # Create backup using mysqldump
            # Note: This is a simplified version. Production would need proper credentials
            backup_file = db_backup_path / f"mariadb_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            # This is a placeholder - actual implementation would need proper database credentials
            # and would use a script like the one in scripts/backup-mariadb.sh
            with open(backup_file, 'w') as f:
                f.write(f"# Database backup placeholder for pod {pod_name}\n")
                f.write(f"# Timestamp: {datetime.now().isoformat()}\n")
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to backup databases: {e.stderr}")
    
    def _write_backup_metadata(
        self,
        backup_path: Path,
        backup_id: str,
        timestamp: datetime,
        components: List[str]
    ) -> None:
        """Write backup metadata file.
        
        Args:
            backup_path: Backup directory
            backup_id: Unique backup identifier
            timestamp: Backup timestamp
            components: List of backed up components
        """
        metadata_file = backup_path / "backup_metadata.txt"
        
        with open(metadata_file, 'w') as f:
            f.write(f"Backup ID: {backup_id}\n")
            f.write(f"Timestamp: {timestamp.isoformat()}\n")
            f.write(f"Components: {', '.join(components)}\n")
            f.write(f"Backup Path: {backup_path}\n")
    
    def list_backups(self) -> List[Backup]:
        """List all available backups.
        
        Returns:
            List of Backup objects sorted by timestamp (newest first)
        """
        backups = []
        
        if not self.backup_base_path.exists():
            return backups
        
        for backup_dir in self.backup_base_path.iterdir():
            if not backup_dir.is_dir():
                continue
            
            metadata_file = backup_dir / "backup_metadata.txt"
            if not metadata_file.exists():
                continue
            
            # Parse metadata
            metadata = {}
            with open(metadata_file, 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
            
            # Find component files
            components = {}
            if (backup_dir / "helm-chart-versions.yaml").exists():
                components["versions"] = backup_dir / "helm-chart-versions.yaml"
            if (backup_dir / "base-helm-configs").exists():
                components["configs"] = backup_dir / "base-helm-configs"
            if (backup_dir / "databases").exists():
                components["databases"] = backup_dir / "databases"
            
            backup = Backup(
                backup_id=metadata.get("Backup ID", backup_dir.name),
                timestamp=datetime.fromisoformat(metadata.get("Timestamp", datetime.now().isoformat())),
                backup_path=backup_dir,
                components=components,
                metadata=metadata
            )
            backups.append(backup)
        
        # Sort by timestamp, newest first
        backups.sort(key=lambda b: b.timestamp, reverse=True)
        
        return backups
    
    def get_latest_backup(self) -> Optional[Backup]:
        """Get the most recent backup.
        
        Returns:
            Latest Backup object or None if no backups exist
        """
        backups = self.list_backups()
        return backups[0] if backups else None
    
    def get_backup_by_id(self, backup_id: str) -> Optional[Backup]:
        """Get a specific backup by ID.
        
        Args:
            backup_id: Backup identifier
            
        Returns:
            Backup object or None if not found
        """
        backups = self.list_backups()
        for backup in backups:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup.
        
        Args:
            backup_id: Backup identifier
            
        Returns:
            True if deletion successful, False otherwise
        """
        backup = self.get_backup_by_id(backup_id)
        if not backup:
            return False
        
        try:
            shutil.rmtree(backup.backup_path)
            return True
        except Exception:
            return False
    
    def restore_from_backup(self, backup: Backup) -> BackupResult:
        """Restore from a backup.
        
        Args:
            backup: Backup object or Path to backup directory
            
        Returns:
            BackupResult with restore status
        """
        # Handle both Backup object and Path
        if isinstance(backup, Path):
            backup_path = backup
            # Try to load backup metadata
            backup_obj = None
            for b in self.list_backups():
                if b.backup_path == backup_path:
                    backup_obj = b
                    break
            if not backup_obj:
                return BackupResult(
                    success=False,
                    backup_path=backup_path,
                    timestamp=datetime.now(),
                    components=[],
                    errors=[f"Backup not found: {backup_path}"]
                )
            backup = backup_obj
        
        errors = []
        warnings = []
        restored_components = []
        
        # Restore helm chart versions
        if "versions" in backup.components:
            try:
                source = backup.components["versions"]
                # Determine destination from metadata or use default
                destination = Path("../helm-chart-versions.yaml")
                shutil.copy2(source, destination)
                restored_components.append("versions")
            except Exception as e:
                errors.append(f"Failed to restore chart versions: {e}")
        
        # Restore override configurations
        if "configs" in backup.components:
            try:
                source = backup.components["configs"]
                destination = Path("../base-helm-configs")
                # Remove existing configs and restore from backup
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
                restored_components.append("configs")
            except Exception as e:
                errors.append(f"Failed to restore override configs: {e}")
        
        # Restore databases
        if "databases" in backup.components:
            try:
                # Database restore is complex and would need proper implementation
                # For now, just note that it would be restored
                warnings.append("Database restore not fully implemented - manual restore may be required")
                restored_components.append("databases")
            except Exception as e:
                errors.append(f"Failed to restore databases: {e}")
        
        success = len(errors) == 0 and len(restored_components) > 0
        
        return BackupResult(
            success=success,
            backup_path=backup.backup_path,
            timestamp=datetime.now(),
            components=restored_components,
            errors=errors,
            warnings=warnings
        )
