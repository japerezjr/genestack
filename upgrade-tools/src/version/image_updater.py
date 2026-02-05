"""Image tag updater for OpenStack container images.

This module updates container image tags in Helm override files
to match the target OpenStack release.
"""

import re
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class ImageUpdateResult:
    """Result of updating image tags."""
    
    file_path: str
    images_updated: int = 0
    images_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = True
    
    def __str__(self) -> str:
        """String representation."""
        if self.success:
            return f"{self.file_path}: {self.images_updated} images updated, {self.images_skipped} skipped"
        return f"{self.file_path}: FAILED - {', '.join(self.errors)}"


class ImageTagUpdater:
    """Updates container image tags in Helm override files."""
    
    # Release version patterns
    RELEASE_PATTERNS = {
        "2024.1": ["2024.1", "caracal"],
        "2024.2": ["2024.2", "caracal"],
        "2025.1": ["2025.1", "epoxy"],
        "2025.2": ["2025.2", "epoxy"]
    }
    
    # Images that should not be updated (infrastructure/tools)
    SKIP_IMAGES = {
        "kubernetes-entrypoint",
        "dep-check",
        "image-repo-sync",
        "ceph-config-helper"
    }
    
    def __init__(
        self,
        source_release: str,
        target_release: str,
        overrides_base_path: str
    ):
        """Initialize the image tag updater.
        
        Args:
            source_release: Source OpenStack release (e.g., "2024.2")
            target_release: Target OpenStack release (e.g., "2025.1")
            overrides_base_path: Base path to helm override files
        """
        self.source_release = source_release
        self.target_release = target_release
        self.overrides_base_path = Path(overrides_base_path)
        
        # Build regex patterns for source release
        self.source_patterns = self._build_patterns(source_release)
        
        logger.info(
            f"ImageTagUpdater initialized: {source_release} -> {target_release}"
        )
        logger.debug(f"Source patterns: {[p.pattern for p in self.source_patterns]}")
    
    def _build_patterns(self, release: str) -> List[re.Pattern]:
        """Build regex patterns for a release version.
        
        Args:
            release: Release version (e.g., "2024.2")
            
        Returns:
            List of compiled regex patterns
        """
        patterns = []
        
        # Get all version strings for this release
        version_strings = self.RELEASE_PATTERNS.get(release, [release])
        
        for version in version_strings:
            # Match version with optional suffix (e.g., "2024.1-latest", "2024.1-ubuntu")
            pattern = re.compile(
                rf"({re.escape(version)})(-[a-zA-Z0-9_.-]+)?",
                re.IGNORECASE
            )
            patterns.append(pattern)
        
        return patterns
    
    def _should_skip_image(self, image_name: str, image_value: str) -> bool:
        """Check if an image should be skipped.
        
        Args:
            image_name: Name of the image key (e.g., "keystone_api")
            image_value: Image tag value
            
        Returns:
            True if image should be skipped
        """
        if not image_value or image_value == "null":
            logger.debug(f"Skipping {image_name}: null or empty value")
            return True
        
        # Check if it's in the skip list
        for skip_image in self.SKIP_IMAGES:
            if skip_image in image_value.lower():
                logger.debug(f"Skipping {image_name}: matches skip pattern '{skip_image}'")
                return True
        
        # Skip if it doesn't contain source release version
        has_source_version = any(
            pattern.search(image_value)
            for pattern in self.source_patterns
        )
        
        if not has_source_version:
            logger.debug(f"Skipping {image_name}: no source version match in '{image_value}'")
        
        return not has_source_version
    
    def _update_image_tag(self, image_value: str) -> Tuple[str, bool]:
        """Update an image tag from source to target release.
        
        Args:
            image_value: Original image tag
            
        Returns:
            Tuple of (updated_tag, was_updated)
        """
        updated = image_value
        was_updated = False
        
        # Try each source pattern
        for pattern in self.source_patterns:
            if pattern.search(updated):
                # Replace source version with target version
                updated = pattern.sub(
                    lambda m: self.target_release + (m.group(2) or ""),
                    updated
                )
                was_updated = True
                break
        
        return updated, was_updated
    
    def update_file(self, file_path: Path) -> ImageUpdateResult:
        """Update image tags in a single override file.
        
        Args:
            file_path: Path to the override file
            
        Returns:
            ImageUpdateResult with update details
        """
        result = ImageUpdateResult(file_path=str(file_path))
        
        try:
            # Read the file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse YAML
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError as e:
                result.errors.append(f"YAML parse error: {e}")
                result.success = False
                return result
            
            if not data or not isinstance(data, dict):
                result.warnings.append("Empty or invalid YAML structure")
                return result
            
            # Check if images section exists
            if "images" not in data or "tags" not in data.get("images", {}):
                result.warnings.append("No images.tags section found")
                return result
            
            # Update image tags
            tags = data["images"]["tags"]
            updated_tags = {}
            
            for image_name, image_value in tags.items():
                if not isinstance(image_value, str):
                    updated_tags[image_name] = image_value
                    continue
                
                # Check if should skip
                if self._should_skip_image(image_name, image_value):
                    updated_tags[image_name] = image_value
                    result.images_skipped += 1
                    logger.debug(f"Skipping {image_name}: {image_value}")
                    continue
                
                # Update the tag
                new_value, was_updated = self._update_image_tag(image_value)
                updated_tags[image_name] = new_value
                
                if was_updated:
                    result.images_updated += 1
                    logger.info(f"Updated {image_name}: {image_value} -> {new_value}")
                else:
                    result.images_skipped += 1
            
            # Update the data structure
            data["images"]["tags"] = updated_tags
            
            # Write back to file if changes were made
            if result.images_updated > 0:
                with open(file_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
                logger.info(f"Updated {file_path}: {result.images_updated} images")
            
        except Exception as e:
            result.errors.append(f"Unexpected error: {e}")
            result.success = False
            logger.error(f"Failed to update {file_path}: {e}")
        
        return result
    
    def update_service(self, service_name: str) -> ImageUpdateResult:
        """Update image tags for a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            ImageUpdateResult with update details
        """
        service_dir = self.overrides_base_path / service_name
        
        if not service_dir.exists():
            result = ImageUpdateResult(file_path=str(service_dir))
            result.errors.append(f"Service directory not found: {service_dir}")
            result.success = False
            return result
        
        # Find the helm overrides file
        override_file = service_dir / f"{service_name}-helm-overrides.yaml"
        
        if not override_file.exists():
            result = ImageUpdateResult(file_path=str(override_file))
            result.warnings.append(f"Override file not found: {override_file}")
            return result
        
        return self.update_file(override_file)
    
    def update_all_services(
        self,
        services: Optional[List[str]] = None
    ) -> Dict[str, ImageUpdateResult]:
        """Update image tags for multiple services.
        
        Args:
            services: List of service names (None = all services in base path)
            
        Returns:
            Dictionary mapping service names to ImageUpdateResult
        """
        results = {}
        
        # Determine which services to update
        if services:
            service_list = services
        else:
            # Find all service directories
            service_list = [
                d.name for d in self.overrides_base_path.iterdir()
                if d.is_dir() and not d.name.startswith('.')
            ]
        
        logger.info(f"Updating image tags for {len(service_list)} services")
        
        # Update each service
        for service_name in service_list:
            result = self.update_service(service_name)
            results[service_name] = result
        
        # Log summary
        total_updated = sum(r.images_updated for r in results.values())
        total_skipped = sum(r.images_skipped for r in results.values())
        total_errors = sum(len(r.errors) for r in results.values())
        
        logger.info(
            f"Image update complete: {total_updated} updated, "
            f"{total_skipped} skipped, {total_errors} errors"
        )
        
        return results
