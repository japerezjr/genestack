#!/usr/bin/env python3
"""
Script to detect breaking changes in OpenStack configurations.

This script analyzes helm override configurations to identify breaking changes
between Caracal and Epoxy releases.
"""

import sys
import argparse
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from breaking_changes import BreakingChangeDetector


def scan_config_files(base_path: Path) -> list:
    """Scan for YAML configuration files."""
    config_files = []
    for pattern in ['**/*.yaml', '**/*.yml']:
        config_files.extend(base_path.glob(pattern))
    return [str(f) for f in config_files]


def load_config_file(filepath: Path) -> dict:
    """Load a YAML configuration file."""
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(
        description='Detect breaking changes in OpenStack configurations'
    )
    parser.add_argument(
        '--config-dir',
        type=str,
        default='../base-helm-configs',
        help='Path to base-helm-configs directory'
    )
    parser.add_argument(
        '--service',
        type=str,
        help='Analyze specific service only'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: print to stdout)'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['markdown', 'text', 'json'],
        default='markdown',
        help='Output format'
    )
    parser.add_argument(
        '--mitigation-plan',
        type=str,
        help='Generate mitigation plan to specified file'
    )
    parser.add_argument(
        '--show-stats',
        action='store_true',
        help='Show catalog statistics'
    )
    parser.add_argument(
        '--list-critical',
        action='store_true',
        help='List all critical breaking changes'
    )
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = BreakingChangeDetector()
    
    # Show statistics if requested
    if args.show_stats:
        stats = detector.get_catalog_statistics()
        print("Breaking Changes Catalog Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  By Severity: {stats['by_severity']}")
        print(f"  By Component: {stats['by_component']}")
        print(f"  By Type: {stats['by_type']}")
        print()
    
    # List critical changes if requested
    if args.list_critical:
        critical = detector.get_critical_changes()
        print(f"Critical Breaking Changes ({len(critical)}):")
        for change in critical:
            print(f"  - {change.id}: {change.title} ({change.component})")
        print()
    
    # If only showing info, exit
    if args.show_stats or args.list_critical:
        if not args.config_dir:
            return 0
    
    # Scan configurations
    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        print(f"Error: Configuration directory not found: {config_dir}")
        return 1
    
    print(f"Scanning configurations in {config_dir}...")
    
    # Load configurations
    config_files = scan_config_files(config_dir)
    
    print(f"Found {len(config_files)} configuration files")
    
    # Load config data
    override_configs = {}
    for config_file in config_files:
        # Extract service name from path
        parts = Path(config_file).parts
        if 'base-helm-configs' in parts:
            idx = parts.index('base-helm-configs')
            if idx + 1 < len(parts):
                service_name = parts[idx + 1]
                
                # Filter by service if specified
                if args.service and service_name != args.service:
                    continue
                
                config_data = load_config_file(Path(config_file))
                if config_data:
                    override_configs[service_name] = config_data
    
    print(f"Loaded configurations for {len(override_configs)} services")
    
    # Detect breaking changes
    print("Analyzing for breaking changes...")
    report = detector.detect_in_deployment(override_configs)
    
    # Generate report
    report_content = detector.generate_report(report, args.output, args.format)
    
    # Print to stdout if no output file
    if not args.output:
        print("\n" + "=" * 80)
        print(report_content)
    else:
        print(f"Report written to {args.output}")
    
    # Generate mitigation plan if requested
    if args.mitigation_plan:
        plan = detector.generate_mitigation_plan(report, args.mitigation_plan, args.format)
        print(f"Mitigation plan written to {args.mitigation_plan}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Breaking Changes Affecting Deployment: {report.total_affected}")
    print(f"  Critical: {report.critical_count}")
    print(f"  High: {report.high_count}")
    print(f"  Medium: {report.medium_count}")
    print(f"  Low: {report.low_count}")
    
    if report.has_critical_issues:
        print("\n⚠️  WARNING: Critical issues detected!")
        print("These issues will prevent upgrade and must be addressed first.")
        return 2
    elif report.has_blocking_issues:
        print("\n⚠️  WARNING: High priority issues detected!")
        print("These issues should be addressed before upgrade.")
        return 1
    else:
        print("\n✅ No critical or high priority issues detected.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
