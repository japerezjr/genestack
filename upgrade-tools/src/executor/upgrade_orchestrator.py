"""Upgrade orchestration for OpenStack services.

This module orchestrates the upgrade of multiple OpenStack services
in dependency order with monitoring and failure handling.
"""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .dependency_graph import DependencyGraph
from .service_upgrader import ServiceUpgrader, ServiceUpgradeResult


@dataclass
class UpgradeOrchestrationResult:
    """Result of orchestrating multiple service upgrades."""
    success: bool
    total_duration: float  # seconds
    services_upgraded: List[str]
    services_failed: List[str]
    service_results: Dict[str, ServiceUpgradeResult]
    errors: List[str]
    warnings: List[str]
    timestamp: str


class UpgradeOrchestrator:
    """Orchestrates upgrade of multiple OpenStack services."""
    
    def __init__(
        self,
        service_upgrader: ServiceUpgrader,
        dependency_graph: Optional[DependencyGraph] = None
    ):
        """Initialize upgrade orchestrator.
        
        Args:
            service_upgrader: ServiceUpgrader for individual service upgrades
            dependency_graph: DependencyGraph for determining upgrade order
        """
        self.service_upgrader = service_upgrader
        self.dependency_graph = dependency_graph or DependencyGraph()
        self.upgrade_log = []
    
    def orchestrate_upgrade(
        self,
        services: List[str],
        chart_base_path: str,
        skip_optional: bool = False,
        halt_on_failure: bool = True,
        timeout_per_service: Optional[int] = None
    ) -> UpgradeOrchestrationResult:
        """Orchestrate upgrade of multiple services in dependency order.
        
        Args:
            services: List of service names to upgrade
            chart_base_path: Base path to helm charts
            skip_optional: If True, skip optional services
            halt_on_failure: If True, stop on first failure
            timeout_per_service: Timeout in seconds for each service
            
        Returns:
            UpgradeOrchestrationResult with overall status
        """
        start_time = time.time()
        errors = []
        warnings = []
        services_upgraded = []
        services_failed = []
        service_results = {}
        
        try:
            # Step 1: Determine upgrade order
            self._log_action("Determining upgrade order")
            
            # Create dependency graph with requested services
            graph = DependencyGraph(services)
            upgrade_order = graph.get_upgrade_order(skip_optional=skip_optional)
            
            self._log_action(f"Upgrade order: {', '.join(upgrade_order)}")
            
            # Step 2: Validate dependencies
            missing_deps = graph.validate_dependencies()
            if missing_deps:
                warning_msg = f"Some services have missing dependencies: {missing_deps}"
                warnings.append(warning_msg)
                self._log_action(warning_msg)
            
            # Step 3: Execute upgrades in order
            for service_name in upgrade_order:
                self._log_action(f"Starting upgrade of {service_name}")
                
                # Construct chart path
                chart_path = f"{chart_base_path}/{service_name}"
                
                # Upgrade the service
                result = self.service_upgrader.upgrade_service(
                    service_name=service_name,
                    chart_path=chart_path,
                    timeout=timeout_per_service
                )
                
                # Store result
                service_results[service_name] = result
                
                # Log result
                if result.success:
                    services_upgraded.append(service_name)
                    self._log_action(
                        f"Successfully upgraded {service_name} "
                        f"(duration: {result.duration:.1f}s)"
                    )
                else:
                    services_failed.append(service_name)
                    error_msg = f"Failed to upgrade {service_name}: {', '.join(result.errors)}"
                    errors.append(error_msg)
                    self._log_action(error_msg)
                    
                    # Halt on failure if requested
                    if halt_on_failure:
                        self._log_action("Halting upgrade due to failure")
                        break
                
                # Collect warnings
                if result.warnings:
                    warnings.extend(result.warnings)
            
            # Step 4: Determine overall success
            overall_success = len(services_failed) == 0
            
            duration = time.time() - start_time
            
            return UpgradeOrchestrationResult(
                success=overall_success,
                total_duration=duration,
                services_upgraded=services_upgraded,
                services_failed=services_failed,
                service_results=service_results,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            errors.append(f"Orchestration error: {str(e)}")
            self._log_action(f"Orchestration error: {str(e)}")
            
            duration = time.time() - start_time
            
            return UpgradeOrchestrationResult(
                success=False,
                total_duration=duration,
                services_upgraded=services_upgraded,
                services_failed=services_failed,
                service_results=service_results,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now().isoformat()
            )
    
    def orchestrate_full_upgrade(
        self,
        chart_base_path: str,
        skip_optional: bool = False,
        halt_on_failure: bool = True,
        timeout_per_service: Optional[int] = None
    ) -> UpgradeOrchestrationResult:
        """Orchestrate upgrade of all OpenStack services.
        
        Args:
            chart_base_path: Base path to helm charts
            skip_optional: If True, skip optional services
            halt_on_failure: If True, stop on first failure
            timeout_per_service: Timeout in seconds for each service
            
        Returns:
            UpgradeOrchestrationResult with overall status
        """
        # Get all services from dependency graph
        all_services = list(self.dependency_graph.services)
        
        return self.orchestrate_upgrade(
            services=all_services,
            chart_base_path=chart_base_path,
            skip_optional=skip_optional,
            halt_on_failure=halt_on_failure,
            timeout_per_service=timeout_per_service
        )
    
    def _log_action(self, message: str):
        """Log an action with timestamp.
        
        Args:
            message: Message to log
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.upgrade_log.append(log_entry)
    
    def get_upgrade_log(self) -> List[str]:
        """Get the upgrade log.
        
        Returns:
            List of log entries
        """
        return self.upgrade_log.copy()
    
    def generate_upgrade_report(self, result: UpgradeOrchestrationResult) -> str:
        """Generate a formatted upgrade report.
        
        Args:
            result: UpgradeOrchestrationResult to format
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("OpenStack Upgrade Report")
        lines.append("=" * 70)
        lines.append(f"Timestamp: {result.timestamp}")
        lines.append(f"Overall Status: {'SUCCESS' if result.success else 'FAILED'}")
        lines.append(f"Total Duration: {result.total_duration:.1f} seconds")
        lines.append("")
        
        lines.append("Summary:")
        lines.append(f"  Services Upgraded: {len(result.services_upgraded)}")
        lines.append(f"  Services Failed: {len(result.services_failed)}")
        lines.append("")
        
        if result.services_upgraded:
            lines.append("Successfully Upgraded Services:")
            for service in result.services_upgraded:
                service_result = result.service_results[service]
                lines.append(f"  - {service} (duration: {service_result.duration:.1f}s)")
            lines.append("")
        
        if result.services_failed:
            lines.append("Failed Services:")
            for service in result.services_failed:
                service_result = result.service_results[service]
                lines.append(f"  - {service}")
                for error in service_result.errors:
                    lines.append(f"    Error: {error}")
            lines.append("")
        
        if result.warnings:
            lines.append("Warnings:")
            for warning in result.warnings:
                lines.append(f"  - {warning}")
            lines.append("")
        
        if result.errors:
            lines.append("Errors:")
            for error in result.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        lines.append("Upgrade Log:")
        for log_entry in self.upgrade_log:
            lines.append(f"  {log_entry}")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
