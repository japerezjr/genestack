#!/usr/bin/env python3
"""
Apply configuration updates for Caracal to Epoxy upgrade.

This script automates:
1. Updating image tags from 2024.1/2024.2 to 2025.1
2. Removing deprecated oslo.messaging options
3. Creating backups before making changes
"""

import argparse
import logging
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.yaml_utils import read_yaml_file, write_yaml_file


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigUpdater:
    """Applies configuration updates for Caracal to Epoxy upgrade."""
    
    def __init__(self, base_path: str, backup_dir: str = None, dry_run: bool = False):
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = Path(f"backups/config_backup_{timestamp}")
        
        self.stats = {
            "files_processed": 0,
            "files_updated": 0,
            "image_tags_updated": 0,
            "deprecated_options_removed": 0,
            "errors": 0
        }
    
    def create_backup(self, file_path: Path) -> Path:
        """Create a backup of the file before modifying."""
        relative_path = file_path.relative_to(self.base_path)
        backup_path = self.backup_dir / relative_path
        
        if not self.dry_run:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
        
        return backup_path
    
    def update_image_tags(self, content: str, file_path: Path) -> Tuple[str, int]:
        """
        Update image tags from Caracal (2024.1/2024.2) to Epoxy (2025.1).
        
        Returns:
            Tuple of (updated_content, number_of_changes)
        """
        changes = 0
        
        # Pattern to match version strings in image tags
        # Matches: 2024.1 or 2024.2 followed by optional build info
        patterns = [
            (r':2024\.1-', ':2025.1-'),  # :2024.1-latest -> :2025.1-latest
            (r':2024\.2-', ':2025.1-'),  # :2024.2-latest -> :2025.1-latest
            (r':2024\.1_', ':2025.1_'),  # :2024.1_ubuntu -> :2025.1_ubuntu
            (r':2024\.2_', ':2025.1_'),  # :2024.2_ubuntu -> :2025.1_ubuntu
        ]
        
        updated_content = content
        for pattern, replacement in patterns:
            matches = re.findall(pattern, updated_content)
            if matches:
                updated_content = re.sub(pattern, replacement, updated_content)
                changes += len(matches)
                logger.debug(f"Updated {len(matches)} occurrences of {pattern} in {file_path.name}")
        
        return updated_content, changes
    
    def remove_deprecated_options(self, content: str, file_path: Path) -> Tuple[str, int]:
        """
        Remove deprecated oslo.messaging options.
        
        Removes:
        - heartbeat_in_pthread option (deprecated in 2024.2)
        - neutron_linuxbridge_agent image tag (Linux Bridge removed in Epoxy)
        
        Returns:
            Tuple of (updated_content, number_of_changes)
        """
        changes = 0
        lines = content.split('\n')
        updated_lines = []
        skip_next = False
        
        for i, line in enumerate(lines):
            # Skip lines with heartbeat_in_pthread
            if 'heartbeat_in_pthread' in line:
                logger.debug(f"Removing deprecated option in {file_path.name}: {line.strip()}")
                changes += 1
                continue
            
            # Skip neutron_linuxbridge_agent image tag
            if 'neutron_linuxbridge_agent' in line and 'images.tags' in line:
                logger.debug(f"Removing deprecated Linux Bridge agent in {file_path.name}")
                changes += 1
                # Also skip the next line if it's the image value
                if i + 1 < len(lines) and ':' in lines[i + 1]:
                    skip_next = True
                continue
            
            if skip_next:
                skip_next = False
                continue
            
            updated_lines.append(line)
        
        return '\n'.join(updated_lines), changes
    
    def process_file(self, file_path: Path) -> bool:
        """
        Process a single configuration file.
        
        Returns:
            True if file was updated, False otherwise
        """
        self.stats["files_processed"] += 1
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Apply updates
            updated_content = original_content
            total_changes = 0
            
            # Update image tags
            updated_content, image_changes = self.update_image_tags(updated_content, file_path)
            total_changes += image_changes
            self.stats["image_tags_updated"] += image_changes
            
            # Remove deprecated options
            updated_content, deprecated_changes = self.remove_deprecated_options(updated_content, file_path)
            total_changes += deprecated_changes
            self.stats["deprecated_options_removed"] += deprecated_changes
            
            # If changes were made, backup and write
            if total_changes > 0:
                logger.info(f"Updating {file_path.name}: {image_changes} image tags, {deprecated_changes} deprecated options")
                
                if not self.dry_run:
                    # Create backup
                    self.create_backup(file_path)
                    
                    # Write updated content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                
                self.stats["files_updated"] += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats["errors"] += 1
            return False
    
    def process_directory(self, patterns: List[str] = None) -> None:
        """
        Process all YAML files in the base directory.
        
        Args:
            patterns: Optional list of glob patterns to match files
        """
        if patterns is None:
            patterns = ["**/*-helm-overrides.yaml", "**/*-overrides.yaml"]
        
        files_to_process = []
        for pattern in patterns:
            files_to_process.extend(self.base_path.glob(pattern))
        
        # Remove duplicates
        files_to_process = list(set(files_to_process))
        
        logger.info(f"Found {len(files_to_process)} files to process")
        
        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
        
        for file_path in sorted(files_to_process):
            self.process_file(file_path)
    
    def print_summary(self) -> None:
        """Print summary of changes made."""
        print("\n" + "=" * 80)
        print("UPDATE SUMMARY")
        print("=" * 80)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files updated: {self.stats['files_updated']}")
        print(f"Image tags updated: {self.stats['image_tags_updated']}")
        print(f"Deprecated options removed: {self.stats['deprecated_options_removed']}")
        print(f"Errors: {self.stats['errors']}")
        
        if self.dry_run:
            print("\nDRY RUN MODE - No actual changes were made")
        else:
            print(f"\nBackups saved to: {self.backup_dir}")
        
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Apply configuration updates for Caracal to Epoxy upgrade",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be changed
  python apply_config_updates.py ../base-helm-configs --dry-run
  
  # Apply updates with automatic backup
  python apply_config_updates.py ../base-helm-configs
  
  # Apply updates with custom backup location
  python apply_config_updates.py ../base-helm-configs --backup-dir /path/to/backups
  
  # Process only specific files
  python apply_config_updates.py ../base-helm-configs --pattern "nova/*.yaml"
        """
    )
    
    parser.add_argument(
        "base_path",
        help="Base path to configuration directory (e.g., ../base-helm-configs)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making actual changes"
    )
    
    parser.add_argument(
        "--backup-dir",
        help="Custom backup directory (default: backups/config_backup_TIMESTAMP)"
    )
    
    parser.add_argument(
        "--pattern",
        action="append",
        help="Glob pattern for files to process (can be specified multiple times)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate base path
    base_path = Path(args.base_path)
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        sys.exit(1)
    
    if not base_path.is_dir():
        logger.error(f"Base path is not a directory: {base_path}")
        sys.exit(1)
    
    # Create updater and process files
    updater = ConfigUpdater(
        base_path=args.base_path,
        backup_dir=args.backup_dir,
        dry_run=args.dry_run
    )
    
    updater.process_directory(patterns=args.pattern)
    updater.print_summary()
    
    # Exit with error code if there were errors
    if updater.stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
