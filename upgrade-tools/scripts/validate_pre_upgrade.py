#!/usr/bin/env python3
"""Pre-upgrade validation script for OpenStack Caracal to Epoxy upgrade."""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from health.validator import PreUpgradeValidator, ValidationError


def main():
    """Run pre-upgrade validation checks."""
    parser = argparse.ArgumentParser(
        description="Validate OpenStack deployment before upgrading from Caracal to Epoxy"
    )
    parser.add_argument(
        "--backup-path",
        default="/var/backups/openstack",
        help="Path to backup directory (default: /var/backups/openstack)"
    )
    parser.add_argument(
        "--namespace",
        default="openstack",
        help="Kubernetes namespace (default: openstack)"
    )
    parser.add_argument(
        "--skip-endpoints",
        action="store_true",
        help="Skip OpenStack API endpoint checks"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--in-cluster",
        action="store_true",
        help="Use in-cluster Kubernetes configuration"
    )
    parser.add_argument(
        "--halt-on-failure",
        action="store_true",
        help="Exit with error code if validation fails"
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = PreUpgradeValidator(
        in_cluster=args.in_cluster,
        check_endpoints=not args.skip_endpoints,
        backup_path=args.backup_path,
        namespace=args.namespace
    )
    
    try:
        # Run validation
        if args.halt_on_failure:
            report = validator.validate_and_halt_on_failure()
            print(validator.generate_detailed_report(output_format=args.format))
            return 0
        else:
            report_text = validator.generate_detailed_report(output_format=args.format)
            print(report_text)
            
            # Get the report to check if it passed
            report = validator.validate()
            return 0 if report.passed else 1
            
    except ValidationError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        print("\n" + e.report.summary, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
