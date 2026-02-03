#!/usr/bin/env python3
"""
CLI script to update OpenStack helm chart versions from Caracal to Epoxy.

Usage:
    python update_chart_versions.py [OPTIONS]

Options:
    --versions-file PATH    Path to helm-chart-versions.yaml (default: ../helm-chart-versions.yaml)
    --dry-run              Show what would be changed without making changes
    --report-path PATH     Path to save the report (default: version-update-report.md)
    --report-format FORMAT Report format: markdown, text, or json (default: markdown)
    --target-release VER   Target release version (default: 2025.1)
    --help                 Show this help message
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.version import ChartVersionManager


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Update OpenStack helm chart versions from Caracal to Epoxy',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--versions-file',
        default='../helm-chart-versions.yaml',
        help='Path to helm-chart-versions.yaml file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    
    parser.add_argument(
        '--report-path',
        default='version-update-report.md',
        help='Path to save the report'
    )
    
    parser.add_argument(
        '--report-format',
        choices=['markdown', 'text', 'json'],
        default='markdown',
        help='Report format'
    )
    
    parser.add_argument(
        '--target-release',
        default='2025.1',
        help='Target OpenStack release version'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Resolve paths
    versions_file = Path(args.versions_file).resolve()
    report_path = Path(args.report_path).resolve()
    
    if not versions_file.exists():
        logger.error(f"Versions file not found: {versions_file}")
        return 1
    
    logger.info(f"Using versions file: {versions_file}")
    logger.info(f"Target release: {args.target_release}")
    logger.info(f"Dry run: {args.dry_run}")
    
    try:
        # Create manager
        manager = ChartVersionManager(str(versions_file))
        
        # Run upgrade workflow
        report = manager.upgrade_caracal_to_epoxy(
            dry_run=args.dry_run,
            generate_report=True,
            report_path=str(report_path),
            report_format=args.report_format
        )
        
        # Print summary
        print("\n" + "=" * 70)
        print("Version Update Summary")
        print("=" * 70)
        print(f"Total charts: {report.total_charts}")
        print(f"Updated charts: {report.updated_charts}")
        print(f"Unchanged charts: {report.total_charts - report.updated_charts}")
        
        if report.errors:
            print("\nErrors:")
            for error in report.errors:
                print(f"  - {error}")
        
        if report.warnings:
            print("\nWarnings:")
            for warning in report.warnings:
                print(f"  - {warning}")
        
        if report.updates:
            print(f"\nUpdated charts:")
            for update in sorted(report.updates, key=lambda u: u.chart_name):
                print(f"  - {update.chart_name}: {update.current_version} -> {update.target_version}")
        
        print(f"\nReport saved to: {report_path}")
        print("=" * 70)
        
        if args.dry_run:
            print("\nDRY RUN MODE: No changes were made to the versions file.")
            print("Run without --dry-run to apply changes.")
        else:
            print(f"\nVersions file updated: {versions_file}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to update versions: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
