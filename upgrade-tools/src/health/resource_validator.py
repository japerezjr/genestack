"""Resource and backup validation for pre-upgrade checks."""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from kubernetes import client
from kubernetes.client.rest import ApiException


@dataclass
class ResourceStatus:
    """Status of cluster resources."""
    
    total_cpu: float  # Total CPU cores
    used_cpu: float  # Used CPU cores
    available_cpu: float  # Available CPU cores
    cpu_utilization: float  # CPU utilization percentage
    
    total_memory: float  # Total memory in GB
    used_memory: float  # Used memory in GB
    available_memory: float  # Available memory in GB
    memory_utilization: float  # Memory utilization percentage
    
    total_storage: Optional[float] = None  # Total storage in GB
    used_storage: Optional[float] = None  # Used storage in GB
    available_storage: Optional[float] = None  # Available storage in GB
    storage_utilization: Optional[float] = None  # Storage utilization percentage
    
    sufficient: bool = True
    issues: List[str] = field(default_factory=list)


@dataclass
class BackupStatus:
    """Status of database backups."""
    
    backup_path: str
    backups_found: List[str] = field(default_factory=list)
    latest_backup: Optional[str] = None
    latest_backup_age: Optional[timedelta] = None
    backup_valid: bool = False
    issues: List[str] = field(default_factory=list)


@dataclass
class JobStatus:
    """Status of active jobs and migrations."""
    
    active_jobs: List[str] = field(default_factory=list)
    active_migrations: List[str] = field(default_factory=list)
    safe_to_upgrade: bool = True
    issues: List[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report."""
    
    timestamp: datetime
    resource_status: ResourceStatus
    backup_status: BackupStatus
    job_status: JobStatus
    passed: bool
    
    @property
    def summary(self) -> str:
        """Generate a summary of the validation."""
        lines = []
        lines.append(f"Validation Status: {'PASSED' if self.passed else 'FAILED'}")
        lines.append(f"Timestamp: {self.timestamp.isoformat()}")
        lines.append("")
        
        # Resource status
        lines.append("Resources:")
        lines.append(f"  CPU: {self.resource_status.cpu_utilization:.1f}% used")
        lines.append(f"  Memory: {self.resource_status.memory_utilization:.1f}% used")
        if self.resource_status.storage_utilization:
            lines.append(f"  Storage: {self.resource_status.storage_utilization:.1f}% used")
        
        if self.resource_status.issues:
            lines.append("  Issues:")
            for issue in self.resource_status.issues:
                lines.append(f"    - {issue}")
        lines.append("")
        
        # Backup status
        lines.append("Backups:")
        if self.backup_status.latest_backup:
            lines.append(f"  Latest: {self.backup_status.latest_backup}")
            if self.backup_status.latest_backup_age:
                hours = self.backup_status.latest_backup_age.total_seconds() / 3600
                lines.append(f"  Age: {hours:.1f} hours")
        else:
            lines.append("  No backups found")
        
        if self.backup_status.issues:
            lines.append("  Issues:")
            for issue in self.backup_status.issues:
                lines.append(f"    - {issue}")
        lines.append("")
        
        # Job status
        lines.append("Active Jobs/Migrations:")
        if self.job_status.active_jobs:
            lines.append(f"  Jobs: {len(self.job_status.active_jobs)}")
        if self.job_status.active_migrations:
            lines.append(f"  Migrations: {len(self.job_status.active_migrations)}")
        
        if not self.job_status.active_jobs and not self.job_status.active_migrations:
            lines.append("  None")
        
        if self.job_status.issues:
            lines.append("  Issues:")
            for issue in self.job_status.issues:
                lines.append(f"    - {issue}")
        
        return "\n".join(lines)


class ResourceValidator:
    """Validates cluster resources and backups for upgrade readiness."""
    
    def __init__(
        self,
        in_cluster: bool = False,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        storage_threshold: float = 80.0,
        backup_max_age_hours: int = 24
    ):
        """
        Initialize the resource validator.
        
        Args:
            in_cluster: If True, use in-cluster config
            cpu_threshold: Maximum CPU utilization percentage
            memory_threshold: Maximum memory utilization percentage
            storage_threshold: Maximum storage utilization percentage
            backup_max_age_hours: Maximum age of backups in hours
        """
        try:
            if in_cluster:
                from kubernetes import config as k8s_config
                k8s_config.load_incluster_config()
            else:
                from kubernetes import config as k8s_config
                k8s_config.load_kube_config()
            
            self.v1 = client.CoreV1Api()
            self.batch_v1 = client.BatchV1Api()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Kubernetes client: {e}")
        
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.storage_threshold = storage_threshold
        self.backup_max_age_hours = backup_max_age_hours
    
    def check_cluster_resources(self) -> ResourceStatus:
        """
        Check cluster resource availability.
        
        Returns:
            ResourceStatus with resource information
        """
        try:
            nodes = self.v1.list_node()
            
            total_cpu = 0.0
            total_memory = 0.0
            allocatable_cpu = 0.0
            allocatable_memory = 0.0
            
            # Get node capacities
            for node in nodes.items:
                capacity = node.status.capacity
                allocatable = node.status.allocatable
                
                # CPU (in cores)
                total_cpu += self._parse_cpu(capacity.get("cpu", "0"))
                allocatable_cpu += self._parse_cpu(allocatable.get("cpu", "0"))
                
                # Memory (convert to GB)
                total_memory += self._parse_memory(capacity.get("memory", "0Ki"))
                allocatable_memory += self._parse_memory(allocatable.get("memory", "0Ki"))
            
            # Get pod resource requests to estimate usage
            pods = self.v1.list_pod_for_all_namespaces()
            used_cpu = 0.0
            used_memory = 0.0
            
            for pod in pods.items:
                if pod.spec.containers:
                    for container in pod.spec.containers:
                        if container.resources and container.resources.requests:
                            requests = container.resources.requests
                            used_cpu += self._parse_cpu(requests.get("cpu", "0"))
                            used_memory += self._parse_memory(requests.get("memory", "0Ki"))
            
            # Calculate available resources
            available_cpu = allocatable_cpu - used_cpu
            available_memory = allocatable_memory - used_memory
            
            # Calculate utilization
            cpu_utilization = (used_cpu / allocatable_cpu * 100) if allocatable_cpu > 0 else 0
            memory_utilization = (used_memory / allocatable_memory * 100) if allocatable_memory > 0 else 0
            
            # Check thresholds
            issues = []
            sufficient = True
            
            if cpu_utilization > self.cpu_threshold:
                issues.append(
                    f"CPU utilization ({cpu_utilization:.1f}%) exceeds threshold "
                    f"({self.cpu_threshold}%)"
                )
                sufficient = False
            
            if memory_utilization > self.memory_threshold:
                issues.append(
                    f"Memory utilization ({memory_utilization:.1f}%) exceeds threshold "
                    f"({self.memory_threshold}%)"
                )
                sufficient = False
            
            return ResourceStatus(
                total_cpu=total_cpu,
                used_cpu=used_cpu,
                available_cpu=available_cpu,
                cpu_utilization=cpu_utilization,
                total_memory=total_memory,
                used_memory=used_memory,
                available_memory=available_memory,
                memory_utilization=memory_utilization,
                sufficient=sufficient,
                issues=issues
            )
            
        except ApiException as e:
            raise RuntimeError(f"Failed to check cluster resources: {e}")
    
    def check_backups(self, backup_path: str) -> BackupStatus:
        """
        Check for database backups.
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            BackupStatus with backup information
        """
        issues = []
        backups_found = []
        latest_backup = None
        latest_backup_age = None
        backup_valid = False
        
        # Check if backup path exists
        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            issues.append(f"Backup directory does not exist: {backup_path}")
            return BackupStatus(
                backup_path=backup_path,
                backups_found=backups_found,
                latest_backup=latest_backup,
                latest_backup_age=latest_backup_age,
                backup_valid=backup_valid,
                issues=issues
            )
        
        # Find backup files (common patterns)
        # Search recursively to handle timestamped subdirectories
        backup_patterns = ["**/*.sql", "**/*.sql.gz", "**/*.dump", "**/*.backup", "**/*.tar.gz"]
        
        for pattern in backup_patterns:
            backups_found.extend([str(f) for f in backup_dir.glob(pattern)])
        
        if not backups_found:
            issues.append("No backup files found")
            return BackupStatus(
                backup_path=backup_path,
                backups_found=backups_found,
                latest_backup=latest_backup,
                latest_backup_age=latest_backup_age,
                backup_valid=backup_valid,
                issues=issues
            )
        
        # Find the most recent backup
        latest_file = None
        latest_mtime = 0
        
        for backup_file in backups_found:
            mtime = os.path.getmtime(backup_file)
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_file = backup_file
        
        if latest_file:
            latest_backup = latest_file
            backup_time = datetime.fromtimestamp(latest_mtime)
            latest_backup_age = datetime.now() - backup_time
            
            # Check if backup is recent enough
            max_age = timedelta(hours=self.backup_max_age_hours)
            if latest_backup_age > max_age:
                issues.append(
                    f"Latest backup is too old: {latest_backup_age.total_seconds() / 3600:.1f} hours "
                    f"(max: {self.backup_max_age_hours} hours)"
                )
            else:
                backup_valid = True
        
        return BackupStatus(
            backup_path=backup_path,
            backups_found=backups_found,
            latest_backup=latest_backup,
            latest_backup_age=latest_backup_age,
            backup_valid=backup_valid,
            issues=issues
        )
    
    def check_active_jobs(self, namespace: str = "openstack") -> JobStatus:
        """
        Check for active jobs and migrations.
        
        Args:
            namespace: Kubernetes namespace to check
            
        Returns:
            JobStatus with active job information
        """
        issues = []
        active_jobs = []
        active_migrations = []
        safe_to_upgrade = True
        
        try:
            # Check for active Kubernetes jobs
            jobs = self.batch_v1.list_namespaced_job(namespace)
            
            for job in jobs.items:
                # Check if job is still active (not completed)
                if job.status.active and job.status.active > 0:
                    job_name = job.metadata.name
                    active_jobs.append(job_name)
                    
                    # Check if it's a migration job
                    if "db-sync" in job_name or "migration" in job_name.lower():
                        active_migrations.append(job_name)
            
            if active_jobs:
                issues.append(f"Found {len(active_jobs)} active jobs")
                safe_to_upgrade = False
            
            if active_migrations:
                issues.append(f"Found {len(active_migrations)} active migration jobs")
                safe_to_upgrade = False
            
        except ApiException as e:
            issues.append(f"Failed to check jobs: {e}")
            safe_to_upgrade = False
        
        return JobStatus(
            active_jobs=active_jobs,
            active_migrations=active_migrations,
            safe_to_upgrade=safe_to_upgrade,
            issues=issues
        )
    
    def validate_all(
        self,
        backup_path: str,
        namespace: str = "openstack"
    ) -> ValidationReport:
        """
        Run all validation checks.
        
        Args:
            backup_path: Path to backup directory
            namespace: Kubernetes namespace to check
            
        Returns:
            ValidationReport with all validation results
        """
        resource_status = self.check_cluster_resources()
        backup_status = self.check_backups(backup_path)
        job_status = self.check_active_jobs(namespace)
        
        # Validation passes if all checks pass
        passed = (
            resource_status.sufficient and
            backup_status.backup_valid and
            job_status.safe_to_upgrade
        )
        
        return ValidationReport(
            timestamp=datetime.now(),
            resource_status=resource_status,
            backup_status=backup_status,
            job_status=job_status,
            passed=passed
        )
    
    @staticmethod
    def _parse_cpu(cpu_str: str) -> float:
        """
        Parse CPU string to float (cores).
        
        Args:
            cpu_str: CPU string (e.g., "2", "500m")
            
        Returns:
            CPU in cores
        """
        if not cpu_str:
            return 0.0
        
        cpu_str = str(cpu_str).strip()
        
        if cpu_str.endswith("m"):
            # Millicores
            return float(cpu_str[:-1]) / 1000.0
        else:
            # Cores
            return float(cpu_str)
    
    @staticmethod
    def _parse_memory(memory_str: str) -> float:
        """
        Parse memory string to float (GB).
        
        Args:
            memory_str: Memory string (e.g., "2Gi", "1024Mi", "1000000Ki")
            
        Returns:
            Memory in GB
        """
        if not memory_str:
            return 0.0
        
        memory_str = str(memory_str).strip()
        
        # Parse unit
        units = {
            "Ki": 1024,
            "Mi": 1024 ** 2,
            "Gi": 1024 ** 3,
            "Ti": 1024 ** 4,
            "K": 1000,
            "M": 1000 ** 2,
            "G": 1000 ** 3,
            "T": 1000 ** 4,
        }
        
        for unit, multiplier in units.items():
            if memory_str.endswith(unit):
                value = float(memory_str[:-len(unit)])
                bytes_value = value * multiplier
                return bytes_value / (1024 ** 3)  # Convert to GB
        
        # No unit, assume bytes
        return float(memory_str) / (1024 ** 3)
