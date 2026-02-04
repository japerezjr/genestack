"""Version update logic for helm chart versions."""

import re
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .parser import VersionParser, VersionUpdate, CARACAL_VERSION_PATTERN
from utils.yaml_utils import read_yaml_file, write_yaml_file


logger = logging.getLogger(__name__)


class VersionUpdater:
    """Handles updating helm chart versions."""
    
    def __init__(self, chart_versions_path: str):
        """
        Initialize the version updater.
        
        Args:
            chart_versions_path: Path to helm-chart-versions.yaml file
        """
        self.chart_versions_path = Path(chart_versions_path)
        self.parser = VersionParser(str(chart_versions_path))
        
    def update_versions(
        self, 
        updates: List[VersionUpdate],
        target_release: str = "2025.1",
        dry_run: bool = False
    ) -> Dict[str, str]:
        """
        Update chart versions in the helm-chart-versions.yaml file.
        
        Args:
            updates: List of VersionUpdate objects specifying what to update
            target_release: Target OpenStack release version (default: "2025.1")
            dry_run: If True, don't write changes to file
            
        Returns:
            Dictionary of updated chart versions (chart_name -> new_version)
            
        Raises:
            FileNotFoundError: If the versions file doesn't exist
            ValueError: If the file format is invalid or updates are invalid
        """
        # Load current versions
        data = read_yaml_file(self.chart_versions_path)
        
        if 'charts' not in data:
            raise ValueError(f"Invalid format: 'charts' key not found in {self.chart_versions_path}")
        
        charts = data['charts']
        updated_charts = {}
        
        # Apply each update
        for update in updates:
            if update.chart_name not in charts:
                logger.warning(f"Chart '{update.chart_name}' not found in versions file, skipping")
                continue
            
            current = charts[update.chart_name]
            
            # Verify the current version matches what we expect
            if current != update.current_version:
                logger.warning(
                    f"Version mismatch for {update.chart_name}: "
                    f"expected {update.current_version}, found {current}"
                )
            
            # Apply the update
            new_version = self._replace_version(current, target_release)
            charts[update.chart_name] = new_version
            updated_charts[update.chart_name] = new_version
            
            logger.info(f"Updated {update.chart_name}: {current} -> {new_version}")
        
        # Write updated versions back to file (unless dry run)
        if not dry_run:
            data['charts'] = charts
            write_yaml_file(self.chart_versions_path, data)
            logger.info(f"Wrote updated versions to {self.chart_versions_path}")
        else:
            logger.info("Dry run mode: changes not written to file")
        
        return updated_charts
    
    def _replace_version(self, current_version: str, target_release: str) -> str:
        """
        Replace Caracal version strings with Epoxy version.
        
        Args:
            current_version: Current version string
            target_release: Target release version (e.g., "2025.1")
            
        Returns:
            Updated version string with Caracal version replaced
        """
        # Replace 2024.1 or 2024.2 with target release
        new_version = CARACAL_VERSION_PATTERN.sub(target_release, current_version)
        return new_version
    
    def replace_caracal_with_epoxy(
        self,
        target_release: str = "2025.1",
        preserve_non_openstack: bool = True,
        dry_run: bool = False
    ) -> Dict[str, str]:
        """
        Replace all Caracal versions with Epoxy versions.
        
        This is a convenience method that identifies all charts needing updates
        and applies them in one operation.
        
        Args:
            target_release: Target OpenStack release version (default: "2025.1")
            preserve_non_openstack: If True, only update OpenStack service charts
            dry_run: If True, don't write changes to file
            
        Returns:
            Dictionary of updated chart versions (chart_name -> new_version)
        """
        # Identify charts that need updating
        updates = self.parser.identify_updates(target_release)
        
        if not updates:
            logger.info("No charts need updating")
            return {}
        
        logger.info(f"Found {len(updates)} charts to update")
        
        # Apply updates
        return self.update_versions(updates, target_release, dry_run)
    
    def update_single_chart(
        self,
        chart_name: str,
        new_version: str,
        dry_run: bool = False
    ) -> bool:
        """
        Update a single chart to a specific version.
        
        Args:
            chart_name: Name of the chart to update
            new_version: New version string
            dry_run: If True, don't write changes to file
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Load current versions
            data = read_yaml_file(self.chart_versions_path)
            
            if 'charts' not in data:
                raise ValueError(f"Invalid format: 'charts' key not found")
            
            charts = data['charts']
            
            if chart_name not in charts:
                logger.error(f"Chart '{chart_name}' not found in versions file")
                return False
            
            old_version = charts[chart_name]
            charts[chart_name] = new_version
            
            # Write updated versions back to file (unless dry run)
            if not dry_run:
                data['charts'] = charts
                write_yaml_file(self.chart_versions_path, data)
                logger.info(f"Updated {chart_name}: {old_version} -> {new_version}")
            else:
                logger.info(f"Dry run: would update {chart_name}: {old_version} -> {new_version}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update {chart_name}: {e}")
            return False
    
    def validate_updates(self, updates: List[VersionUpdate]) -> List[str]:
        """
        Validate that proposed updates are valid.
        
        Args:
            updates: List of VersionUpdate objects to validate
            
        Returns:
            List of error messages (empty if all updates are valid)
        """
        errors = []
        
        # Load current versions
        try:
            charts = self.parser.load_versions()
        except Exception as e:
            errors.append(f"Failed to load current versions: {e}")
            return errors
        
        for update in updates:
            # Check if chart exists
            if update.chart_name not in charts:
                errors.append(f"Chart '{update.chart_name}' not found in versions file")
                continue
            
            # Check if current version matches
            actual_current = charts[update.chart_name]
            if actual_current != update.current_version:
                errors.append(
                    f"Version mismatch for {update.chart_name}: "
                    f"expected {update.current_version}, found {actual_current}"
                )
            
            # Check if target version is valid (not empty, not same as current)
            if not update.target_version:
                errors.append(f"Target version for {update.chart_name} is empty")
            elif update.target_version == update.current_version:
                errors.append(f"Target version for {update.chart_name} is same as current")
        
        return errors
