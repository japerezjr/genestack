"""Kubernetes pod status checker for pre-upgrade validation."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from kubernetes import client, config
from kubernetes.client.rest import ApiException


@dataclass
class PodStatus:
    """Represents the status of a pod."""
    
    name: str
    namespace: str
    phase: str  # Running, Pending, Failed, Succeeded, Unknown
    ready: bool
    restarts: int
    node: Optional[str] = None
    reason: Optional[str] = None
    message: Optional[str] = None


@dataclass
class PodStatusReport:
    """Aggregated pod status report."""
    
    total_pods: int
    running: int
    pending: int
    failed: int
    succeeded: int
    unknown: int
    pods: List[PodStatus]
    healthy: bool
    
    @property
    def summary(self) -> str:
        """Generate a summary string."""
        return (
            f"Total: {self.total_pods}, "
            f"Running: {self.running}, "
            f"Pending: {self.pending}, "
            f"Failed: {self.failed}, "
            f"Succeeded: {self.succeeded}, "
            f"Unknown: {self.unknown}"
        )


class PodStatusChecker:
    """Checks Kubernetes pod status for pre-upgrade validation."""
    
    def __init__(self, in_cluster: bool = False):
        """
        Initialize the pod status checker.
        
        Args:
            in_cluster: If True, use in-cluster config. Otherwise use kubeconfig.
        """
        try:
            if in_cluster:
                config.load_incluster_config()
            else:
                config.load_kube_config()
            self.v1 = client.CoreV1Api()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Kubernetes client: {e}")
    
    def check_namespace(self, namespace: str) -> PodStatusReport:
        """
        Check pod status in a specific namespace.
        
        Args:
            namespace: Kubernetes namespace to check
            
        Returns:
            PodStatusReport with aggregated status
        """
        try:
            pods = self.v1.list_namespaced_pod(namespace)
            return self._aggregate_pod_status(pods.items, namespace)
        except ApiException as e:
            raise RuntimeError(f"Failed to list pods in namespace {namespace}: {e}")
    
    def check_all_namespaces(self) -> PodStatusReport:
        """
        Check pod status across all namespaces.
        
        Returns:
            PodStatusReport with aggregated status
        """
        try:
            pods = self.v1.list_pod_for_all_namespaces()
            return self._aggregate_pod_status(pods.items, "all")
        except ApiException as e:
            raise RuntimeError(f"Failed to list pods across all namespaces: {e}")
    
    def check_namespaces(self, namespaces: List[str]) -> Dict[str, PodStatusReport]:
        """
        Check pod status across multiple namespaces.
        
        Args:
            namespaces: List of namespace names to check
            
        Returns:
            Dictionary mapping namespace to PodStatusReport
        """
        results = {}
        for namespace in namespaces:
            try:
                results[namespace] = self.check_namespace(namespace)
            except RuntimeError as e:
                # Create a failed report for this namespace
                results[namespace] = PodStatusReport(
                    total_pods=0,
                    running=0,
                    pending=0,
                    failed=0,
                    succeeded=0,
                    unknown=0,
                    pods=[],
                    healthy=False
                )
        return results
    
    def _aggregate_pod_status(
        self, 
        pods: List[client.V1Pod], 
        namespace: str
    ) -> PodStatusReport:
        """
        Aggregate pod status from a list of pods.
        
        Args:
            pods: List of V1Pod objects
            namespace: Namespace being checked (for reporting)
            
        Returns:
            PodStatusReport with aggregated status
        """
        pod_statuses = []
        counts = {
            "Running": 0,
            "Pending": 0,
            "Failed": 0,
            "Succeeded": 0,
            "Unknown": 0
        }
        
        for pod in pods:
            status = self._extract_pod_status(pod)
            pod_statuses.append(status)
            
            # Classify pod by phase
            phase = status.phase
            if phase in counts:
                counts[phase] += 1
            else:
                counts["Unknown"] += 1
        
        # Determine if the namespace is healthy
        # Healthy means all pods are either Running or Succeeded
        healthy = (
            counts["Failed"] == 0 and 
            counts["Pending"] == 0 and 
            counts["Unknown"] == 0
        )
        
        return PodStatusReport(
            total_pods=len(pods),
            running=counts["Running"],
            pending=counts["Pending"],
            failed=counts["Failed"],
            succeeded=counts["Succeeded"],
            unknown=counts["Unknown"],
            pods=pod_statuses,
            healthy=healthy
        )
    
    def _extract_pod_status(self, pod: client.V1Pod) -> PodStatus:
        """
        Extract status information from a V1Pod object.
        
        Args:
            pod: V1Pod object
            
        Returns:
            PodStatus with extracted information
        """
        # Get pod phase
        phase = pod.status.phase if pod.status.phase else "Unknown"
        
        # Check if all containers are ready
        ready = True
        if pod.status.container_statuses:
            ready = all(
                container.ready 
                for container in pod.status.container_statuses
            )
        
        # Count restarts
        restarts = 0
        if pod.status.container_statuses:
            restarts = sum(
                container.restart_count 
                for container in pod.status.container_statuses
            )
        
        # Get reason and message if pod is not running
        reason = None
        message = None
        if phase != "Running" and pod.status.conditions:
            for condition in pod.status.conditions:
                if condition.status == "False":
                    reason = condition.reason
                    message = condition.message
                    break
        
        return PodStatus(
            name=pod.metadata.name,
            namespace=pod.metadata.namespace,
            phase=phase,
            ready=ready,
            restarts=restarts,
            node=pod.spec.node_name,
            reason=reason,
            message=message
        )
    
    def get_unhealthy_pods(self, report: PodStatusReport) -> List[PodStatus]:
        """
        Get list of unhealthy pods from a report.
        
        Args:
            report: PodStatusReport to analyze
            
        Returns:
            List of PodStatus for unhealthy pods
        """
        unhealthy = []
        for pod in report.pods:
            if pod.phase in ["Failed", "Pending", "Unknown"] or not pod.ready:
                unhealthy.append(pod)
        return unhealthy
