"""Configuration file scanner for discovering YAML override files."""

import os
import logging
from pathlib import Path
from typing import List, Set


logger = logging.getLogger(__name__)


class ConfigurationScanner:
    """
    Scanner for discovering helm override configuration files.
    
    This class recursively scans a directory for YAML files,
    handling symbolic links and permission issues gracefully.
    """
    
    YAML_EXTENSIONS = {'.yaml', '.yml'}
    
    def __init__(self, base_path: str):
        """
        Initialize the configuration scanner.
        
        Args:
            base_path: Base directory to scan (e.g., base-helm-configs/)
        """
        self.base_path = Path(base_path)
        self.discovered_files: List[Path] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def scan(self, follow_symlinks: bool = False) -> List[str]:
        """
        Recursively scan for YAML configuration files.
        
        Args:
            follow_symlinks: If True, follow symbolic links during scan
            
        Returns:
            List of absolute paths to discovered YAML files
        """
        if not self.base_path.exists():
            error_msg = f"Base path does not exist: {self.base_path}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return []
        
        if not self.base_path.is_dir():
            error_msg = f"Base path is not a directory: {self.base_path}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return []
        
        logger.info(f"Scanning directory: {self.base_path}")
        self.discovered_files = []
        self.errors = []
        self.warnings = []
        
        self._scan_directory(self.base_path, follow_symlinks)
        
        logger.info(f"Discovered {len(self.discovered_files)} YAML files")
        if self.errors:
            logger.warning(f"Encountered {len(self.errors)} errors during scan")
        if self.warnings:
            logger.info(f"Generated {len(self.warnings)} warnings during scan")
        
        return [str(f.absolute()) for f in self.discovered_files]
    
    def _scan_directory(self, directory: Path, follow_symlinks: bool) -> None:
        """
        Recursively scan a directory for YAML files.
        
        Args:
            directory: Directory to scan
            follow_symlinks: Whether to follow symbolic links
        """
        try:
            entries = list(directory.iterdir())
        except PermissionError as e:
            warning_msg = f"Permission denied accessing directory: {directory}"
            logger.warning(warning_msg)
            self.warnings.append(warning_msg)
            return
        except OSError as e:
            error_msg = f"Error accessing directory {directory}: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return
        
        for entry in entries:
            try:
                # Handle symbolic links
                if entry.is_symlink():
                    if not follow_symlinks:
                        logger.debug(f"Skipping symbolic link: {entry}")
                        continue
                    
                    # Check if symlink target exists
                    try:
                        entry.resolve(strict=True)
                    except (OSError, RuntimeError) as e:
                        warning_msg = f"Broken symbolic link: {entry}"
                        logger.warning(warning_msg)
                        self.warnings.append(warning_msg)
                        continue
                
                # Process directories recursively
                if entry.is_dir():
                    self._scan_directory(entry, follow_symlinks)
                
                # Process YAML files
                elif entry.is_file() and self._is_yaml_file(entry):
                    logger.debug(f"Found YAML file: {entry}")
                    self.discovered_files.append(entry)
            
            except PermissionError:
                warning_msg = f"Permission denied accessing: {entry}"
                logger.warning(warning_msg)
                self.warnings.append(warning_msg)
            except OSError as e:
                error_msg = f"Error processing {entry}: {e}"
                logger.error(error_msg)
                self.errors.append(error_msg)
    
    def _is_yaml_file(self, path: Path) -> bool:
        """
        Check if a file has a YAML extension.
        
        Args:
            path: Path to check
            
        Returns:
            True if file has .yaml or .yml extension
        """
        return path.suffix.lower() in self.YAML_EXTENSIONS
    
    def filter_by_pattern(self, pattern: str) -> List[str]:
        """
        Filter discovered files by a glob pattern.
        
        Args:
            pattern: Glob pattern (e.g., "*-helm-overrides.yaml")
            
        Returns:
            List of file paths matching the pattern
        """
        if not self.discovered_files:
            logger.warning("No files discovered yet. Run scan() first.")
            return []
        
        matching = [
            str(f.absolute())
            for f in self.discovered_files
            if f.match(pattern)
        ]
        
        logger.info(f"Filtered to {len(matching)} files matching pattern: {pattern}")
        return matching
    
    def get_files_by_service(self) -> dict:
        """
        Group discovered files by service name.
        
        Returns:
            Dictionary mapping service names to file paths
        """
        if not self.discovered_files:
            logger.warning("No files discovered yet. Run scan() first.")
            return {}
        
        services = {}
        for file_path in self.discovered_files:
            # Extract service name from directory structure
            # e.g., base-helm-configs/keystone/keystone-helm-overrides.yaml -> keystone
            try:
                relative = file_path.relative_to(self.base_path)
                service_name = relative.parts[0] if relative.parts else "unknown"
                
                if service_name not in services:
                    services[service_name] = []
                services[service_name].append(str(file_path.absolute()))
            except ValueError:
                # File is not relative to base_path
                logger.warning(f"File not relative to base path: {file_path}")
        
        logger.info(f"Grouped files into {len(services)} services")
        return services
    
    def get_scan_summary(self) -> dict:
        """
        Get a summary of the scan results.
        
        Returns:
            Dictionary with scan statistics
        """
        return {
            "base_path": str(self.base_path.absolute()),
            "total_files": len(self.discovered_files),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "services": len(self.get_files_by_service())
        }
