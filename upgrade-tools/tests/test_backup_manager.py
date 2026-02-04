"""Tests for backup manager."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.rollback.backup_manager import BackupManager, BackupResult, Backup


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def backup_manager(temp_dir):
    """Create a backup manager with temporary backup path."""
    return BackupManager(backup_base_path=str(temp_dir / "backups"))


@pytest.fixture
def sample_chart_versions(temp_dir):
    """Create a sample helm-chart-versions.yaml file."""
    chart_file = temp_dir / "helm-chart-versions.yaml"
    chart_file.write_text("""
charts:
  keystone:
    version: "2024.1"
  nova:
    version: "2024.1"
""")
    return str(chart_file)


@pytest.fixture
def sample_overrides(temp_dir):
    """Create sample override configuration files."""
    overrides_dir = temp_dir / "base-helm-configs"
    overrides_dir.mkdir(parents=True)
    
    # Create keystone override
    keystone_dir = overrides_dir / "keystone"
    keystone_dir.mkdir()
    (keystone_dir / "keystone-helm-overrides.yaml").write_text("""
images:
  tags:
    keystone: "quay.io/openstack/keystone:2024.1"
""")
    
    # Create nova override
    nova_dir = overrides_dir / "nova"
    nova_dir.mkdir()
    (nova_dir / "nova-helm-overrides.yaml").write_text("""
images:
  tags:
    nova: "quay.io/openstack/nova:2024.1"
""")
    
    return str(overrides_dir)


class TestBackupManager:
    """Test cases for BackupManager."""
    
    def test_initialization(self, temp_dir):
        """Test backup manager initialization."""
        backup_path = temp_dir / "backups"
        manager = BackupManager(backup_base_path=str(backup_path))
        
        assert manager.backup_base_path == backup_path
        assert backup_path.exists()
    
    def test_backup_chart_versions(self, backup_manager, sample_chart_versions):
        """Test backing up helm chart versions."""
        result = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        assert result.success
        assert "versions" in result.components
        assert len(result.errors) == 0
        
        # Verify backup file exists
        backup_file = result.backup_path / "helm-chart-versions.yaml"
        assert backup_file.exists()
        
        # Verify content
        content = backup_file.read_text()
        assert "keystone" in content
        assert "2024.1" in content
    
    def test_backup_override_configs(self, backup_manager, sample_overrides):
        """Test backing up override configurations."""
        result = backup_manager.create_backup(
            components=["configs"],
            overrides_base_path=sample_overrides
        )
        
        assert result.success
        assert "configs" in result.components
        assert len(result.errors) == 0
        
        # Verify backup directory exists
        backup_dir = result.backup_path / "base-helm-configs"
        assert backup_dir.exists()
        
        # Verify keystone override exists
        keystone_file = backup_dir / "keystone" / "keystone-helm-overrides.yaml"
        assert keystone_file.exists()
        
        # Verify nova override exists
        nova_file = backup_dir / "nova" / "nova-helm-overrides.yaml"
        assert nova_file.exists()
    
    def test_backup_all_components(self, backup_manager, sample_chart_versions, sample_overrides):
        """Test backing up all components."""
        result = backup_manager.create_backup(
            components=["versions", "configs"],
            chart_versions_path=sample_chart_versions,
            overrides_base_path=sample_overrides
        )
        
        assert result.success
        assert "versions" in result.components
        assert "configs" in result.components
        assert len(result.errors) == 0
        
        # Verify both backups exist
        assert (result.backup_path / "helm-chart-versions.yaml").exists()
        assert (result.backup_path / "base-helm-configs").exists()
    
    def test_backup_missing_source(self, backup_manager):
        """Test backup with missing source file."""
        result = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path="/nonexistent/file.yaml"
        )
        
        assert not result.success
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()
    
    def test_backup_metadata(self, backup_manager, sample_chart_versions):
        """Test backup metadata creation."""
        result = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        metadata_file = result.backup_path / "backup_metadata.txt"
        assert metadata_file.exists()
        
        content = metadata_file.read_text()
        assert "Backup ID:" in content
        assert "Timestamp:" in content
        assert "Components:" in content
        assert "versions" in content
    
    def test_list_backups(self, backup_manager, sample_chart_versions):
        """Test listing backups."""
        # Create multiple backups
        backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        backups = backup_manager.list_backups()
        
        assert len(backups) == 2
        assert all(isinstance(b, Backup) for b in backups)
        
        # Verify sorted by timestamp (newest first)
        assert backups[0].timestamp >= backups[1].timestamp
    
    def test_get_latest_backup(self, backup_manager, sample_chart_versions):
        """Test getting the latest backup."""
        # Create first backup
        result1 = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        # Create second backup
        result2 = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        latest = backup_manager.get_latest_backup()
        
        assert latest is not None
        assert latest.backup_path == result2.backup_path
    
    def test_get_backup_by_id(self, backup_manager, sample_chart_versions):
        """Test getting a backup by ID."""
        result = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        backup_id = result.timestamp.strftime("%Y%m%d_%H%M%S_%f")
        backup = backup_manager.get_backup_by_id(backup_id)
        
        assert backup is not None
        assert backup.backup_id == backup_id
        assert backup.backup_path == result.backup_path
    
    def test_delete_backup(self, backup_manager, sample_chart_versions):
        """Test deleting a backup."""
        result = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        backup_id = result.timestamp.strftime("%Y%m%d_%H%M%S_%f")
        
        # Verify backup exists
        assert result.backup_path.exists()
        
        # Delete backup
        success = backup_manager.delete_backup(backup_id)
        
        assert success
        assert not result.backup_path.exists()
    
    def test_delete_nonexistent_backup(self, backup_manager):
        """Test deleting a nonexistent backup."""
        success = backup_manager.delete_backup("nonexistent_backup")
        assert not success
    
    def test_backup_with_timestamp(self, backup_manager, sample_chart_versions):
        """Test that backups have unique timestamps."""
        result1 = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        result2 = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=sample_chart_versions
        )
        
        # Backup paths should be different (different timestamps)
        assert result1.backup_path != result2.backup_path
    
    def test_empty_components_list(self, backup_manager):
        """Test backup with empty components list."""
        result = backup_manager.create_backup(components=[])
        
        # Should fail because no components were backed up
        assert not result.success
        assert len(result.components) == 0
