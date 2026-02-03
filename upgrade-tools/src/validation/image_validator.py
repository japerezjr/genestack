"""Image tag validation for detecting Caracal version strings."""

import re
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ImageTagIssue:
    """Represents an image tag that needs updating."""
    
    file_path: str
    image_key: str  # Path to the image in the YAML (e.g., "images.tags.keystone_api")
    current_tag: str
    recommended_tag: str
    description: str
    
    def __str__(self) -> str:
        """String representation of the issue."""
        return (
            f"{self.file_path} - {self.image_key}:\n"
            f"  Current: {self.current_tag}\n"
            f"  Recommended: {self.recommended_tag}\n"
            f"  Reason: {self.description}"
        )


class ImageTagValidator:
    """
    Validator for detecting and updating Caracal version strings in image tags.
    
    This class scans configuration files for image tags containing Caracal
    version strings (2024.1, 2024.2) and generates recommendations for
    updating to Epoxy (2025.1).
    """
    
    # Caracal version patterns
    CARACAL_PATTERNS = [
        r'2024\.1',
        r'2024\.2',
    ]
    
    # Epoxy version
    EPOXY_VERSION = "2025.1"
    
    def __init__(self):
        """Initialize the image tag validator."""
        self.issues: List[ImageTagIssue] = []
        self.compiled_patterns = [re.compile(p) for p in self.CARACAL_PATTERNS]
    
    def validate_config(
        self,
        config: Dict[str, Any],
        file_path: str
    ) -> List[ImageTagIssue]:
        """
        Validate image tags in a configuration file.
        
        Args:
            config: Parsed YAML configuration
            file_path: Path to the configuration file
            
        Returns:
            List of image tag issues found in this file
        """
        file_issues = []
        
        # Extract image tags from configuration
        image_tags = self._extract_image_tags(config)
        
        # Check each image tag for Caracal versions
        for key, tag in image_tags.items():
            if self._contains_caracal_version(tag):
                recommended = self._generate_recommendation(tag)
                
                issue = ImageTagIssue(
                    file_path=file_path,
                    image_key=key,
                    current_tag=tag,
                    recommended_tag=recommended,
                    description=f"Image tag contains Caracal version string"
                )
                
                file_issues.append(issue)
                self.issues.append(issue)
                logger.info(f"Found Caracal version in {file_path}: {key}")
        
        return file_issues
    
    def _extract_image_tags(
        self,
        config: Dict[str, Any],
        prefix: str = ""
    ) -> Dict[str, str]:
        """
        Recursively extract image tags from configuration.
        
        Args:
            config: Configuration dictionary
            prefix: Key prefix for nested structures
            
        Returns:
            Dictionary mapping image keys to tag values
        """
        tags = {}
        
        if not isinstance(config, dict):
            return tags
        
        # Check for images.tags section (common pattern)
        if 'images' in config and isinstance(config['images'], dict):
            if 'tags' in config['images'] and isinstance(config['images']['tags'], dict):
                for key, value in config['images']['tags'].items():
                    if isinstance(value, str):
                        full_key = f"images.tags.{key}"
                        tags[full_key] = value
        
        # Also scan for any string values that look like image tags
        # (format: registry/repo:tag)
        for key, value in config.items():
            current_prefix = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, str):
                # Check if it looks like an image tag (contains : and /)
                if ':' in value and '/' in value:
                    tags[current_prefix] = value
            
            elif isinstance(value, dict):
                # Recursively process nested dictionaries
                nested_tags = self._extract_image_tags(value, current_prefix)
                tags.update(nested_tags)
            
            elif isinstance(value, list):
                # Process lists
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        nested_tags = self._extract_image_tags(
                            item,
                            f"{current_prefix}[{i}]"
                        )
                        tags.update(nested_tags)
                    elif isinstance(item, str) and ':' in item and '/' in item:
                        tags[f"{current_prefix}[{i}]"] = item
        
        return tags
    
    def _contains_caracal_version(self, tag: str) -> bool:
        """
        Check if an image tag contains a Caracal version string.
        
        Args:
            tag: Image tag to check
            
        Returns:
            True if tag contains Caracal version
        """
        for pattern in self.compiled_patterns:
            if pattern.search(tag):
                return True
        return False
    
    def _generate_recommendation(self, current_tag: str) -> str:
        """
        Generate recommended tag by replacing Caracal version with Epoxy.
        
        Args:
            current_tag: Current image tag
            
        Returns:
            Recommended tag with Epoxy version
        """
        recommended = current_tag
        
        # Replace all Caracal version patterns with Epoxy version
        for pattern in self.compiled_patterns:
            recommended = pattern.sub(self.EPOXY_VERSION, recommended)
        
        return recommended
    
    def get_issues(self) -> List[ImageTagIssue]:
        """Get all image tag issues found."""
        return self.issues
    
    def get_issues_by_file(self) -> Dict[str, List[ImageTagIssue]]:
        """
        Group issues by file path.
        
        Returns:
            Dictionary mapping file paths to lists of issues
        """
        by_file = {}
        for issue in self.issues:
            if issue.file_path not in by_file:
                by_file[issue.file_path] = []
            by_file[issue.file_path].append(issue)
        return by_file
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of image tag validation.
        
        Returns:
            Dictionary with validation statistics
        """
        by_file = self.get_issues_by_file()
        
        return {
            "total_issues": len(self.issues),
            "files_affected": len(by_file),
            "unique_images": len(set(i.image_key for i in self.issues))
        }
    
    def generate_update_recommendations(self) -> List[Dict[str, str]]:
        """
        Generate a list of update recommendations.
        
        Returns:
            List of dictionaries with update information
        """
        recommendations = []
        
        for issue in self.issues:
            recommendations.append({
                "file": issue.file_path,
                "key": issue.image_key,
                "current": issue.current_tag,
                "recommended": issue.recommended_tag,
                "action": f"Update {issue.image_key} from {issue.current_tag} to {issue.recommended_tag}"
            })
        
        return recommendations
    
    def apply_recommendations(
        self,
        config: Dict[str, Any],
        file_path: str
    ) -> Dict[str, Any]:
        """
        Apply recommendations to a configuration.
        
        This creates a new configuration with updated image tags.
        
        Args:
            config: Original configuration
            file_path: Path to the configuration file
            
        Returns:
            Updated configuration
        """
        import copy
        updated_config = copy.deepcopy(config)
        
        # Get issues for this file
        file_issues = [i for i in self.issues if i.file_path == file_path]
        
        for issue in file_issues:
            # Parse the key path (e.g., "images.tags.keystone_api")
            keys = issue.image_key.split('.')
            
            # Navigate to the parent and update the value
            current = updated_config
            for key in keys[:-1]:
                if key in current:
                    current = current[key]
                else:
                    logger.warning(f"Key path not found: {issue.image_key}")
                    break
            else:
                # Update the final key
                final_key = keys[-1]
                if final_key in current:
                    current[final_key] = issue.recommended_tag
                    logger.info(f"Updated {issue.image_key} to {issue.recommended_tag}")
        
        return updated_config
