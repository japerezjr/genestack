#!/usr/bin/env python3
"""
CLI script to validate OpenStack helm configuration files.

This script scans helm override configurations for:
- YAML syntax errors
- Caracal version strings in image tags
- Deprecated configuration options

Usage:
    python validate_configs.py <base-helm-configs-path> [options]

Example:
    python validate_configs.py ../base-helm-configs --report validation-report.md
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.validator import ConfigurationValidator


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate OpenStack helm configuration files for Caracal to Epoxy upgrade"
    )
    
    parser.add_argument(
        "base_path",
        help="Path to base-helm-configs directory"
    )
    
    parser.add_argument(
        "--deprecation-rules",
        default=None,
        help="Path to deprecation rules YAML file (default: config/deprecation-rules.yaml)"
    )
    
    parser.add_argument(
        "--report",
        default=None,
        help="Path to save validation report (default: print to stdout)"
    )
    
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "text"],
        default="markdown",
        help="Report format (default: markdown)"
    )
    
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links during scan"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Determine deprecation rules file
    if args.deprecation_rules:
        rules_file = args.deprecation_rules
    else:
        # Use default rules file
        default_rules = Path(__file__).parent.parent / "config" / "deprecation-rules.yaml"
        rules_file = str(default_rules) if default_rules.exists() else None
    
    if rules_file:
        logger.info(f"Using deprecation rules: {rules_file}")
    else:
        logger.warning("No deprecation rules file specified or found")
    
    # Create validator
    logger.info(f"Scanning configurations in: {args.base_path}")
    validator = ConfigurationValidator(args.base_path, rules_file)
    
    # Run validation
    report = validator.validate_all(follow_symlinks=args.follow_symlinks)
    
    # Print summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"Files scanned: {report.total_files_scanned}")
    print(f"Files with issues: {report.files_with_issues}")
    print(f"Total issues: {report.get_total_issues()}")
    print(f"  - YAML errors: {len(report.yaml_errors)}")
    print(f"  - YAML warnings: {len(report.yaml_warnings)}")
    print(f"  - Image tag issues: {len(report.image_tag_issues)}")
    print(f"  - Deprecated options: {len(report.deprecation_issues)}")
    print("="*80)
    
    # Save or print report
    if args.report:
        report.save_to_file(args.report, format=args.format)
        logger.info(f"Report saved to: {args.report}")
    else:
        print("\n" + report.to_markdown())
    
    # Exit with appropriate code
    if report.has_errors():
        logger.error("Validation failed with errors")
        sys.exit(1)
    elif report.has_critical_issues():
        logger.warning("Validation found critical issues")
        sys.exit(2)
    elif report.get_total_issues() > 0:
        logger.warning("Validation found issues")
        sys.exit(3)
    else:
        logger.info("Validation passed with no issues")
        sys.exit(0)


if __name__ == "__main__":
    main()
