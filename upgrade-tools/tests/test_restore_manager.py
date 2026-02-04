"""Tests for restore manager."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.rollback.restore_manager import RestoreManager, RestoreResult
from src.rollback.backup_manager import Backup, BackupManager


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
def restore_manager(backup_manager):
    """Create a restore manager."""
    return RestoreManager(backup_manager=backup_manager)


@pytest.fixture
def sample_backup(temp_dir):
    """Create a sample backup."""
    backup_path = temp_dir / "test_backup"
    backup_path.mkdir()
    
    # Create chart versions backup
    chart_file = backup_path / "helm-chart-versions.yaml"
    chart_file.write_text("""
charts:
  keystone:
    version: "2024.1"
  nova:
    version: "2024.1"
""")
    
    # Create configs backup
    configs_dir = backup_path / "base-helm-configs"
    configs_dir.mkdir()
    keystone_dir = configs_dir / "keystone"
    keystone_dir.mkdir()
    (keystone_dir / "keystone-helm-overrides.yaml").write_text("""
images:
  tags:
    keystone: "quay.io/openstack/keystone:2024.1"
""")
    
    # Create backup metadata
    metadata_file = backup_path / "backup_metadata.txt"
    metadata_file.write_text("""
Backup ID: test_backup
Timestamp: 2026-02-04T10:00:00
Components: versions, configs
""")
    
    return Backup(
        backup_id="test_backup",
        timestamp=datetime(2026, 2, 4, 10, 0, 0),
        backup_path=backup_path,
        components={
            "versions": chart_file,
            "configs": configs_dir
        }
    )


class TestRestoreManager:
    """Test cases for RestoreManager."""
    
    def test_initialization(self, backup_manager):
        """Test restore manager initialization."""
        manager = RestoreManager(backup_manager=backup_manager)
        
        assert manager.backup_manager == backup_manager
        assert manager.helm_executor is not None
    
    def test_restore_chart_versions(self, restore_manager, sample_backup, temp_dir):
        """Test restoring helm chart versions."""
        destination = temp_dir / "helm-chart-versions.yaml"
        
        result = restore_manager.restore_from_backup(
            backup=sample_backup,
            components=["versions"],
            chart_versions_path=str(destination)
        )
        
        assert result.success
        assert "versions" in result.components
        assert len(result.errors) == 0
        
        # Verify file was restored
        assert destination.exists()
        content = destination.read_text()
        assert "keystone" in content
        assert "2024.1" in content
    
    def test_restore_override_configs(self, restore_manager, sample_backup, temp_dir):
        """Test restoring override configurations."""
        destination = temp_dir / "base-helm-configs"
        
        result = restore_manager.restore_from_backup(
            backup=sample_backup,
            components=["configs"],
            overrides_base_path=str(destination)
        )
        
        assert result.success
        assert "configs" in result.components
        assert len(result.errors) == 0
        
        # Verify directory was restored
        assert destination.exists()
        keystone_file = destination / "keystone" / "keystone-helm-overrides.yaml"
        assert keystone_file.exists()
    
    def test_restore_all_components(self, restore_manager, sample_backup, temp_dir):
        """Test restoring all components."""
        chart_dest = temp_dir / "helm-chart-versions.yaml"
        configs_dest = temp_dir / "base-helm-configs"
        
        result = restore_manager.restore_from_backup(
            backup=sample_backup,
            components=["versions", "configs"],
            chart_versions_path=str(chart_dest),
            overrides_base_path=str(configs_dest)
        )
        
        assert result.success
        assert "versions" in result.components
        assert "configs" in result.components
        assert len(result.errors) == 0
        
        # Verify both were restored
        assert chart_dest.exists()
        assert configs_dest.exists()
    
    def test_restore_missing_component(self, restore_manager, sample_backup, temp_dir):
        """Test restoring a component that doesn't exist in backup."""
        result = restore_manager.restore_from_backup(
            backup=sample_backup,
            components=["databases"],  # Not in sample backup
            chart_versions_path=str(temp_dir / "helm-chart-versions.yaml")
        )
        
        # Should not fail, just skip the missing component
        assert "databases" not in result.components
    
    def test_restore_without_destination_path(self, restore_manager, sample_backup):
        """Test restore without providing destination path."""
        result = restore_manager.restore_from_backup(
            backup=sample_backup,
            components=["versions"]
            # Missing chart_versions_path
        )
        
        assert not result.success
        assert len(result.errors) > 0
        assert "required" in result.errors[0].lower()
    
    def test_restore_creates_pre_restore_backup(self, restore_manager, sample_backup, temp_dir):
        """Test that restore creates a backup of existing files."""
        destination = temp_dir / "helm-chart-versions.yaml"
        
        # Create existing file
        destination.write_text("existing content")
        
        # Restore
        restore_manager.restore_from_backup(
            backup=sample_backup,
            components=["versions"],
            chart_versions_path=str(destination)
        )
        
        # Verify pre-restore backup was created
        pre_restore = destination.parent / f"{destination.name}.pre-restore"
        assert pre_restore.exists()
        assert pre_restore.read_text() == "existing content"
    
    def test_restore_latest(self, restore_manager, backup_manager, temp_dir):
        """Test restoring from latest backup."""
        # Create a backup first
        chart_file = temp_dir / "original-chart-versions.yaml"
        chart_file.write_text("original: content")
        
        backup_result = backup_manager.create_backup(
            components=["versions"],
            chart_versions_path=str(chart_file)
        )
        
        # Now restore
        destination = temp_dir / "restored-chart-versions.yaml"
        result = restore_manager.restore_latest(
            components=["versions"],
            chart_versions_path=str(destination)
        )
        
        assert result.success
        assert destination.exists()
    
    def test_restore_latest_no_backups(self, restore_manager, temp_dir):
        """Test restore_latest when no backups exist."""
        with pytest.raises(ValueError, match="No backups available"):
            restore_manager.restore_latest(
                components=["versions"],
                chart_versions_path=str(temp_dir / "helm-chart-versions.yaml")
            )
    
    def test_restore_with_missing_backup_file(self, restore_manager, temp_dir):
        """Test restore when backup file is missing."""
        # Create backup with missing file
        backup = Backup(
            backup_id="missing_backup",
            timestamp=datetime.now(),
            backup_path=temp_dir / "missing",
            components={
                "versions": temp_dir / "nonexistent.yaml"
            }
        )
        
        result = restore_manager.restore_from_backup(
            backup=backup,
            components=["versions"],
            chart_versions_path=str(temp_dir / "destination.yaml")
        )
        
        assert not result.success
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()
    
    def test_restore_configs_overwrites_existing(self, restore_manager, sample_backup, temp_dir):
        """Test that restore overwrites existing configs."""
        destination = temp_dir / "base-helm-configs"
        destination.mkdir()
        
        # Create existing config
        existing_dir = destination / "existing"
        existing_dir.mkdir()
        (existing_dir / "existing.yaml").write_text("existing")
        
        # Restore
        result = restore_manager.restore_from_backup(
            backup=sample_backup,
            components=["configs"],
            overrides_base_path=str(destination)
        )
        
        assert result.success
        
        # Verify pre-restore backup was created
        pre_restore = destination.parent / f"{destination.name}.pre-restore"
        assert pre_restore.exists()
        assert (pre_restore / "existing" / "existing.yaml").exists()
        
        # Verify new configs are in place
        assert (destination / "keystone" / "keystone-helm-overrides.yaml").exists()
    
    @patch('src.rollback.restore_manager.RestoreManager._apply_previous_versions')
    def test_restore_with_helm_apply(self, mock_apply, restore_manager, sample_backup, temp_dir):
        """Test restore with helm chart application."""
        destination = temp_dir / "helm-chart-versions.yaml"
        
        result = restore_manager.restore_from_backup(
            backup=sample_backup,
            components=["versions"],
            chart_versions_path=str(destination),
            apply_helm_charts=True
        )
        
        assert result.success
        assert "versions" in result.components
        
        # Verify helm apply was called
        mock_apply.assert_called_once()
    
    @patch('src.rollback.restore_manager.RestoreManager._apply_previous_versions')
    def test_restore_helm_apply_failure(self, mock_apply, restore_manager, sample_backup, temp_dir):
        """Test restore when helm apply fails."""
        mock_apply.side_effect = Exception("Helm apply failed")
        
        destination = temp_dir / "helm-chart-versions.yaml"
        
        result = restore_manager.restore_from_backup(
            backup=sample_backup,
            components=["versions"],
            chart_versions_path=str(destination),
            apply_helm_charts=True
        )
        
        # Should still succeed for file restore, but have warning
        assert result.success
        assert "versions" in result.components
        assert len(result.warnings) > 0
        assert "helm" in result.warnings[0].lower()
