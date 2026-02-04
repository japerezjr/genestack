#!/usr/bin/env python3
"""Example demonstrating the logging and reporting system.

This script shows how to use the UpgradeLogger, SummaryReportGenerator,
and UpgradeDocGenerator together during an upgrade operation.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logging import (
    UpgradeLogger,
    LogLevel,
    SummaryReportGenerator,
    UpgradeDocGenerator
)


def main():
    """Run example upgrade with logging and reporting."""
    print("=" * 80)
    print("OpenStack Upgrade Logging and Reporting Example")
    print("=" * 80)
    print()
    
    # Setup output directory
    output_dir = Path("example_output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize components
    print("Initializing logging and reporting components...")
    logger = UpgradeLogger(
        log_file=output_dir / "upgrade.log",
        console_level=LogLevel.INFO,
        file_level=LogLevel.DEBUG
    )
    
    report_gen = SummaryReportGenerator()
    doc_gen = UpgradeDocGenerator()
    
    # Start upgrade
    print("Starting upgrade simulation...")
    report_gen.start_upgrade()
    logger.info("Starting OpenStack Caracal to Epoxy upgrade")
    
    # Phase 1: Version Updates
    print("\nPhase 1: Updating chart versions...")
    version_updates = [
        ("keystone", "2024.1-ubuntu_jammy", "2025.1-ubuntu_jammy"),
        ("glance", "2024.1-ubuntu_jammy", "2025.1-ubuntu_jammy"),
        ("nova", "2024.2-ubuntu_jammy", "2025.1-ubuntu_jammy"),
        ("neutron", "2024.1-ubuntu_jammy", "2025.1-ubuntu_jammy"),
        ("cinder", "2024.1-ubuntu_jammy", "2025.1-ubuntu_jammy"),
    ]
    
    for chart, old_ver, new_ver in version_updates:
        print(f"  Updating {chart}: {old_ver} -> {new_ver}")
        logger.log_version_update(chart, old_ver, new_ver)
        report_gen.add_version_change(chart, old_ver, new_ver)
        doc_gen.add_version_change(chart, old_ver, new_ver)
    
    # Phase 2: Configuration Updates
    print("\nPhase 2: Updating configurations...")
    config_updates = [
        ("base-helm-configs/keystone/keystone-helm-overrides.yaml", 
         {"image_tag": "2025.1", "removed_deprecated_option": "heartbeat_in_pthread"}),
        ("base-helm-configs/nova/nova-helm-overrides.yaml",
         {"image_tag": "2025.1", "replicas": 3}),
    ]
    
    for file_path, changes in config_updates:
        print(f"  Updating {file_path}")
        logger.log_config_update(file_path, changes)
        report_gen.add_config_change(file_path, changes)
        
        for key, value in changes.items():
            if key == "removed_deprecated_option":
                doc_gen.add_config_change(
                    file_path,
                    "removed",
                    f"Removed deprecated option: {value}"
                )
            else:
                doc_gen.add_config_change(
                    file_path,
                    "modified",
                    f"Updated {key}",
                    new_value=str(value)
                )
    
    # Phase 3: Breaking Changes
    print("\nPhase 3: Handling breaking changes...")
    breaking_changes = [
        {
            "component": "oslo.messaging",
            "description": "heartbeat_in_pthread option deprecated and removed",
            "mitigation": "Removed deprecated option from all service configurations"
        },
        {
            "component": "Ironic",
            "description": "PostgreSQL support removed",
            "mitigation": "Not applicable - deployment uses MariaDB"
        }
    ]
    
    for change in breaking_changes:
        print(f"  Handling {change['component']}: {change['description']}")
        doc_gen.add_breaking_change(
            change["component"],
            change["description"],
            change["mitigation"]
        )
    
    # Phase 4: Service Upgrades
    print("\nPhase 4: Upgrading services...")
    services = ["keystone", "glance", "nova", "neutron", "cinder"]
    
    for service in services:
        print(f"  Upgrading {service}...")
        logger.log_service_upgrade(service, "success", duration=45.5)
        report_gen.add_service_upgraded(service)
    
    # Phase 5: Post-upgrade verification
    print("\nPhase 5: Post-upgrade verification...")
    logger.log_health_check("all_services", "healthy", {"services_checked": 5})
    
    # Add manual steps
    print("\nAdding manual steps...")
    doc_gen.add_manual_step(
        "Verify all Nova compute agents are running",
        "nova",
        "Required to ensure compute nodes are operational after upgrade",
        commands=[
            "openstack compute service list",
            "# Verify all services show 'up' status"
        ]
    )
    
    doc_gen.add_manual_step(
        "Test instance creation",
        "nova",
        "Validate that instances can be created successfully",
        commands=[
            "openstack server create --flavor m1.small --image cirros test-instance",
            "openstack server show test-instance",
            "openstack server delete test-instance"
        ]
    )
    
    # Add warnings and notes
    doc_gen.add_warning("Database backups were created before upgrade")
    doc_gen.add_note("Upgrade completed successfully with no critical issues")
    
    # End upgrade
    report_gen.end_upgrade()
    logger.info("Upgrade completed successfully")
    
    # Generate outputs
    print("\n" + "=" * 80)
    print("Generating reports and documentation...")
    print("=" * 80)
    
    # Save action log
    action_log_file = output_dir / "action_log.json"
    logger.save_action_log(action_log_file)
    print(f"\n✓ Action log saved to: {action_log_file}")
    
    # Save summary reports
    report_gen.save_report(output_dir, format="both")
    print(f"✓ Summary reports saved to: {output_dir}/")
    
    # Save documentation
    doc_file = output_dir / "upgrade_documentation.md"
    doc_gen.save_documentation(doc_file, update_docs_dir=False)
    print(f"✓ Upgrade documentation saved to: {doc_file}")
    
    # Generate changelog entry
    changelog_file = output_dir / "CHANGELOG.md"
    doc_gen.append_to_changelog(changelog_file)
    print(f"✓ Changelog updated: {changelog_file}")
    
    # Display summary
    print("\n" + "=" * 80)
    print("Upgrade Summary")
    print("=" * 80)
    print(f"Duration: {report_gen.summary.duration}")
    print(f"Version changes: {report_gen.summary.total_version_changes}")
    print(f"Config changes: {report_gen.summary.total_config_changes}")
    print(f"Services upgraded: {len(report_gen.summary.services_upgraded)}")
    print(f"Status: {'SUCCESS' if report_gen.summary.success else 'FAILED'}")
    
    print("\n" + "=" * 80)
    print("Example completed! Check the example_output/ directory for generated files.")
    print("=" * 80)


if __name__ == "__main__":
    main()
