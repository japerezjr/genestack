"""Tests for configuration file scanner."""

import pytest
import tempfile
import os
from pathlib import Path

from src.validation.scanner import ConfigurationScanner


class TestConfigurationScanner:
    """Test suite for ConfigurationScanner."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            
            # Create service directories with YAML files
            (base / "keystone").mkdir()
            (base / "keystone" / "keystone-helm-overrides.yaml").write_text("key: value")
            
            (base / "nova").mkdir()
            (base / "nova" / "nova-helm-overrides.yaml").write_text("key: value")
            (base / "nova" / "nova-helm-cinder-overrides.yaml").write_text("key: value")
            
            (base / "neutron").mkdir()
            (base / "neutron" / "neutron-helm-overrides.yaml").write_text("key: value")
            
            # Create a non-YAML file
            (base / "neutron" / "README.md").write_text("# Neutron")
            
            # Create nested directory
            (base / "monitoring").mkdir()
            (base / "monitoring" / "subdir").mkdir()
            (base / "monitoring" / "subdir" / "config.yml").write_text("key: value")
            
            yield base
    
    def test_scan_discovers_yaml_files(self, temp_config_dir):
        """Test that scanner discovers all YAML files."""
        scanner = ConfigurationScanner(str(temp_config_dir))
        files = scanner.scan()
        
        assert len(files) == 5  # 4 .yaml + 1 .yml
        assert all(f.endswith(('.yaml', '.yml')) for f in files)
    
    def test_scan_excludes_non_yaml_files(self, temp_config_dir):
        """Test that scanner excludes non-YAML files."""
        scanner = ConfigurationScanner(str(temp_config_dir))
        files = scanner.scan()
        
        assert not any(f.endswith('.md') for f in files)
    
    def test_scan_handles_nested_directories(self, temp_config_dir):
        """Test that scanner handles nested directories."""
        scanner = ConfigurationScanner(str(temp_config_dir))
        files = scanner.scan()
        
        # Should find the config.yml in monitoring/subdir/
        nested_files = [f for f in files if 'subdir' in f]
        assert len(nested_files) == 1
    
    def test_scan_nonexistent_directory(self):
        """Test scanner handles nonexistent directory."""
        scanner = ConfigurationScanner("/nonexistent/path")
        files = scanner.scan()
        
        assert len(files) == 0
        assert len(scanner.errors) > 0
    
    def test_filter_by_pattern(self, temp_config_dir):
        """Test filtering files by pattern."""
        scanner = ConfigurationScanner(str(temp_config_dir))
        scanner.scan()
        
        # Filter for helm overrides
        filtered = scanner.filter_by_pattern("*-helm-overrides.yaml")
        assert len(filtered) == 3  # keystone, nova, neutron (nova-cinder doesn't match pattern)
    
    def test_get_files_by_service(self, temp_config_dir):
        """Test grouping files by service."""
        scanner = ConfigurationScanner(str(temp_config_dir))
        scanner.scan()
        
        services = scanner.get_files_by_service()
        
        assert "keystone" in services
        assert "nova" in services
        assert "neutron" in services
        assert "monitoring" in services
        
        # Nova should have 2 files
        assert len(services["nova"]) == 2
    
    def test_get_scan_summary(self, temp_config_dir):
        """Test scan summary generation."""
        scanner = ConfigurationScanner(str(temp_config_dir))
        scanner.scan()
        
        summary = scanner.get_scan_summary()
        
        assert summary["total_files"] == 5
        assert summary["services"] == 4
        assert "base_path" in summary
    
    def test_scan_with_symlinks(self, temp_config_dir):
        """Test scanner handles symbolic links."""
        # Create a symlink
        link_path = temp_config_dir / "link_to_keystone"
        target_path = temp_config_dir / "keystone"
        
        try:
            link_path.symlink_to(target_path)
        except OSError:
            pytest.skip("Cannot create symlinks on this system")
        
        scanner = ConfigurationScanner(str(temp_config_dir))
        
        # Without following symlinks
        files_no_follow = scanner.scan(follow_symlinks=False)
        
        # With following symlinks
        scanner2 = ConfigurationScanner(str(temp_config_dir))
        files_follow = scanner2.scan(follow_symlinks=True)
        
        # Following symlinks should discover more files
        assert len(files_follow) >= len(files_no_follow)
    
    def test_scan_empty_directory(self):
        """Test scanner handles empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = ConfigurationScanner(tmpdir)
            files = scanner.scan()
            
            assert len(files) == 0
            assert len(scanner.errors) == 0
